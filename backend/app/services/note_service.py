import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.note import Note
from app.repositories.note import NoteRepository
from app.schemas.note import NoteCreate, NoteUpdate

class NoteService:
    def __init__(self, db: Session) -> None:
        self.repository = NoteRepository(db)

    def list_notes(self, user: User, search: Optional[str] = None, pinned_only: bool = False) -> List[Note]:
        return self.repository.list_by_user(user.id, search=search, pinned_only=pinned_only)

    def get_note(self, user: User, note_id: uuid.UUID) -> Note:
        note = self.repository.get_by_user(user.id, note_id)
        if not note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
        return note

    def create_note(self, user: User, schema: NoteCreate) -> Note:
        note_data = schema.model_dump()
        note_data["user_id"] = user.id
        return self.repository.create(**note_data)

    def update_note(self, user: User, note_id: uuid.UUID, schema: NoteUpdate) -> Note:
        note = self.get_note(user, note_id)
        update_data = schema.model_dump(exclude_unset=True)
        return self.repository.update(note, **update_data)

    def delete_note(self, user: User, note_id: uuid.UUID) -> None:
        note = self.get_note(user, note_id)
        self.repository.delete(note)

    def toggle_pin(self, user: User, note_id: uuid.UUID) -> Note:
        note = self.get_note(user, note_id)
        return self.repository.update(note, is_pinned=not note.is_pinned)
