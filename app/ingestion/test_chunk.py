from loader import (
    discover_documents,
    load_document,
)

from parser import parse_document

from chunker import create_chunks


def main():

    paths = discover_documents("data/raw")

    total_parents = 0
    total_children = 0

    for path in paths:

        text = load_document(path)

        document = parse_document(text)

        parents, children = create_chunks(document)

        total_parents += len(parents)
        total_children += len(children)

        print(
            f"{document.metadata.document_id}: "
            f"{len(parents)} parents, "
            f"{len(children)} children"
        )

    print("\n" + "=" * 50)

    print(f"Documents:     {len(paths)}")
    print(f"Parent chunks: {total_parents}")
    print(f"Child chunks:  {total_children}")


if __name__ == "__main__":
    main()