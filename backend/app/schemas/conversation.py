import uuid

from pydantic import Field

from app.schemas.common import ORMBaseSchema, TimestampSchema
from app.schemas.message import MessageRead


class ConversationBase(ORMBaseSchema):
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = None
    is_favorite: bool = False
    is_pinned: bool = False


class ConversationCreate(ORMBaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    initial_message: str | None = Field(default=None, min_length=1)


class ConversationUpdate(ORMBaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = None
    is_favorite: bool | None = None
    is_pinned: bool | None = None


class ConversationRead(ConversationBase, TimestampSchema):
    user_id: uuid.UUID


class ConversationListItem(ConversationRead):
    message_count: int = 0
    last_message_preview: str | None = None


class ConversationDetail(ConversationRead):
    messages: list[MessageRead] = Field(default_factory=list)


class ConversationRename(ORMBaseSchema):
    title: str = Field(min_length=1, max_length=255)


class ConversationFavoriteUpdate(ORMBaseSchema):
    is_favorite: bool


class ConversationPinUpdate(ORMBaseSchema):
    is_pinned: bool
