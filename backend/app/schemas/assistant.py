from pydantic import BaseModel, Field

from app.schemas.rag import RetrievedChunk, ChatChunk
from app.core.config import settings


class SummaryStat(BaseModel):
    label: str
    value: str


class DashboardSummary(BaseModel):
    title: str
    description: str
    stats: list[SummaryStat]


class AnalyticsMetric(BaseModel):
    label: str
    value: str
    detail: str


class AnalyticsSeriesPoint(BaseModel):
    label: str
    value: int


class RecentUploadItem(BaseModel):
    id: str
    title: str
    file_name: str
    file_size: int
    uploaded_at: str
    status: str


class AIUsageStats(BaseModel):
    total_messages: int
    assistant_messages: int
    user_messages: int
    average_messages_per_chat: float
    local_only_inference: bool
    primary_model: str


class AnalyticsOverview(BaseModel):
    metrics: list[AnalyticsMetric]
    uploads_timeline: list[AnalyticsSeriesPoint]
    chats_timeline: list[AnalyticsSeriesPoint]
    messages_timeline: list[AnalyticsSeriesPoint]
    recent_uploads: list[RecentUploadItem]
    ai_usage: AIUsageStats


class AssistantSummaryRequest(BaseModel):
    query: str = Field(min_length=1)
    model: str = Field(default_factory=lambda: settings.OLLAMA_DEFAULT_MODEL)
    document_ids: list[str] = Field(default_factory=list)


class AssistantSummaryResponse(BaseModel):
    summary: str
    context: str
    chunks: list[ChatChunk]


class QuizItem(BaseModel):
    question: str
    answer: str
    difficulty: str


class AssistantQuizResponse(BaseModel):
    questions: list[QuizItem]
    chunks: list[ChatChunk]
    context: str


class SuggestedPromptsResponse(BaseModel):
    prompts: list[str]
    chunks: list[ChatChunk]


class SemanticDocumentSearchItem(BaseModel):
    document_id: str
    title: str
    filename: str
    excerpt: str
    score: float
    tags: list[str] = Field(default_factory=list)


class SemanticDocumentSearchResponse(BaseModel):
    results: list[SemanticDocumentSearchItem]


class StudyNotesRequest(BaseModel):
    query: str = Field(min_length=1)
    model: str = Field(default_factory=lambda: settings.OLLAMA_DEFAULT_MODEL)
    document_ids: list[str] = Field(default_factory=list)


class StudyNotesResponse(BaseModel):
    notes: str
    context: str
    chunks: list[ChatChunk]

