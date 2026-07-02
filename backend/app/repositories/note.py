from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.note import Note
from app.repositories.base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    def __init__(self, db: Session) -> None:
        super().__init__(Note, db)

    def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        search: str | None = None,
        pinned_only: bool = False,
    ) -> list[Note]:
        stmt = select(Note).where(Note.user_id == user_id)
        if pinned_only:
            stmt = stmt.where(Note.is_pinned == True)  # noqa: E712
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Note.title.ilike(pattern),
                    Note.content.ilike(pattern),
                    Note.tags.ilike(pattern),
                )
            )
        stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_by_user(self, user_id: uuid.UUID, note_id: uuid.UUID) -> Note | None:
        stmt = select(Note).where(Note.user_id == user_id, Note.id == note_id)
        return self.db.scalar(stmt)

    def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Note.id)).where(Note.user_id == user_id)
        return int(self.db.scalar(stmt) or 0)
