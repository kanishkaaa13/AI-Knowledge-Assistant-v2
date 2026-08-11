"""Shared helpers for user-isolated document storage on disk."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.core.config import settings


def sanitize_file_name(file_name: str, *, fallback: str = "document") -> str:
    """Reduce a file name to a storage-safe slug."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", file_name).strip("._-")
    return cleaned or fallback


def resolve_user_upload_dir(user_id: uuid.UUID) -> Path:
    """Return (creating if needed) the upload directory for a user."""
    user_dir = Path(settings.UPLOAD_ROOT_DIR) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir
