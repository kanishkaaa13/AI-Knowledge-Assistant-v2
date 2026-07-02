import uuid

from pydantic import Field

from app.schemas.common import ORMBaseSchema, TimestampSchema


class MessageBase(ORMBaseSchema):
    role: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)
    sequence_number: int = Field(ge=0)


class MessageCreate(MessageBase):
    conversation_id: uuid.UUID


class MessageUpdate(ORMBaseSchema):
    content: str | None = Field(default=None, min_length=1)


import json
from pydantic import field_validator

class MessageRead(MessageBase, TimestampSchema):
    conversation_id: uuid.UUID
    citations: list[dict] | None = None

    @field_validator("citations", mode="before")
    @classmethod
    def parse_citations(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return []
        return v
