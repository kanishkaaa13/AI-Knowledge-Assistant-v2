from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _build_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class EncryptionService:
    def __init__(self) -> None:
        self.fernet = Fernet(_build_fernet_key(settings.FERNET_SECRET_KEY))

    def encrypt_bytes(self, payload: bytes) -> bytes:
        return self.fernet.encrypt(payload)

    def decrypt_bytes(self, payload: bytes) -> bytes:
        return self.fernet.decrypt(payload)


encryption_service = EncryptionService()
