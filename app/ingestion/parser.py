import re
from typing import Dict, List

from app.ingestion.model import (
    DocumentMetadata,
    Section,
    TechNovaDocument,
)


REQUIRED_METADATA = {
    "document_id",
    "title",
    "department",
    "section",
    "document_type",
    "version",
    "access_level",
}


def parse_front_matter(text: str) -> tuple[Dict[str, str], str]:
    """
    Extract YAML-style front matter from a Markdown document.

    Expected format:

    ---
    key: value
    ---
    body
    """

    text = text.strip()

    if not text.startswith("---"):
        raise ValueError("Document must start with front matter.")

    match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n?(.*)$",
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError("Invalid front matter format.")

    raw_metadata = match.group(1)
    body = match.group(2).strip()

    metadata = {}

    for line in raw_metadata.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            raise ValueError(
                f"Invalid metadata line: {line}"
            )

        key, value = line.split(":", 1)

        key = key.strip()
        value = value.strip()

        metadata[key] = value

    missing = REQUIRED_METADATA - metadata.keys()

    if missing:
        raise ValueError(
            f"Missing required metadata: {sorted(missing)}"
        )

    return metadata, body


def parse_sections(body: str) -> List[Section]:
    """
    Extract ## level sections from the document body.
    """

    pattern = re.compile(
        r"^##\s+(.+?)\s*$",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(body))

    if not matches:
        return [
            Section(
                heading="Document",
                content=body.strip(),
            )
        ]

    sections = []

    for index, match in enumerate(matches):

        heading = match.group(1).strip()

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(body)

        content = body[start:end].strip()

        if content:
            sections.append(
                Section(
                    heading=heading,
                    content=content,
                )
            )

    return sections


def parse_document(text: str) -> TechNovaDocument:
    """
    Convert raw Markdown into a structured TechNovaDocument.
    """

    metadata_dict, body = parse_front_matter(text)

    metadata = DocumentMetadata(
        document_id=metadata_dict["document_id"],
        title=metadata_dict["title"],
        department=metadata_dict["department"],
        section=metadata_dict["section"],
        document_type=metadata_dict["document_type"],
        version=metadata_dict["version"],
        access_level=metadata_dict["access_level"],
    )

    sections = parse_sections(body)

    return TechNovaDocument(
        content=body,
        metadata=metadata,
        sections=sections,
    )
