import sys
from pathlib import Path

# Allow running this script directly from any working directory
sys.path.insert(0, str(Path(__file__).parent))

from loader import (
    discover_documents,
    load_document,
)

from parser import parse_document

# Resolve the data directory relative to this file, not the cwd
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


def main():
    documents = discover_documents(DATA_DIR)

    print(f"Found {len(documents)} documents\n")

    successful = 0
    failed = 0

    for path in documents:
        try:
            text = load_document(path)
            document = parse_document(text)

            print(f"✓ {document.metadata.document_id}")
            print(f"  Title: {document.metadata.title}")
            print(f"  Department: {document.metadata.department}")
            print(f"  Sections: {len(document.sections)}")
            print()

            successful += 1

        except Exception as exc:
            print(f"✗ {path}")
            print(f"  Error: {exc}")
            print()

            failed += 1

    print("=" * 50)
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")


if __name__ == "__main__":
    main()