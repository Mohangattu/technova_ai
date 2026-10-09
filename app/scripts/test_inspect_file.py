from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

_APP_DIR = Path(__file__).parent.parent

sys.path.insert(0, str(_APP_DIR))
sys.path.insert(0, str(_APP_DIR / "ingestion"))

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


TARGET = "ai_rag_eval_001"


print("=" * 80)
print("TECHNOVA RAG EVALUATION DOCUMENT")
print("=" * 80)


print("\nPARENT CHUNKS")
print("-" * 80)

for chunk in parent_chunks:

    if chunk.metadata.document_id == TARGET:

        print("\nParent ID:")
        print(chunk.parent_id)

        print("\nTitle:")
        print(chunk.metadata.title)

        print("\nSection:")
        print(chunk.metadata.section)

        print("\nAccess:")
        print(chunk.metadata.access_level)

        print("\nCONTENT:")
        print(chunk.content)


print("\n")
print("=" * 80)
print("CHILD CHUNKS")
print("=" * 80)

for chunk in child_chunks:

    if chunk.metadata.document_id == TARGET:

        print("\nChild ID:")
        print(chunk.child_id)

        print("\nParent ID:")
        print(chunk.parent_id)

        print("\nCONTENT:")
        print(chunk.content)