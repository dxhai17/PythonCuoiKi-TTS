"""File loader and text normalizer for plain text (.txt) and Markdown (.md) documents."""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_content_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash of document text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DocumentReader:
    """Handles file reading, encoding handling, and format validation."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".text"}

    @classmethod
    def load_document(cls, file_path: str | Path) -> tuple[str, str, str]:
        """
        Load document from disk, validate format, and return (content, filename, content_hash).

        Raises:
            FileNotFoundError: If the target file does not exist.
            ValueError: If file is empty or has an unsupported format.
        """
        path = Path(file_path).resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{path.suffix}'. Supported formats: {', '.join(sorted(cls.SUPPORTED_EXTENSIONS))}"
            )

        # Try UTF-8 first, fallback to Latin-1
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        cleaned = content.strip()
        if not cleaned:
            raise ValueError(f"Document '{path.name}' is empty.")

        content_hash = compute_content_hash(cleaned)
        return cleaned, path.name, content_hash
