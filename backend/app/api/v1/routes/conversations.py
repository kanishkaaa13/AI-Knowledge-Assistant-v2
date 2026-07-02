import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rate_limit import apply_rate_limit
from app.core.sanitize import ensure_present, sanitize_text
from app.db.session import get_db
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationFavoriteUpdate,
    ConversationListItem,
    ConversationRename,
    ConversationPinUpdate,
)
from app.services.chat_memory import ChatMemoryService

router = APIRouter()


@router.get("", response_model=list[ConversationListItem])
def list_conversations(
    request: Request,
    search: str | None = Query(default=None, min_length=1, max_length=255),
    is_favorite: bool | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationListItem]:
    apply_rate_limit(request, scope="conversations-list", limit=60, user_id=str(current_user.id))
    safe_search = sanitize_text(search, max_length=255) if search else None
    return ChatMemoryService(db).list_conversations(
        user=current_user,
        search=safe_search,
        is_favorite=is_favorite,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("", response_model=ConversationDetail, status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: Request,
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationDetail:
    apply_rate_limit(request, scope="conversations-create", limit=30, user_id=str(current_user.id))
    return ChatMemoryService(db).create_conversation(
        user=current_user,
        title=sanitize_text(payload.title, max_length=255) if payload.title else None,
        initial_message=sanitize_text(payload.initial_message, max_length=4000)
        if payload.initial_message
        else None,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationDetail:
    return ChatMemoryService(db).get_conversation(
        user=current_user,
        conversation_id=conversation_id,
    )


@router.patch("/{conversation_id}", response_model=ConversationListItem)
def rename_conversation(
    request: Request,
    conversation_id: uuid.UUID,
    payload: ConversationRename,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationListItem:
    apply_rate_limit(request, scope="conversations-rename", limit=20, user_id=str(current_user.id))
    return ChatMemoryService(db).rename_conversation(
        user=current_user,
        conversation_id=conversation_id,
        title=ensure_present(sanitize_text(payload.title, max_length=255), field_name="title"),
    )


@router.patch("/{conversation_id}/favorite", response_model=ConversationListItem)
def favorite_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationFavoriteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationListItem:
    return ChatMemoryService(db).toggle_favorite(
        user=current_user,
        conversation_id=conversation_id,
        is_favorite=payload.is_favorite,
    )


@router.patch("/{conversation_id}/pin", response_model=ConversationListItem)
def pin_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationPinUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationListItem:
    return ChatMemoryService(db).toggle_pin(
        user=current_user,
        conversation_id=conversation_id,
        is_pinned=payload.is_pinned,
    )


@router.get("/{conversation_id}/export", response_class=PlainTextResponse)
def export_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> str:
    return ChatMemoryService(db).export_conversation(
        user=current_user,
        conversation_id=conversation_id,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    request: Request,
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    apply_rate_limit(request, scope="conversations-delete", limit=20, user_id=str(current_user.id))
    ChatMemoryService(db).delete_conversation(
        user=current_user,
        conversation_id=conversation_id,
    )
    return {"message": "Conversation deleted."}
