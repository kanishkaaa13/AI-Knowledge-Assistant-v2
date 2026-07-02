import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.note import NoteCreate, NoteRead, NoteUpdate
from app.services.note_service import NoteService

router = APIRouter()

@router.get("/", response_model=List[NoteRead])
def list_notes(
    search: Optional[str] = Query(None, description="Search note titles, content, or tags"),
    pinned_only: bool = Query(False, description="Filter only pinned notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List notes for the current user."""
    service = NoteService(db)
    return service.list_notes(current_user, search=search, pinned_only=pinned_only)

@router.post("/", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new note."""
    service = NoteService(db)
    return service.create_note(current_user, payload)

@router.get("/{note_id}", response_model=NoteRead)
def get_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get note details."""
    service = NoteService(db)
    return service.get_note(current_user, note_id)

@router.patch("/{note_id}", response_model=NoteRead)
def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update note content."""
    service = NoteService(db)
    return service.update_note(current_user, note_id, payload)

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a note."""
    service = NoteService(db)
    service.delete_note(current_user, note_id)
    return None

@router.post("/{note_id}/pin", response_model=NoteRead)
def toggle_pin_note(
    note_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pin or unpin a note."""
    service = NoteService(db)
    return service.toggle_pin(current_user, note_id)
