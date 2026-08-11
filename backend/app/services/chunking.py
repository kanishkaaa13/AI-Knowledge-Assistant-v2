"""Shared sentence-aware text chunking used by the ingestion paths."""

from __future__ import annotations

import re

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks, preferring sentence then word boundaries."""
    if not text or not text.strip():
        return []

    text = re.sub(r"\s+", " ", text.strip())
    text_length = len(text)

    chunks: list[str] = []
    start = 0
    while start < text_length:
        end = start + chunk_size

        if end < text_length:
            for index in range(end, max(start + chunk_size // 2, start), -1):
                if text[index] in ".!?" and index + 1 < text_length and text[index + 1] == " ":
                    end = index + 1
                    break
            else:
                for index in range(end, max(start + chunk_size // 2, start), -1):
                    if text[index] == " ":
                        end = index
                        break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = max(end - chunk_overlap, 0)

    return chunks
