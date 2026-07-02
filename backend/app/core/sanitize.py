from __future__ import annotations

import re

from fastapi import HTTPException, status


CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
SCRIPT_TAG_PATTERN = re.compile(r"<\s*/?\s*script\b", re.IGNORECASE)


def sanitize_text(value: str, *, max_length: int | None = None) -> str:
    cleaned = CONTROL_CHAR_PATTERN.sub("", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if SCRIPT_TAG_PATTERN.search(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input contains unsupported markup.",
        )
    if max_length is not None:
        cleaned = cleaned[:max_length].strip()
    return cleaned


def ensure_present(value: str, *, field_name: str) -> str:
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty.",
        )
    return value
