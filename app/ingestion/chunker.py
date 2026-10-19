from typing import List

from app.ingestion.model import (
    TechNovaDocument,
    ParentChunk,
    ChildChunk,
)


PARENT_SIZE = 700
PARENT_OVERLAP = 80

CHILD_SIZE = 200
CHILD_OVERLAP = 40


def split_text(
    text: str,
    chunk_size: int,
    overlap: int,
) -> List[str]:

    words = text.split()

    if not words:
        return []

    chunks = []

    start = 0

    while start < len(words):

        end = min(start + chunk_size, len(words))

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


def create_parent_chunks(
    document: TechNovaDocument,
) -> List[ParentChunk]:

    parents = []

    for section_index, section in enumerate(document.sections):

        section_chunks = split_text(
            section.content,
            PARENT_SIZE,
            PARENT_OVERLAP,
        )

        for chunk_index, content in enumerate(section_chunks):

            parent_id = (
                f"{document.metadata.document_id}"
                f"_p{section_index}_{chunk_index}"
            )

            parents.append(
                ParentChunk(
                    parent_id=parent_id,
                    content=content,
                    metadata=document.metadata,
                )
            )

    return parents


def create_child_chunks(
    parent: ParentChunk,
) -> List[ChildChunk]:

    children = []

    chunks = split_text(
        parent.content,
        CHILD_SIZE,
        CHILD_OVERLAP,
    )

    for index, content in enumerate(chunks):

        child_id = f"{parent.parent_id}_c{index}"

        children.append(
            ChildChunk(
                child_id=child_id,
                parent_id=parent.parent_id,
                content=content,
                metadata=parent.metadata,
            )
        )

    return children


def create_chunks(
    document: TechNovaDocument,
) -> tuple[List[ParentChunk], List[ChildChunk]]:

    parents = create_parent_chunks(document)

    children = []

    for parent in parents:
        children.extend(
            create_child_chunks(parent)
        )

    return parents, children
