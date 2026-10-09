from pathlib import Path
from typing import List


SUPPORTED_EXTENSIONS = {".md", ".markdown"}


def discover_documents(root_dir: str) -> List[Path]:
    """
    Find all supported knowledge-base documents recursively.
    """
    root = Path(root_dir)

    if not root.exists():
        raise FileNotFoundError(
            f"Knowledge base directory does not exist: {root}"
        )

    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def load_document(path: Path) -> str:
    """
    Load a Markdown document as UTF-8 text.
    """
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")

    return path.read_text(encoding="utf-8")