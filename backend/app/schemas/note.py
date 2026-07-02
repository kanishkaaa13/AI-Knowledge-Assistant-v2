import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class NoteBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str = Field("")
    is_pinned: bool = Field(False)
    tags: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    tags: Optional[str] = None

class NoteRead(NoteBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
