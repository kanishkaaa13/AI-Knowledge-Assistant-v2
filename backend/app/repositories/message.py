import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, db: Session) -> None:
        super().__init__(Message, db)

    def list_by_conversation(self, conversation_id: uuid.UUID) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number.asc(), Message.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_next_sequence_number(self, conversation_id: uuid.UUID) -> int:
        statement = select(func.max(Message.sequence_number)).where(
            Message.conversation_id == conversation_id
        )
        current_max = self.db.scalar(statement)
        return 0 if current_max is None else int(current_max) + 1

    def get_last_message(self, conversation_id: uuid.UUID) -> Message | None:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number.desc(), Message.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def count_by_user_and_role(self, user_id: uuid.UUID, role: str | None = None) -> int:
        statement = select(func.count(Message.id)).join(
            Conversation, Conversation.id == Message.conversation_id
        ).where(Conversation.user_id == user_id)
        if role:
            statement = statement.where(Message.role == role)
        return int(self.db.scalar(statement) or 0)

    def message_counts_by_day(self, user_id: uuid.UUID, role: str | None = None, limit: int = 7) -> list[tuple[datetime, int]]:
        statement = (
            select(func.date_trunc("day", Message.created_at), func.count(Message.id))
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Conversation.user_id == user_id)
        )
        if role:
            statement = statement.where(Message.role == role)
        statement = (
            statement.group_by(func.date_trunc("day", Message.created_at))
            .order_by(func.date_trunc("day", Message.created_at).desc())
            .limit(limit)
        )
        return [(row[0], int(row[1])) for row in self.db.execute(statement).all()]
