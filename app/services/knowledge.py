"""Load the knowledge base once and expose the existing retrieval/generation stack."""

from dataclasses import asdict
import hashlib
import re
import threading
import time

from app.ingestion.chunker import create_chunks
from app.ingestion.loader import discover_documents, load_document
from app.ingestion.parser import parse_document
from app.retrieval.access_control import AccessController
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.context_process import ContextProcessor
from app.retrieval.parent_expansion import ParentExpander


class KnowledgeService:
    def __init__(self, settings):
        self.settings = settings
        self.access = AccessController()
        self.documents = {}
        parents, children = [], []
        digest = hashlib.sha256()
        for path in discover_documents(settings.knowledge_dir):
            raw = load_document(path)
            digest.update(raw.encode())
            document = parse_document(raw)
            self.access.validate_access_level(document.metadata.access_level)
            document_id = document.metadata.document_id
            if document_id in self.documents:
                raise ValueError(f"Duplicate document ID: {document_id}")
            self.documents[document_id] = document
            new_parents, new_children = create_chunks(document)
            parents.extend(new_parents)
            children.extend(new_children)
        self.chunks = [
            {
                "id": c.child_id,
                "text": c.content,
                "metadata": {**asdict(c.metadata), "parent_id": c.parent_id},
            }
            for c in children
        ]
        self.bm25 = BM25Retriever(self.chunks) if self.chunks else None
        self.expander = ParentExpander(parents)
        self.processor = ContextProcessor(max_contexts=3)
        self.graph = None
        self.graph_lock = threading.Lock()
        if settings.rag_mode == "groq":
            if not settings.groq_api_key:
                raise ValueError(
                    "RAG_MODE=groq requires GROQ_API_KEY. Use RAG_MODE=local for local search."
                )
            if not children:
                raise ValueError("Groq mode requires at least one knowledge document.")
            from app.graph.graph import RAGGraph
            from app.retrieval.dense import DenseRetriever

            dense = DenseRetriever(
                persist_directory=str(settings.vectorstore_dir),
                collection_name=f"technova_{digest.hexdigest()[:16]}",
            )
            dense.add_chunks(children)
            self.graph = RAGGraph(dense, self.bm25, parents)

    def visible_documents(self):
        return [
            d
            for d in self.documents.values()
            if self.access.can_access(self.settings.access_level, d.metadata.access_level)
        ]

    def document(self, document_id):
        document = self.documents.get(document_id)
        if document and self.access.can_access(
            self.settings.access_level, document.metadata.access_level
        ):
            return {**asdict(document.metadata), "content": document.content}
        return None

    def list_documents(self, search="", department=None):
        words = search.casefold().split()
        return [
            {**asdict(d.metadata), "preview": re.sub(r"[#*`\n]+", " ", d.content).strip()[:180]}
            for d in self.visible_documents()
            if (not department or d.metadata.department == department)
            and all(w in (d.metadata.title + " " + d.content).casefold() for w in words)
        ]

    def query(self, query):
        started = time.perf_counter()
        if self.graph:
            # RAGGraph's tracer is mutable. Serialize invocations to isolate requests.
            with self.graph_lock:
                result = self.graph.run(query, user_access_level=self.settings.access_level)
            if result.get("error"):
                raise RuntimeError("The AI provider could not complete the request.")
            contexts = result.get("contexts", [])
        else:
            hits = (
                self.bm25.retrieve(query, top_k=5, user_access_level=self.settings.access_level)
                if self.bm25
                else []
            )
            hits = [hit for hit in hits if hit["score"] > 0]
            contexts = self.processor.process(
                self.expander.expand(hits, self.settings.access_level)
            )
            # Extract exact passages; local mode makes no generated factual claims.
            answer = "\n\n".join(f"{c['metadata']['title']}\n{c['content']}" for c in contexts)
            result = {
                "answer": answer
                or "I couldn’t find a matching passage in the documents available to you. Try a specific topic, or browse the knowledge library.",
                "grounded": bool(contexts),
                "verification_reason": "Exact passages from the knowledge base; no AI generation."
                if contexts
                else "No matching passages found.",
                "route": "DIRECT",
                "retry_count": 0,
                "sources": [c["metadata"] for c in contexts],
            }
        sources, seen = [], set()
        for source in result.get("sources", []):
            document_id = source.get("document_id")
            document = self.document(document_id)
            if not document or document_id in seen:
                continue
            seen.add(document_id)
            excerpt = next(
                (
                    c["content"]
                    for c in contexts
                    if c.get("metadata", {}).get("document_id") == document_id
                ),
                "",
            )
            sources.append(
                {
                    key: document[key]
                    for key in ("document_id", "title", "department", "section", "version")
                }
            )
            sources[-1]["excerpt"] = excerpt[:700]
        return {
            "answer": result["answer"],
            "sources": sources,
            "grounded": bool(result.get("grounded")),
            "verification_reason": result.get("verification_reason", ""),
            "mode": self.settings.rag_mode,
            "route": result.get("route", "DIRECT"),
            "retry_count": result.get("retry_count", 0),
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
