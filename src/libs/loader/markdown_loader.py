"""Markdown Loader for .md files.

Extracts text content and optionally extracts the first # heading as title.
"""

from __future__ import annotations

from pathlib import Path

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader


class MarkdownLoader(BaseLoader):
    """Markdown file loader.

    Reads .md files and extracts the first # heading as the document title.

    Example:
        >>> loader = MarkdownLoader()
        >>> doc = loader.load("README.md")
        >>> assert "title" in doc.metadata
    """

    def load(self, file_path: str | Path) -> Document:
        path = self._validate_file(file_path)
        if path.suffix.lower() not in (".md", ".mdx"):
            raise ValueError(f"File is not a Markdown file: {path}")

        text = path.read_text(encoding="utf-8")

        # Extract title from first # heading
        title = None
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        metadata = {
            "source_path": str(path),
            "doc_type": "markdown",
            "file_name": path.name,
        }
        if title:
            metadata["title"] = title

        return Document(
            id=f"doc_md_{path.stem}",
            text=text,
            metadata=metadata,
        )
