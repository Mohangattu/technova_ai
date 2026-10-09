from pathlib import Path
import sys
import os

# --------------------------------------------------
# UTF-8 SETUP
# --------------------------------------------------

if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")

sys.stdout.reconfigure(
    encoding="utf-8",
    errors="replace",
)

sys.stderr.reconfigure(
    encoding="utf-8",
    errors="replace",
)

# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------

_APP_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_APP_DIR / "graph"))
sys.path.insert(0, str(_APP_DIR / "query"))
sys.path.insert(0, str(_APP_DIR / "retrieval"))
sys.path.insert(0, str(_APP_DIR / "generation"))
sys.path.insert(0, str(_APP_DIR / "evaluation"))
sys.path.insert(0, str(_APP_DIR / "ingestion"))

# --------------------------------------------------
# IMPORTS
# --------------------------------------------------

from graph import RAGGraph
from dense import DenseRetriever
from bm25 import BM25Retriever

from loader import discover_documents, load_document
from parser import parse_document
from chunker import create_chunks


# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

_DATA_DIR = _APP_DIR.parent / "data" / "raw"

parent_chunks = []
child_chunks = []

for _doc_path in discover_documents(_DATA_DIR):

    _raw = load_document(_doc_path)

    _doc = parse_document(_raw)

    _parents, _children = create_chunks(_doc)

    parent_chunks.extend(_parents)
    child_chunks.extend(_children)


print("=" * 80)
print("TECHNOVA DATASET")
print("=" * 80)

print("Parent chunks:", len(parent_chunks))
print("Child chunks :", len(child_chunks))


# --------------------------------------------------
# PREPARE BM25 DATA
# --------------------------------------------------

bm25_chunks = []

for chunk in child_chunks:

    bm25_chunks.append(
        {
            "id": chunk.child_id,
            "text": chunk.content,
            "metadata": {
                "parent_id": chunk.parent_id,
                "document_id": chunk.metadata.document_id,
                "title": chunk.metadata.title,
                "department": chunk.metadata.department,
                "section": chunk.metadata.section,
                "document_type": chunk.metadata.document_type,
                "version": chunk.metadata.version,
                "access_level": chunk.metadata.access_level,
            },
        }
    )


# --------------------------------------------------
# RETRIEVERS
# --------------------------------------------------

dense_retriever = DenseRetriever()

bm25_retriever = BM25Retriever(
    chunks=bm25_chunks
)


# --------------------------------------------------
# BUILD LANGGRAPH
# --------------------------------------------------

rag_graph = RAGGraph(
    dense_retriever=dense_retriever,
    bm25_retriever=bm25_retriever,
    parent_chunks=parent_chunks,
    top_k=5,
    candidate_k=10,
    max_contexts=5,
)


# --------------------------------------------------
# CONTROLLED VERIFIER TEST
# --------------------------------------------------

class MockGroundedRAG:

    def __init__(self):
        self.call_count = 0

    def generate(
        self,
        query,
        contexts,
    ):

        self.call_count += 1

        print(
            f"\n[MOCK GENERATION CALL {self.call_count}]"
        )

        if self.call_count == 1:

            print(
                "Returning grounded = False"
            )

            return {
                "answer": "Initial intentionally failed answer.",
                "sources": [],
                "grounded": False,
                "claims": [],
                "verification_reason": (
                    "Controlled test failure: "
                    "answer was not sufficiently grounded."
                ),
            }

        print(
            "Returning grounded = True"
        )

        return {
            "answer": (
                "Corrected answer after self-correction."
            ),
            "sources": [],
            "grounded": True,
            "claims": [],
            "verification_reason": (
                "Controlled test success."
            ),
        }


# Replace ONLY the generation/verifier component
# for this test.

rag_graph.nodes.grounded_rag = MockGroundedRAG()


# --------------------------------------------------
# TEST QUERY
# --------------------------------------------------

query = "How does TechNova evaluate RAG systems?"

result = rag_graph.run(
    query=query,
    user_access_level="AI_ENGINEER",
)


# --------------------------------------------------
# DISPLAY RESULT
# --------------------------------------------------

print("\n" + "=" * 70)
print("STAGE 15 SELF-CORRECTION TEST")
print("=" * 70)

print("\nOriginal Query:")
print(result.get("original_query"))

print("\nRoute:")
print(result.get("route"))

print("\nRetrieval Query:")
print(result.get("retrieval_query"))

print("\nCorrection Query:")
print(result.get("correction_query"))

print("\nRetry Count:")
print(result.get("retry_count"))

print("\nAnswer:")
print(result.get("answer"))

print("\nGrounded:")
print(result.get("grounded"))

print("\nVerification Reason:")
print(result.get("verification_reason"))

print("\nError:")
print(result.get("error"))

print("\n" + "=" * 70)
