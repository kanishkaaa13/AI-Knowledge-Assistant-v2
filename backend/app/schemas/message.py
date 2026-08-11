import json
import logging
import uuid

from pydantic import Field, field_validator

from app.schemas.common import ORMBaseSchema, TimestampSchema

logger = logging.getLogger(__name__)


class MessageBase(ORMBaseSchema):
    role: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    sequence_number: int = Field(ge=0)


class MessageCreate(MessageBase):
    conversation_id: uuid.UUID


class MessageUpdate(ORMBaseSchema):
    content: str | None = Field(default=None, min_length=1)


class MessageRead(MessageBase, TimestampSchema):
    conversation_id: uuid.UUID
    citations: list[dict] | None = None

    @field_validator("citations", mode="before")
    @classmethod
    def parse_citations(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Persisted citations are corrupt: keep the message readable but
                # make the data problem visible in the logs.
                logger.error("Discarding unparsable stored citations: %r", v)
                return []
        return v
