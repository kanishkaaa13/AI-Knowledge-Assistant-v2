from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import app_cache
from app.core.config import settings
from app.models.document_chunk import DocumentChunk
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.repositories.chunk import DocumentChunkRepository
from app.repositories.document import DocumentRepository
from app.schemas.rag import RetrievedChunk, RetrievalResponse
from app.services.vector_store import VectorRecord, VectorSearchResult, get_vector_store_service
from app.services.document_parser import StoredDocumentParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def _chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Simple word-boundary text chunker."""
    import re
    text = re.sub(r"\s+", " ", text.strip())
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # find sentence boundary
            for i in range(end, max(start + chunk_size // 2, start), -1):
                if text[i] in ".!?" and i + 1 < len(text) and text[i + 1] == " ":
                    end = i + 1
                    break
            else:
                for i in range(end, max(start + chunk_size // 2, start), -1):
                    if text[i] == " ":
                        end = i
                        break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - chunk_overlap
        if start < 0:
            start = 0
    return chunks


class RAGIngestionService:
    """Handles indexing documents into ChromaDB (sync ingestion path)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.chunk_repository = DocumentChunkRepository(db)
        self.vector_store = get_vector_store_service()

    def index_document(self, document: UploadedDocument) -> list[DocumentChunk]:
        print(f"[INDEX] Starting indexing for document: {document.id} ({document.file_name!r})")
        print(f"[INDEX] Document status: {document.status!r}")
        print(f"[INDEX] Extracted text length: {len(document.extracted_text or '')} chars")

        # Use extracted_text stored in DB — avoids re-parsing the (possibly encrypted) file
        if not document.extracted_text or not document.extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has no extractable text to index.",
            )

        # Remove old chunks + vectors first
        existing_chunks = self.chunk_repository.list_by_document(document.id)
        if existing_chunks:
            print(f"[INDEX] Removing {len(existing_chunks)} existing chunks before re-index")
            self.delete_document_index(document.id)

        # Parse the document page-by-page (decrypts automatically)
        parser = StoredDocumentParser()
        pages = parser.parse(document)

        # Fallback to single page using extracted text if parsing returns empty list
        if not pages:
            from app.services.document_parser import ParsedDocumentPage
            pages = [ParsedDocumentPage(page_number=1, text=document.extracted_text or "")]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        )

        # Fetch associated OKF records
        from sqlalchemy import select
        from app.models.okf_record import OKFRecord
        import re

        okf_records = []
        try:
            okf_records = self.db.scalars(
                select(OKFRecord).where(OKFRecord.source_document_id == document.id)
            ).all()
        except Exception as e:
            print(f"[INDEX OKF ERROR] Failed to fetch OKF records: {e}")

        def find_best_okf_match(chunk_txt: str, okf_recs: list[OKFRecord]) -> OKFRecord | None:
            if not okf_recs:
                return None
            chunk_words = set(re.findall(r"\w+", chunk_txt.lower()))
            if not chunk_words:
                return okf_recs[0]
            
            best_m = None
            best_s = -1
            
            for record in okf_recs:
                title_words = set(re.findall(r"\w+", record.title.lower()))
                tags_words = {t.lower() for t in record.tags} if isinstance(record.tags, list) else set()
                record_words = title_words.union(tags_words)
                
                overlap = len(chunk_words.intersection(record_words))
                if overlap > best_s:
                    best_s = overlap
                    best_m = record
            return best_m

        base_metadata = {
            "document_id": str(document.id),
            "document_title": document.title,
            "user_id": str(document.user_id),
            "filename": document.file_name,
            "upload_timestamp": document.created_at.isoformat(),
            "tags": document.tags or "",
        }

        chunk_payloads: list[dict] = []
        vector_records: list[VectorRecord] = []
        global_chunk_index = 0

        for page in pages:
            # Detect paragraphs by double newlines
            paragraphs = [p.strip() for p in page.text.split("\n\n") if p.strip()]
            for p_idx, paragraph_text in enumerate(paragraphs, start=1):
                # Split paragraph into chunks if it is too large
                if len(paragraph_text) <= settings.RAG_CHUNK_SIZE:
                    paragraph_chunks = [paragraph_text]
                else:
                    paragraph_chunks = splitter.split_text(paragraph_text)

                for chunk_text in paragraph_chunks:
                    if not chunk_text.strip():
                        continue
                    vector_id = f"{document.id}:{global_chunk_index}"
                    
                    # Match nearest OKFRecord
                    best_okf = find_best_okf_match(chunk_text, okf_records)
                    chunk_metadata = {
                        **base_metadata,
                        "chunk_index": global_chunk_index,
                        "chunk_id": vector_id,
                        "page": str(page.page_number),
                        "paragraph_index": str(p_idx),
                    }
                    if best_okf:
                        chunk_metadata["okf_type"] = best_okf.type
                        chunk_metadata["okf_tags"] = ",".join(best_okf.tags) if isinstance(best_okf.tags, list) else str(best_okf.tags)

                    chunk_payloads.append(
                        {
                            "document_id": document.id,
                            "chunk_index": global_chunk_index,
                            "page_number": page.page_number,
                            "paragraph_index": p_idx,
                            "content": chunk_text,
                            "token_count": len(chunk_text.split()),
                            "vector_id": vector_id,
                        }
                    )
                    vector_records.append(
                        VectorRecord(
                            id=vector_id,
                            document=chunk_text,
                            metadata=chunk_metadata,
                        )
                    )
                    global_chunk_index += 1

        print(f"[INDEX] Created {global_chunk_index} page-and-paragraph-aware text chunks")

        if not chunk_payloads:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document text could not be split into chunks.",
            )

        created_chunks = self.chunk_repository.bulk_create(chunk_payloads)
        print(f"[INDEX] Stored {len(created_chunks)} chunk records in DB")

        try:
            print(f"[INDEX] Upserting {len(vector_records)} vectors into ChromaDB for user {document.user_id}")
            self.vector_store.upsert_vectors(user_id=document.user_id, records=vector_records)
        except Exception:
            logger.exception("ChromaDB upsert failed -- rolling back chunk records.")
            for chunk in created_chunks:
                self.db.delete(chunk)
            self.db.commit()
            raise

        print(f"[INDEX] ChromaDB upsert complete [OK]")

        document.status = "indexed"
        document.processing_error = None
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        app_cache.delete_prefix(f"retrieval:{document.user_id}:")
        print(f"[INDEX] Document {document.id} indexed successfully ({len(created_chunks)} chunks) [OK]")
        return created_chunks

    def delete_document_index(self, document_id: uuid.UUID) -> None:
        chunks = self.chunk_repository.list_by_document(document_id)
        if not chunks:
            return

        document = chunks[0].document
        vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]
        if vector_ids:
            self.vector_store.delete_vectors(user_id=document.user_id, ids=vector_ids)
        for chunk in chunks:
            self.db.delete(chunk)
        self.db.commit()
        app_cache.delete_prefix(f"retrieval:{document.user_id}:")

    def update_document_index(self, document: UploadedDocument) -> list[DocumentChunk]:
        return self.index_document(document)


class RAGRetrievalService:
    """Retrieves relevant chunks from ChromaDB for a given query (async retrieval path)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.vector_store = get_vector_store_service()
        self.document_repository = DocumentRepository(db)
        self.chunk_repository = DocumentChunkRepository(db)

    async def retrieve(
        self,
        *,
        user: User,
        query: str,
        top_k: int | None = None,
        hybrid: bool = True,
        document_ids: list[str] | None = None,
        filters: dict | None = None,
    ) -> RetrievalResponse:
        normalized_ids = sorted(document_ids or [])
        cache_key = (
            f"retrieval:{user.id}:{query}:{top_k}:{hybrid}:{','.join(normalized_ids)}:{filters}"
        )
        cached = app_cache.get(cache_key)
        if cached:
            return cached

        k = top_k or settings.RAG_TOP_K
        allowed_document_ids = (
            {uuid.UUID(item) for item in normalized_ids} if normalized_ids else set()
        )

        print(f"[RAG] document_ids received: {normalized_ids!r}")
        print(f"[RAG] user_id: {user.id!r}")
        print(f"[RAG] Running similarity search...")

        # Both hybrid and semantic now use the same async similarity_search
        results: list[VectorSearchResult]
        if hybrid:
            results = await self.vector_store.hybrid_similarity_search(
                user_id=user.id, query=query, top_k=k, document_ids=normalized_ids, filters=filters
            )
        else:
            results = await self.vector_store.semantic_similarity_search(
                user_id=user.id, query=query, top_k=k, document_ids=normalized_ids, filters=filters
            )

        print(f"[RAG] Results count: {len(results)}")
        if results:
            print(f"[RAG] First result preview: {str(results[0])[:200]}")
        else:
            print(f"[RAG] NO RESULTS FOUND")

        retrieved_chunks: list[RetrievedChunk] = []
        context_sections: list[str] = []
        chunk_lookup: dict[tuple[uuid.UUID, int], DocumentChunk] = {}

        raw_document_ids: list[uuid.UUID] = []
        for result in results:
            doc_id_str = result.metadata.get("document_id", "")
            if not doc_id_str:
                continue
            try:
                raw_document_id = uuid.UUID(doc_id_str)
            except ValueError:
                continue
            if allowed_document_ids and raw_document_id not in allowed_document_ids:
                continue
            raw_document_ids.append(raw_document_id)

        unique_document_ids = sorted(set(raw_document_ids), key=lambda item: str(item))
        documents = {
            document.id: document
            for document in self.document_repository.list_by_ids(user.id, unique_document_ids)
        }
        for chunk in self.chunk_repository.list_by_documents(unique_document_ids):
            chunk_lookup[(chunk.document_id, chunk.chunk_index)] = chunk

        for result in results:
            doc_id_str = result.metadata.get("document_id", "")
            if not doc_id_str:
                continue
            try:
                document_id = uuid.UUID(doc_id_str)
            except ValueError:
                continue
            if allowed_document_ids and document_id not in allowed_document_ids:
                continue
            db_document = documents.get(document_id)
            if not db_document:
                continue
            chunk_index = int(result.metadata.get("chunk_index", 0))
            chunk = chunk_lookup.get((document_id, chunk_index))
            if not chunk:
                continue

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=db_document.id,
                    document_title=db_document.title,
                    filename=db_document.file_name,
                    page=chunk.page_number,
                    paragraph_index=chunk.paragraph_index,
                    content=chunk.content,
                    score=float(result.combined_score),
                    semantic_score=float(result.semantic_score),
                    keyword_score=float(result.keyword_score),
                    chunk_index=chunk.chunk_index,
                    upload_timestamp=db_document.created_at.isoformat(),
                )
            )
            context_sections.append(
                f"[Source: {db_document.file_name}, Page {chunk.page_number or 1}, Paragraph {chunk.paragraph_index or 1}]\n{chunk.content}"
            )
            if len(retrieved_chunks) >= k:
                break

        response = RetrievalResponse(
            query=query,
            top_k=k,
            chunks=retrieved_chunks,
            context="\n\n".join(context_sections),
        )
        app_cache.set(cache_key, response, ttl_seconds=45)
        return response
