from __future__ import annotations

from app.core.config import settings
from app.models.user import User
from app.repositories.conversation import ConversationRepository
from app.repositories.document import DocumentRepository
from app.repositories.message import MessageRepository
from app.schemas.assistant import (
    AIUsageStats,
    AnalyticsMetric,
    AnalyticsOverview,
    AnalyticsSeriesPoint,
    RecentUploadItem,
)


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    unit = units[0]
    for next_unit in units:
        unit = next_unit
        if value < 1024 or next_unit == units[-1]:
            break
        value /= 1024
    return f"{value:.1f} {unit}"


class AnalyticsService:
    def __init__(self, document_repository: DocumentRepository, conversation_repository: ConversationRepository, message_repository: MessageRepository) -> None:
        self.documents = document_repository
        self.conversations = conversation_repository
        self.messages = message_repository

    def build_overview(self, *, user: User) -> AnalyticsOverview:
        total_documents = self.documents.count_by_user(user.id)
        total_chats = self.conversations.count_by_user(user.id)
        storage_usage = self.documents.total_storage_by_user(user.id)
        total_messages = self.messages.count_by_user_and_role(user.id)
        assistant_messages = self.messages.count_by_user_and_role(user.id, "assistant")
        user_messages = self.messages.count_by_user_and_role(user.id, "user")

        recent_uploads = [
            RecentUploadItem(
                id=str(document.id),
                title=document.title,
                file_name=document.file_name,
                file_size=document.file_size or 0,
                uploaded_at=document.created_at.isoformat(),
                status=document.status,
            )
            for document in self.documents.recent_by_user(user.id, limit=6)
        ]

        uploads_timeline = [
            AnalyticsSeriesPoint(label=day.strftime("%b %d"), value=count)
            for day, count in reversed(self.documents.upload_counts_by_day(user.id))
        ]
        chats_timeline = [
            AnalyticsSeriesPoint(label=day.strftime("%b %d"), value=count)
            for day, count in reversed(self.conversations.conversation_counts_by_day(user.id))
        ]
        messages_timeline = [
            AnalyticsSeriesPoint(label=day.strftime("%b %d"), value=count)
            for day, count in reversed(self.messages.message_counts_by_day(user.id))
        ]

        average_messages_per_chat = round(total_messages / total_chats, 1) if total_chats else 0.0

        metrics = [
            AnalyticsMetric(
                label="Total documents",
                value=str(total_documents),
                detail="Indexed knowledge sources stored in your private workspace.",
            ),
            AnalyticsMetric(
                label="Total chats",
                value=str(total_chats),
                detail="Persistent conversation threads available in memory.",
            ),
            AnalyticsMetric(
                label="Storage usage",
                value=format_bytes(storage_usage),
                detail="Plaintext-equivalent file size before encryption overhead.",
            ),
            AnalyticsMetric(
                label="AI usage",
                value=str(assistant_messages),
                detail="Assistant replies generated locally from your grounded context.",
            ),
        ]

        ai_usage = AIUsageStats(
            total_messages=total_messages,
            assistant_messages=assistant_messages,
            user_messages=user_messages,
            average_messages_per_chat=average_messages_per_chat,
            local_only_inference=settings.ENFORCE_LOCAL_ONLY_AI,
            primary_model=settings.OLLAMA_DEFAULT_MODEL,
        )

        return AnalyticsOverview(
            metrics=metrics,
            uploads_timeline=uploads_timeline,
            chats_timeline=chats_timeline,
            messages_timeline=messages_timeline,
            recent_uploads=recent_uploads,
            ai_usage=ai_usage,
        )
