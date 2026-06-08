"""TXT Loader implementation for plain text files.

This module implements a simple text file loader that reads .txt files
and returns a standardized Document object.
"""

from __future__ import annotations

from pathlib import Path

from src.core.types import Document
from src.libs.loader.base_loader import BaseLoader


class TxtLoader(BaseLoader):
    """Plain text file loader.

    Reads .txt files with UTF-8 encoding and wraps content into a Document.

    Example:
        >>> loader = TxtLoader()
        >>> doc = loader.load("notes.txt")
        >>> assert doc.text
        >>> assert doc.metadata["source_path"].endswith(".txt")
    """

    def load(self, file_path: str | Path) -> Document:
        path = self._validate_file(file_path)
        if path.suffix.lower() != ".txt":
            raise ValueError(f"File is not a .txt file: {path}")

        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            raise RuntimeError(f"Failed to read text file {path}: {e}") from e

        return Document(
            id=f"doc_txt_{path.stem}",
            text=text,
            metadata={
                "source_path": str(path),
                "doc_type": "txt",
                "file_name": path.name,
            },
        )
