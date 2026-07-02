from __future__ import annotations

import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.conversation import ConversationDetail, ConversationListItem
from app.schemas.message import MessageRead


class ChatMemoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)

    def list_conversations(
        self,
        *,
        user: User,
        search: str | None = None,
        is_favorite: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[ConversationListItem]:
        from datetime import datetime
        d_from = datetime.fromisoformat(date_from) if date_from else None
        d_to = datetime.fromisoformat(date_to) if date_to else None
        items = self.conversations.search_by_user(
            user.id,
            search,
            is_favorite=is_favorite,
            date_from=d_from,
            date_to=d_to,
        )
        return [self._build_list_item(conversation) for conversation in items]

    def get_conversation(self, *, user: User, conversation_id: uuid.UUID) -> ConversationDetail:
        conversation = self._get_owned_conversation(user=user, conversation_id=conversation_id)
        messages = self.messages.list_by_conversation(conversation.id)
        return ConversationDetail(
            id=str(conversation.id),
            user_id=str(conversation.user_id),
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            is_favorite=conversation.is_favorite,
            messages=[MessageRead.model_validate(message) for message in messages],
        )

    def create_conversation(
        self,
        *,
        user: User,
        title: str | None = None,
        initial_message: str | None = None,
    ) -> ConversationDetail:
        resolved_title = title or self.generate_title(initial_message) or "New conversation"
        summary = self.summarize(initial_message) if initial_message else "Awaiting first message."
        conversation = self.conversations.create(
            user_id=user.id,
            title=resolved_title,
            summary=summary,
        )

        messages: list[MessageRead] = []
        if initial_message:
            message = self.append_message(
                conversation=conversation,
                role="user",
                content=initial_message,
            )
            messages.append(MessageRead.model_validate(message))

        return ConversationDetail(
            id=str(conversation.id),
            user_id=str(conversation.user_id),
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            is_favorite=conversation.is_favorite,
            messages=messages,
        )

    def get_or_create_conversation(
        self,
        *,
        user: User,
        conversation_id: uuid.UUID | None,
        initial_user_message: str,
    ) -> Conversation:
        if conversation_id:
            return self._get_owned_conversation(user=user, conversation_id=conversation_id)

        created = self.create_conversation(
            user=user,
            initial_message=initial_user_message,
        )
        conversation = self._get_owned_conversation(user=user, conversation_id=created.id)
        return conversation

    def append_message(self, *, conversation: Conversation, role: str, content: str, citations: str | None = None) -> Message:
        next_sequence = self.messages.get_next_sequence_number(conversation.id)
        message = self.messages.create(
            conversation_id=conversation.id,
            role=role,
            content=content,
            sequence_number=next_sequence,
            citations=citations,
        )
        return message

    def rename_conversation(
        self,
        *,
        user: User,
        conversation_id: uuid.UUID,
        title: str,
    ) -> ConversationListItem:
        conversation = self._get_owned_conversation(user=user, conversation_id=conversation_id)
        updated = self.conversations.update(conversation, title=title.strip())
        return self._build_list_item(updated)

    def toggle_favorite(
        self,
        *,
        user: User,
        conversation_id: uuid.UUID,
        is_favorite: bool,
    ) -> ConversationListItem:
        conversation = self._get_owned_conversation(user=user, conversation_id=conversation_id)
        updated = self.conversations.update(conversation, is_favorite=is_favorite)
        return self._build_list_item(updated)

    def delete_conversation(self, *, user: User, conversation_id: uuid.UUID) -> None:
        conversation = self._get_owned_conversation(user=user, conversation_id=conversation_id)
        self.conversations.delete(conversation)

    def sync_conversation_after_response(
        self,
        *,
        conversation: Conversation,
        user_message: str,
        assistant_message: str,
        citations: str | None = None,
    ) -> Conversation:
        last_message = self.messages.get_last_message(conversation.id)
        if (
            last_message is None
            or last_message.role != "assistant"
            or last_message.content != assistant_message
        ):
            self.append_message(
                conversation=conversation,
                role="assistant",
                content=assistant_message,
                citations=citations,
            )

        title = conversation.title
        if conversation.title.strip().lower() in {"new conversation", "untitled conversation"}:
            title = self.generate_title(user_message) or conversation.title

        updated = self.conversations.update(
            conversation,
            title=title,
            summary=self.summarize(assistant_message or user_message),
        )
        return updated

    def generate_title(self, text: str | None) -> str:
        if not text:
            return "New conversation"

        cleaned = re.sub(r"`{1,3}.*?`{1,3}", " ", text, flags=re.DOTALL)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;!?-_")
        if not cleaned:
            return "New conversation"

        words = cleaned.split(" ")[:7]
        title = " ".join(words).strip()
        if len(cleaned.split(" ")) > 7:
            title = f"{title}..."
        return title[:255]

    def summarize(self, text: str | None, limit: int = 160) -> str | None:
        if not text:
            return None

        compact = re.sub(r"\s+", " ", text).strip()
        return compact if len(compact) <= limit else f"{compact[: limit - 3].rstrip()}..."

    def export_conversation(self, *, user: User, conversation_id: uuid.UUID) -> str:
        conversation = self._get_owned_conversation(user=user, conversation_id=conversation_id)
        messages = self.messages.list_by_conversation(conversation.id)
        lines = [f"# {conversation.title}", ""]
        for message in messages:
            lines.append(f"## {message.role.title()}")
            lines.append(message.content)
            lines.append("")
        return "\n".join(lines).strip()

    def _build_list_item(self, conversation: Conversation) -> ConversationListItem:
        last_message = self.messages.get_last_message(conversation.id)
        message_count = self.conversations.get_message_count(conversation.id)
        return ConversationListItem(
            id=str(conversation.id),
            user_id=str(conversation.user_id),
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            is_favorite=conversation.is_favorite,
            is_pinned=conversation.is_pinned,
            message_count=message_count,
            last_message_preview=self.summarize(last_message.content if last_message else conversation.summary),
        )

    def _get_owned_conversation(self, *, user: User, conversation_id: uuid.UUID) -> Conversation:
        conversation = self.conversations.get_by_user(user.id, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return conversation

    def toggle_pin(self, *, user: User, conversation_id: uuid.UUID, is_pinned: bool) -> ConversationListItem:
        conversation = self._get_owned_conversation(user=user, conversation_id=conversation_id)
        updated = self.conversations.update(conversation, is_pinned=is_pinned)
        return self._build_list_item(updated)
