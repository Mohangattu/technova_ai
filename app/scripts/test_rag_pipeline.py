from pathlib import Path
import sys
import os
sys.stdout.reconfigure(
    encoding="utf-8"
)
# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.system("chcp 65001 > nul 2>&1")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# PATH SETUP
# ============================================================

_APP_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_APP_DIR / "query"))
sys.path.insert(0, str(_APP_DIR / "retrieval"))
sys.path.insert(0, str(_APP_DIR / "generation"))
sys.path.insert(0, str(_APP_DIR / "evaluation"))
sys.path.insert(0, str(_APP_DIR / "services"))
sys.path.insert(0, str(_APP_DIR / "ingestion"))


# ============================================================
# IMPORTS
# ============================================================

from model import ParentChunk, ChildChunk

from dense import DenseRetriever
from bm25 import BM25Retriever

from rag_pipeline import RAGPipeline


# ============================================================
# LOAD TECHNOVA CHUNKS
# ============================================================

# Use the same loading code you used when creating
# your 117 parent chunks and 117 child chunks.

# ------------------------------------------------------------
# IMPORTANT:
# Replace ONLY this section with your existing loading code.
# ------------------------------------------------------------

from loader import discover_documents, load_document
from parser import parse_document
from chunker import create_chunks

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


# ============================================================
# PREPARE BM25 DATA
# ============================================================

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


# ============================================================
# INITIALIZE DENSE RETRIEVER
# ============================================================

dense_retriever = DenseRetriever(
    persist_directory="vectorstore/chroma",
    collection_name="technova_children",
    model_name="all-MiniLM-L6-v2",
)


# ============================================================
# INITIALIZE BM25
# ============================================================

bm25_retriever = BM25Retriever(
    chunks=bm25_chunks
)


# ============================================================
# INITIALIZE COMPLETE RAG PIPELINE
# ============================================================

rag_pipeline = RAGPipeline(
    dense_retriever=dense_retriever,
    bm25_retriever=bm25_retriever,
    parent_chunks=parent_chunks,
    top_k=5,
    candidate_k=10,
    max_contexts=5,
)


# ============================================================
# TEST CASES
# ============================================================

tests = [

    {
        "name": "DIRECT QUERY",
        "query": "What is the default production API timeout?",
        "access": "EMPLOYEE",
    },

    {
        "name": "REWRITE QUERY",
        "query": "What about authentication?",
        "access": "EMPLOYEE",
    },

    {
        "name": "RAG EVALUATION",
        "query": "How does TechNova evaluate RAG systems?",
        "access": "MANAGER",
    },

    {
        "name": "UNSUPPORTED QUERY",
        "query": "What is TechNova's stock price forecast?",
        "access": "EMPLOYEE",
    },

]


# ============================================================
# RUN END-TO-END TESTS
# ============================================================

for test in tests:

    print("\n")
    print("=" * 80)
    print(f"TEST: {test['name']}")
    print("=" * 80)

    print("\nUSER QUERY:")
    print(test["query"])

    print("\nUSER ACCESS:")
    print(test["access"])


    try:

        result = rag_pipeline.run(
            query=test["query"],
            user_access_level=test["access"],
        )


        # ----------------------------------------------------
        # QUERY ROUTING
        # ----------------------------------------------------

        print("\n" + "-" * 80)
        print("QUERY ROUTING")
        print("-" * 80)

        print("Route:")
        print(result["route"])

        print("\nRetrieval Query:")
        print(result["retrieval_query"])


        # ----------------------------------------------------
        # FINAL ANSWER
        # ----------------------------------------------------

        print("\n" + "-" * 80)
        print("FINAL ANSWER")
        print("-" * 80)

        print(result["answer"])


        # ----------------------------------------------------
        # SOURCES
        # ----------------------------------------------------

        print("\n" + "-" * 80)
        print("SOURCES")
        print("-" * 80)

        if result["sources"]:

            for source in result["sources"]:

                print(
                    f"- {source.get('document_id')} | "
                    f"{source.get('title')} | "
                    f"{source.get('section')}"
                )

        else:

            print("No sources returned.")


        # ----------------------------------------------------
        # GROUNDING
        # ----------------------------------------------------

        print("\n" + "-" * 80)
        print("GROUNDING")
        print("-" * 80)

        print(
            "Grounded:",
            result["grounded"]
        )

        print(
            "Verification:",
            result["verification_reason"]
        )


        # ----------------------------------------------------
        # CLAIMS
        # ----------------------------------------------------

        print("\n" + "-" * 80)
        print("CLAIMS")
        print("-" * 80)

        if result["claims"]:

            for claim in result["claims"]:
                print("-", claim)

        else:

            print("No claims returned.")


    except Exception as error:

        print("\n" + "-" * 80)
        print("ERROR")
        print("-" * 80)

        print(
            type(error).__name__,
            ":",
            error
        )


# ============================================================
# COMPLETE
# ============================================================

print("\n")
print("=" * 80)
print("END-TO-END TECHNOVA RAG TEST COMPLETED")
print("=" * 80)