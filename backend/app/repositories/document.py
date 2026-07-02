import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.uploaded_document import UploadedDocument
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[UploadedDocument]):
    def __init__(self, db: Session) -> None:
        super().__init__(UploadedDocument, db)

    def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        tag: str | None = None,
        favorites_only: bool = False,
    ) -> list[UploadedDocument]:
        statement = select(UploadedDocument).where(UploadedDocument.user_id == user_id)
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    UploadedDocument.title.ilike(pattern),
                    UploadedDocument.file_name.ilike(pattern),
                    UploadedDocument.extracted_text.ilike(pattern),
                    UploadedDocument.ai_summary.ilike(pattern),
                )
            )
        if tag:
            statement = statement.where(UploadedDocument.tags.ilike(f"%{tag}%"))
        if favorites_only:
            statement = statement.where(UploadedDocument.is_favorite.is_(True))

        statement = (
            statement.order_by(UploadedDocument.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(statement).all())

    def count_filtered_by_user(
        self,
        user_id: uuid.UUID,
        *,
        search: str | None = None,
        tag: str | None = None,
        favorites_only: bool = False,
    ) -> int:
        statement = select(func.count(UploadedDocument.id)).where(UploadedDocument.user_id == user_id)
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    UploadedDocument.title.ilike(pattern),
                    UploadedDocument.file_name.ilike(pattern),
                    UploadedDocument.extracted_text.ilike(pattern),
                    UploadedDocument.ai_summary.ilike(pattern),
                )
            )
        if tag:
            statement = statement.where(UploadedDocument.tags.ilike(f"%{tag}%"))
        if favorites_only:
            statement = statement.where(UploadedDocument.is_favorite.is_(True))
        return int(self.db.scalar(statement) or 0)

    def get_by_user(self, document_id: uuid.UUID, user_id: uuid.UUID) -> UploadedDocument | None:
        statement = select(UploadedDocument).where(
            UploadedDocument.id == document_id,
            UploadedDocument.user_id == user_id,
        )
        return self.db.scalar(statement)

    def get_by_user_and_checksum(
        self, user_id: uuid.UUID, checksum: str
    ) -> UploadedDocument | None:
        statement = select(UploadedDocument).where(
            UploadedDocument.user_id == user_id,
            UploadedDocument.checksum == checksum,
        )
        return self.db.scalar(statement)

    def list_chunks(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(statement).all())

    def count_by_user(self, user_id: uuid.UUID) -> int:
        statement = select(func.count(UploadedDocument.id)).where(UploadedDocument.user_id == user_id)
        return int(self.db.scalar(statement) or 0)

    def total_storage_by_user(self, user_id: uuid.UUID) -> int:
        statement = select(func.coalesce(func.sum(UploadedDocument.file_size), 0)).where(
            UploadedDocument.user_id == user_id
        )
        return int(self.db.scalar(statement) or 0)

    def recent_by_user(self, user_id: uuid.UUID, limit: int = 5) -> list[UploadedDocument]:
        statement = (
            select(UploadedDocument)
            .where(UploadedDocument.user_id == user_id)
            .order_by(UploadedDocument.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def upload_counts_by_day(self, user_id: uuid.UUID, limit: int = 7) -> list[tuple[datetime, int]]:
        statement = (
            select(func.date_trunc("day", UploadedDocument.created_at), func.count(UploadedDocument.id))
            .where(UploadedDocument.user_id == user_id)
            .group_by(func.date_trunc("day", UploadedDocument.created_at))
            .order_by(func.date_trunc("day", UploadedDocument.created_at).desc())
            .limit(limit)
        )
        return [(row[0], int(row[1])) for row in self.db.execute(statement).all()]

    def list_by_ids(self, user_id: uuid.UUID, document_ids: list[uuid.UUID]) -> list[UploadedDocument]:
        if not document_ids:
            return []
        statement = select(UploadedDocument).where(
            UploadedDocument.user_id == user_id,
            UploadedDocument.id.in_(document_ids),
        )
        return list(self.db.scalars(statement).all())
