import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.flashcard import FlashcardCreate, FlashcardRead, FlashcardUpdate, FlashcardGenerateRequest
from app.services.flashcard_service import FlashcardService

router = APIRouter()

@router.get("/", response_model=List[FlashcardRead])
def list_flashcards(
    document_id: Optional[uuid.UUID] = Query(None, description="Filter flashcards by document"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List flashcards for the current user."""
    service = FlashcardService(db)
    return service.list_flashcards(current_user, document_id=document_id)

@router.post("/", response_model=FlashcardRead, status_code=status.HTTP_201_CREATED)
def create_flashcard(
    payload: FlashcardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a flashcard manually."""
    service = FlashcardService(db)
    return service.create_flashcard(current_user, payload)

@router.post("/generate", response_model=List[FlashcardRead])
async def generate_flashcards(
    payload: FlashcardGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate study flashcards from document context using local LLM."""
    service = FlashcardService(db)
    return await service.generate_flashcards(
        user=current_user,
        document_ids=payload.document_ids,
        query=payload.query,
        count=payload.count,
        model=payload.model
    )

@router.patch("/{flashcard_id}", response_model=FlashcardRead)
def update_flashcard(
    flashcard_id: uuid.UUID,
    payload: FlashcardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a flashcard."""
    service = FlashcardService(db)
    return service.update_flashcard(current_user, flashcard_id, payload)

@router.delete("/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(
    flashcard_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a flashcard."""
    service = FlashcardService(db)
    service.delete_flashcard(current_user, flashcard_id)
    return None
