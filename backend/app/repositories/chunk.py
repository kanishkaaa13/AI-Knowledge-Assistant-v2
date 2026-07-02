import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.repositories.base import BaseRepository


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    def __init__(self, db: Session) -> None:
        super().__init__(DocumentChunk, db)

    def list_by_document(self, document_id: uuid.UUID) -> list[DocumentChunk]:
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_by_documents(self, document_ids: list[uuid.UUID]) -> list[DocumentChunk]:
        if not document_ids:
            return []
        statement = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id.in_(document_ids))
            .order_by(DocumentChunk.document_id.asc(), DocumentChunk.chunk_index.asc())
        )
        return list(self.db.scalars(statement).all())

    def bulk_create(self, chunks: list[dict]) -> list[DocumentChunk]:
        entities = [DocumentChunk(**chunk) for chunk in chunks]
        self.db.add_all(entities)
        self.db.commit()
        for entity in entities:
            self.db.refresh(entity)
        return entities
