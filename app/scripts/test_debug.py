from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

_APP_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_APP_DIR / "retrieval"))
sys.path.insert(0, str(_APP_DIR / "ingestion"))


from dense import DenseRetriever
from bm25 import BM25Retriever
from hybrid import HybridRetriever
from reranker import CrossEncoderReranker
from parent_expansion import ParentExpander
from context_process import ContextProcessor


# ============================================================
# LOAD YOUR EXISTING CHUNKS
# ============================================================

# Use the same loading code you used in test_pipeline.py.

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
# PREPARE BM25
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
# INITIALIZE
# ============================================================

dense = DenseRetriever(
    persist_directory="vectorstore/chroma",
    collection_name="technova_children",
    model_name="all-MiniLM-L6-v2",
)

bm25 = BM25Retriever(
    chunks=bm25_chunks
)

hybrid = HybridRetriever(
    dense_retriever=dense,
    bm25_retriever=bm25,
)

reranker = CrossEncoderReranker()

parent_expander = ParentExpander(
    parent_chunks
)

context_processor = ContextProcessor(
    max_contexts=5
)


# ============================================================
# QUERY
# ============================================================

query = "How does TechNova evaluate RAG systems?"

access_level = "AI_ENGINEER"


print("=" * 80)
print("RETRIEVAL DEBUG")
print("=" * 80)

print("\nQUERY:")
print(query)

print("\nACCESS LEVEL:")
print(access_level)


# ============================================================
# 1. DENSE RETRIEVAL
# ============================================================

dense_results = dense.retrieve(
    query=query,
    top_k=10,
    user_access_level=access_level,
)

print("\n")
print("=" * 80)
print("1. DENSE RETRIEVAL - TOP 10")
print("=" * 80)

for rank, result in enumerate(
    dense_results,
    start=1
):

    metadata = result.get("metadata", {})

    print(
        f"\n#{rank}"
    )

    print(
        "Child ID:",
        result.get("child_id")
    )

    print(
        "Document:",
        metadata.get("document_id")
    )

    print(
        "Title:",
        metadata.get("title")
    )

    print(
        "Distance:",
        result.get("distance")
    )

    print(
        "Access:",
        metadata.get("access_level")
    )


# ============================================================
# 2. BM25 RETRIEVAL
# ============================================================

bm25_results = bm25.retrieve(
    query=query,
    top_k=10,
    user_access_level=access_level,
)

print("\n")
print("=" * 80)
print("2. BM25 RETRIEVAL - TOP 10")
print("=" * 80)

for rank, result in enumerate(
    bm25_results,
    start=1
):

    metadata = result.get("metadata", {})

    print(
        f"\n#{rank}"
    )

    print(
        "Child ID:",
        result.get("id")
    )

    print(
        "Document:",
        metadata.get("document_id")
    )

    print(
        "Title:",
        metadata.get("title")
    )

    print(
        "BM25 Score:",
        result.get("score")
    )

    print(
        "Access:",
        metadata.get("access_level")
    )


# ============================================================
# 3. HYBRID RETRIEVAL
# ============================================================

hybrid_results = hybrid.retrieve(
    query=query,
    top_k=10,
    candidate_k=10,
    user_access_level=access_level,
)

print("\n")
print("=" * 80)
print("3. HYBRID RRF - TOP 10")
print("=" * 80)

for rank, result in enumerate(
    hybrid_results,
    start=1
):

    metadata = result.get("metadata", {})

    print(
        f"\n#{rank}"
    )

    print(
        "Child ID:",
        result.get("id")
    )

    print(
        "Document:",
        metadata.get("document_id")
    )

    print(
        "Title:",
        metadata.get("title")
    )

    print(
        "RRF Score:",
        result.get("rrf_score")
    )


# ============================================================
# 4. CROSS-ENCODER RERANKING
# ============================================================

reranked_results = reranker.rerank(
    query=query,
    results=hybrid_results,
    top_k=10,
)

print("\n")
print("=" * 80)
print("4. CROSS-ENCODER RERANKING - TOP 10")
print("=" * 80)

for rank, result in enumerate(
    reranked_results,
    start=1
):

    metadata = result.get("metadata", {})

    print(
        f"\n#{rank}"
    )

    print(
        "Child ID:",
        result.get("id")
    )

    print(
        "Document:",
        metadata.get("document_id")
    )

    print(
        "Title:",
        metadata.get("title")
    )

    print(
        "Rerank Score:",
        result.get("rerank_score")
    )


# ============================================================
# 5. PARENT EXPANSION
# ============================================================

expanded_results = parent_expander.expand(
    results=reranked_results,
    user_access_level=access_level,
)

print("\n")
print("=" * 80)
print("5. PARENT EXPANSION")
print("=" * 80)

for rank, result in enumerate(
    expanded_results,
    start=1
):

    metadata = result.get(
        "parent_metadata",
        {}
    )

    print(
        f"\n#{rank}"
    )

    print(
        "Parent ID:",
        result.get("parent_id")
    )

    print(
        "Document:",
        metadata.get("document_id")
    )

    print(
        "Title:",
        metadata.get("title")
    )


# ============================================================
# 6. CONTEXT PROCESSING
# ============================================================

contexts = context_processor.process(
    expanded_results
)

print("\n")
print("=" * 80)
print("6. FINAL CONTEXTS")
print("=" * 80)

for rank, context in enumerate(
    contexts,
    start=1
):

    metadata = context.get(
        "metadata",
        {}
    )

    print(
        f"\n#{rank}"
    )

    print(
        "Parent ID:",
        context.get("parent_id")
    )

    print(
        "Document:",
        metadata.get("document_id")
    )

    print(
        "Title:",
        metadata.get("title")
    )

    print(
        "Content:"
    )

    print(
        context.get("content", "")[:500]
    )


# ============================================================
# 7. CHECK TARGET DOCUMENT
# ============================================================

target = "ai_rag_eval_001"

print("\n")
print("=" * 80)
print("7. TARGET DOCUMENT CHECK")
print("=" * 80)

print(
    "Target:",
    target
)

print(
    "In Dense:",
    any(
        r.get("metadata", {}).get("document_id")
        == target
        for r in dense_results
    )
)

print(
    "In BM25:",
    any(
        r.get("metadata", {}).get("document_id")
        == target
        for r in bm25_results
    )
)

print(
    "In Hybrid:",
    any(
        r.get("metadata", {}).get("document_id")
        == target
        for r in hybrid_results
    )
)

print(
    "In Reranker:",
    any(
        r.get("metadata", {}).get("document_id")
        == target
        for r in reranked_results
    )
)

print(
    "In Parent Expansion:",
    any(
        r.get("parent_metadata", {}).get("document_id")
        == target
        for r in expanded_results
    )
)

print(
    "In Final Context:",
    any(
        r.get("metadata", {}).get("document_id")
        == target
        for r in contexts
    )
)


print("\n")
print("=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)