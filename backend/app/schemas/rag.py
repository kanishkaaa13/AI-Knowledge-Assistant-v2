import uuid
from typing import Any

from pydantic import BaseModel, Field
from app.core.config import settings


class RetrievedChunk(BaseModel):
    """Full chunk record returned by the /retrieve endpoint (DB-hydrated)."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    filename: str
    page: int | None = None
    paragraph_index: int | None = None
    content: str
    score: float
    semantic_score: float
    keyword_score: float
    chunk_index: int
    upload_timestamp: str


class ChatChunk(BaseModel):
    """Lightweight chunk returned by /query and /chat/stream (no DB lookup required)."""

    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    query: str
    top_k: int
    chunks: list[RetrievedChunk]
    context: str


class AssistantQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=12)
    hybrid: bool = True
    model: str = Field(default_factory=lambda: settings.OLLAMA_DEFAULT_MODEL)
    conversation_id: uuid.UUID | None = None
    document_ids: list[str] = Field(default_factory=list)


class AssistantQueryResponse(BaseModel):
    query: str
    answer: str
    context: str
    chunks: list[ChatChunk]          # lightweight — no DB hydration needed
    prompt: str
    model: str
    conversation_id: uuid.UUID
    conversation_title: str
