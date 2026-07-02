from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Flashcard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "flashcards"
    __table_args__ = (
        Index("ix_flashcards_user_id_updated_at", "user_id", "updated_at"),
        Index("ix_flashcards_user_id_document_id", "user_id", "document_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Optional: flashcard may be linked to a specific document
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    # easy | medium | hard
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    is_starred: Mapped[bool] = mapped_column(default=False, nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="flashcards")
