from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.flashcard import Flashcard
from app.repositories.base import BaseRepository


class FlashcardRepository(BaseRepository[Flashcard]):
    def __init__(self, db: Session) -> None:
        super().__init__(Flashcard, db)

    def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        document_id: uuid.UUID | None = None,
    ) -> list[Flashcard]:
        stmt = select(Flashcard).where(Flashcard.user_id == user_id)
        if document_id:
            stmt = stmt.where(Flashcard.document_id == document_id)
        stmt = stmt.order_by(Flashcard.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_by_user(self, user_id: uuid.UUID, flashcard_id: uuid.UUID) -> Flashcard | None:
        stmt = select(Flashcard).where(
            Flashcard.user_id == user_id,
            Flashcard.id == flashcard_id,
        )
        return self.db.scalar(stmt)

    def bulk_create(self, items: list[dict]) -> list[Flashcard]:
        flashcards = [Flashcard(**item) for item in items]
        self.db.add_all(flashcards)
        self.db.commit()
        for fc in flashcards:
            self.db.refresh(fc)
        return flashcards

    def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Flashcard.id)).where(Flashcard.user_id == user_id)
        return int(self.db.scalar(stmt) or 0)
