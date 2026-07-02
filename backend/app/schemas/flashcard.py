import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class FlashcardBase(BaseModel):
    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)
    difficulty: str = Field("medium", max_length=20)
    is_starred: bool = False
    tags: Optional[str] = None
    source_context: Optional[str] = None
    document_id: Optional[uuid.UUID] = None

class FlashcardCreate(FlashcardBase):
    pass

class FlashcardUpdate(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    difficulty: Optional[str] = None
    is_starred: Optional[bool] = None
    tags: Optional[str] = None
    source_context: Optional[str] = None

class FlashcardRead(FlashcardBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FlashcardGenerateRequest(BaseModel):
    query: Optional[str] = Field(None, description="Optional query to focus generation")
    document_ids: List[str] = Field(default_factory=list, description="Documents to generate from")
    count: int = Field(5, ge=1, le=20)
    model: str = Field("llama3")
