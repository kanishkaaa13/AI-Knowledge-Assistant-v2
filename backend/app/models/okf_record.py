from __future__ import annotations

import uuid
from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class OKFRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "okf_records"

    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    source_document = relationship("UploadedDocument", backref="okf_records")
