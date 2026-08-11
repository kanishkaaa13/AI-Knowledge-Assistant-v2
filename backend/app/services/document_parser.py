from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from io import BytesIO

from docx import Document as DocxDocument
from pypdf import PdfReader
from fastapi import HTTPException

from app.models.uploaded_document import UploadedDocument
from app.services.document_upload import read_encrypted_document_bytes

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocumentPage:
    page_number: int
    text: str


class StoredDocumentParser:
    def parse(self, document: UploadedDocument) -> list[ParsedDocumentPage]:
        try:
            file_bytes = read_encrypted_document_bytes(document)
        except HTTPException as e:
            # Log the error and raise with clear message
            logger.error(f"[PARSER] Failed to read document {document.id}: {e.detail}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Document file cannot be read: {e.detail}. The file may be corrupted or encryption may have failed during upload."
            ) from e

        extension = document.file_extension.lower()
        if extension == ".pdf":
            reader = PdfReader(BytesIO(file_bytes))
            return [
                ParsedDocumentPage(page_number=index + 1, text=page.extract_text() or "")
                for index, page in enumerate(reader.pages)
            ]

        if extension == ".docx":
            docx = DocxDocument(BytesIO(file_bytes))
            content = "\n".join(paragraph.text for paragraph in docx.paragraphs)
            return [ParsedDocumentPage(page_number=1, text=content)]

        if extension in {".txt", ".md"}:
            try:
                content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                content = file_bytes.decode("latin-1")
            return [ParsedDocumentPage(page_number=1, text=content)]

        return []
