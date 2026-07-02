from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    id: str
    document: str
    metadata: dict


@dataclass
class VectorSearchResult:
    id: str
    document: str
    metadata: dict
    distance: float
    semantic_score: float
    # Derived fields (no BM25 yet — keyword score defaults to 0)
    keyword_score: float = field(default=0.0)

    @property
    def combined_score(self) -> float:
        """Weighted combination of semantic + keyword scores."""
        return 0.7 * self.semantic_score + 0.3 * self.keyword_score


class VectorStoreService:
    """
    Vector store service using ChromaDB and Sentence-Transformers for semantic search.

    Embedding model is loaded lazily — synchronously for sync callers, asynchronously
    for async callers — to avoid blocking the event loop on first use.
    """

    def __init__(
        self,
        persist_directory: str = "storage/chromadb",
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        persist_path = Path(persist_directory)
        persist_path.mkdir(parents=True, exist_ok=True)

        self.client: PersistentClient = chromadb.PersistentClient(path=str(persist_path))
        self.model_name = "default-onnx-embedding"
        self._embedding_function = DefaultEmbeddingFunction()

    # ------------------------------------------------------------------
    # Embedding model loading — sync and async variants
    # ------------------------------------------------------------------

    def _get_embedding_model_sync(self):
        """Pre-warm the embedding function."""
        logger.info("Loading chromadb default embedding function (sync)…")
        # Trigger model download/load by embedding a dummy string
        self._embedding_function(["warmup"])
        logger.info("Embedding function loaded.")
        return self._embedding_function

    async def _get_embedding_model_async(self):
        """Load (or return cached) embedding model without blocking the event loop."""
        logger.info("Loading chromadb default embedding function (async)…")
        await asyncio.to_thread(self._embedding_function, ["warmup"])
        logger.info("Embedding function loaded.")
        return self._embedding_function

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------

    def _collection_name(self, user_id: uuid.UUID) -> str:
        return f"user_collection_{user_id}"

    def _get_or_create_collection(self, user_id: uuid.UUID):
        return self.client.get_or_create_collection(
            name=self._collection_name(user_id),
            embedding_function=self._embedding_function
        )

    # ------------------------------------------------------------------
    # Write operations (synchronous — called from upload/ingestion paths)
    # ------------------------------------------------------------------

    def add_documents_to_vector_store(
        self,
        user_id: uuid.UUID,
        chunks_list: list[dict[str, Any]],
    ) -> None:
        """Vectorize text chunks and upsert into ChromaDB.

        This is a **synchronous** method.  Call it from a threadpool or from
        regular (non-async) ingestion code.  Do NOT ``await`` it.
        """
        if not chunks_list:
            print("[INDEX DEBUG] add_documents_to_vector_store called with EMPTY chunks_list — skipping")
            return

        print(f"[INDEX DEBUG] Loading embedding model: {self.model_name}")
        self._get_embedding_model_sync()
        print(f"[INDEX DEBUG] Embedding model loaded OK")

        collection = self._get_or_create_collection(user_id)
        count_before = collection.count()
        print(f"[INDEX DEBUG] Collection name used: {collection.name}")
        print(f"[INDEX DEBUG] Collection count BEFORE upsert: {count_before}")

        ids = [str(chunk.get("id", "")) for chunk in chunks_list]
        documents = [chunk.get("content", "") for chunk in chunks_list]

        metadatas: list[dict] = []
        for chunk in chunks_list:
            metadata = dict(chunk.get("metadata", {}))
            metadata["user_id"] = str(user_id)
            metadata.setdefault("document_id", chunk.get("document_id", ""))
            metadata.setdefault("filename", chunk.get("filename", ""))
            metadata.setdefault("chunk_index", chunk.get("chunk_index", 0))
            # Stringify any list/dict values — ChromaDB only supports scalar metadata
            for k, v in list(metadata.items()):
                if not isinstance(v, (str, int, float, bool)):
                    metadata[k] = str(v)
            metadatas.append(metadata)

        print(f"[INDEX DEBUG] Metadata stored on chunks: {metadatas[:1]}")
        print(f"[INDEX DEBUG] Total chunks to store: {len(ids)}")
        print(f"[INDEX DEBUG] Generating embeddings and upserting {len(documents)} chunks...")

        print(f"[INDEX] Collection: {collection.name}")
        if metadatas:
            print(f"[INDEX] Metadata on chunks: {metadatas[0]}")
        print(f"[INDEX] Upserting {len(ids)} vectors into ChromaDB")

        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as e:
            print(f"[INDEX DEBUG] CHROMA UPSERT FAILED: {e}")
            import traceback
            print(traceback.format_exc())
            raise

        count_after = collection.count()
        print(f"[INDEX] Upsert complete. Collection now has {count_after} total vectors.")
        if count_after == count_before:
            print(f"[INDEX DEBUG] WARNING: Count did not increase! Before={count_before}, After={count_after}")
            print(f"[INDEX DEBUG] This may mean the same IDs already existed and were updated (which is correct for re-index)")
        logger.info("Upserted %d vectors for user %s.", len(ids), user_id)

    def upsert_vectors(self, user_id: uuid.UUID, records: list[VectorRecord]) -> None:
        """Upsert pre-built VectorRecord objects into the user's collection."""
        if not records:
            return

        chunks_list = [
            {
                "id": r.id,
                "content": r.document,
                "metadata": r.metadata,
                "document_id": r.metadata.get("document_id", ""),
                "filename": r.metadata.get("filename", ""),
                "chunk_index": r.metadata.get("chunk_index", 0),
            }
            for r in records
        ]
        self.add_documents_to_vector_store(user_id, chunks_list)

    def delete_vectors(self, user_id: uuid.UUID, ids: list[str]) -> None:
        """Delete specific vectors by ID."""
        if not ids:
            return
        collection = self._get_or_create_collection(user_id)
        collection.delete(ids=ids)

    def delete_documents(
        self,
        user_id: uuid.UUID,
        document_ids: list[str] | None = None,
    ) -> None:
        """Delete all chunks belonging to the given document IDs."""
        if not document_ids:
            return
        collection = self._get_or_create_collection(user_id)
        collection.delete(where={"document_id": {"$in": document_ids}})

    def delete_collection(self, user_id: uuid.UUID) -> None:
        """Delete the entire user collection."""
        try:
            self.client.delete_collection(name=self._collection_name(user_id))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Read operations (async — called from API route handlers)
    # ------------------------------------------------------------------

    async def similarity_search(
        self,
        user_id: uuid.UUID,
        query: str,
        top_k: int = 4,
        document_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        """Semantic similarity search — async, non-blocking."""

        def _search_sync() -> list[VectorSearchResult]:
            collection = self._get_or_create_collection(user_id)

            # Verify the collection has data
            count = collection.count()
            print(f"[RAG] Query: {query!r}")
            print(f"[RAG] Selected doc IDs: {document_ids!r}")
            print(f"[RAG] ChromaDB collection '{self._collection_name(user_id)}' has {count} total vectors")

            if count == 0:
                print(f"[RAG] Collection is EMPTY — documents may not have been indexed yet")
                logger.debug("Collection for user %s is empty.", user_id)
                return []

            where_clause: dict = {"user_id": str(user_id)}
            if document_ids:
                if len(document_ids) == 1:
                    where_clause = {
                        "$and": [
                            {"user_id": str(user_id)},
                            {"document_id": document_ids[0]},
                        ]
                    }
                else:
                    where_clause = {
                        "$and": [
                            {"user_id": str(user_id)},
                            {"document_id": {"$in": document_ids}},
                        ]
                    }

            print(f"[QUERY] Filter used: {where_clause}")

            # Clamp n_results to the actual collection size
            n_results = min(top_k, count)

            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_clause,
                    include=["documents", "metadatas", "distances"],
                )
            except Exception as e:
                print(f"[RAG] ChromaDB query FAILED: {e}")
                # If filter caused error, try without filter as fallback
                try:
                    print(f"[RAG] Retrying without document_id filter...")
                    results = collection.query(
                        query_texts=[query],
                        n_results=n_results,
                        where={"user_id": str(user_id)},
                        include=["documents", "metadatas", "distances"],
                    )
                    print(f"[RAG] Fallback query returned {len(results.get('ids', [[]])[0])} results")
                except Exception as e2:
                    print(f"[RAG] Fallback query also FAILED: {e2}")
                    return []

            ids_list = results.get("ids", [[]])[0]
            docs_list = results.get("documents", [[]])[0]
            meta_list = results.get("metadatas", [[]])[0]
            dist_list = results.get("distances", [[]])[0]

            print(f"[RAG] ChromaDB returned {len(ids_list)} results")
            if meta_list:
                print(f"[RAG] First result metadata: {meta_list[0]}")

            formatted: list[VectorSearchResult] = []
            for vid, doc, meta, dist in zip(ids_list, docs_list, meta_list, dist_list):
                semantic_score = max(0.0, 1.0 - float(dist or 0.0))
                formatted.append(
                    VectorSearchResult(
                        id=vid,
                        document=doc,
                        metadata=meta or {},
                        distance=float(dist or 0.0),
                        semantic_score=semantic_score,
                    )
                )
            return formatted

        try:
            await self._get_embedding_model_async()
            return await asyncio.to_thread(_search_sync)
        except Exception as e:
            logger.error("Similarity search failed: %s", e)
            print(f"[RAG] CRITICAL ERROR IN SIMILARITY SEARCH: {e}")
            import traceback
            print(traceback.format_exc())
            return []

    # Performs a hybrid semantic + keyword search with Reciprocal Rank Fusion (RRF)
    async def hybrid_similarity_search(
        self,
        user_id: uuid.UUID,
        query: str,
        top_k: int = 4,
        document_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        """Hybrid search combining semantic search and keyword search using Reciprocal Rank Fusion (RRF)."""
        import re
        from sqlalchemy import select, or_
        from app.db.session import db_manager
        from app.models.document_chunk import DocumentChunk
        from app.models.uploaded_document import UploadedDocument

        # Tokenize query to terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "is", "are", "was", "were", "be", "been", "this", "that", "it", "he", "she", "they", "we", "you"}
        words = [re.sub(r'[^a-zA-Z0-9]', '', w).lower() for w in query.split()]
        terms = [w for w in words if w and w not in stop_words]
        if not terms and words:
            terms = [w for w in words if w]

        sql_results = []
        if terms:
            try:
                with db_manager.session_factory() as session:
                    conditions = []
                    for term in terms:
                        conditions.append(DocumentChunk.content.ilike(f"%{term}%"))

                    stmt = select(DocumentChunk).join(UploadedDocument).where(
                        UploadedDocument.user_id == user_id
                    )

                    if document_ids:
                        stmt = stmt.where(UploadedDocument.id.in_([uuid.UUID(d) for d in document_ids if d]))

                    stmt = stmt.where(or_(*conditions)).limit(50)
                    db_chunks = session.scalars(stmt).all()

                    for chunk in db_chunks:
                        matches = 0
                        content_lower = chunk.content.lower()
                        for term in terms:
                            matches += content_lower.count(term)

                        sql_results.append({
                            "chunk_id": str(chunk.id),
                            "document_id": str(chunk.document_id),
                            "filename": chunk.document.file_name,
                            "title": chunk.document.title,
                            "page": chunk.page_number,
                            "paragraph_index": chunk.paragraph_index,
                            "content": chunk.content,
                            "chunk_index": chunk.chunk_index,
                            "score": matches
                        })
                    sql_results.sort(key=lambda x: x["score"], reverse=True)
            except Exception as e:
                logger.error("SQL keyword search failed in hybrid search: %s", e)

        # Get semantic results
        semantic_results = await self.similarity_search(user_id, query, top_k=top_k * 3, document_ids=document_ids)

        # Apply Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        chunk_data_map = {}

        for rank, res in enumerate(semantic_results, start=1):
            doc_id = str(res.metadata.get("document_id", ""))
            chunk_idx = int(res.metadata.get("chunk_index", 0))
            key = (doc_id, chunk_idx)

            chunk_data_map[key] = {
                "id": res.id,
                "document": res.document,
                "metadata": res.metadata,
                "semantic_score": res.semantic_score,
                "keyword_score": 0.0
            }
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (60.0 + rank))

        for rank, res in enumerate(sql_results, start=1):
            doc_id = res["document_id"]
            chunk_idx = res["chunk_index"]
            key = (doc_id, chunk_idx)

            if key not in chunk_data_map:
                chunk_data_map[key] = {
                    "id": res["chunk_id"],
                    "document": res["content"],
                    "metadata": {
                        "document_id": doc_id,
                        "filename": res["filename"],
                        "document_title": res["title"],
                        "page": res["page"],
                        "paragraph_index": res["paragraph_index"],
                        "chunk_index": chunk_idx
                    },
                    "semantic_score": 0.0,
                    "keyword_score": float(res["score"])
                }
            else:
                chunk_data_map[key]["keyword_score"] = float(res["score"])
                if "paragraph_index" not in chunk_data_map[key]["metadata"] and res.get("paragraph_index") is not None:
                    chunk_data_map[key]["metadata"]["paragraph_index"] = res["paragraph_index"]

            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (60.0 + rank))

        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        final_results = []
        seen_texts = set()
        for key in sorted_keys:
            data = chunk_data_map[key]
            text_norm = data["document"].strip().lower()
            if text_norm in seen_texts:
                continue
            seen_texts.add(text_norm)

            # Normalize keyword score to a reasonable range
            k_score = min(data["keyword_score"], 10.0) / 10.0
            final_results.append(
                VectorSearchResult(
                    id=data["id"],
                    document=data["document"],
                    metadata=data["metadata"],
                    distance=0.0,
                    semantic_score=data["semantic_score"],
                    keyword_score=k_score
                )
            )
            if len(final_results) >= top_k:
                break
        return final_results

    async def semantic_similarity_search(
        self,
        user_id: uuid.UUID,
        query: str,
        top_k: int = 4,
        document_ids: list[str] | None = None,
    ) -> list[VectorSearchResult]:
        """Pure semantic search alias."""
        return await self.similarity_search(user_id, query, top_k, document_ids)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_vector_store_service: VectorStoreService | None = None


def get_vector_store_service() -> VectorStoreService:
    """Return the application-wide singleton VectorStoreService."""
    global _vector_store_service
    if _vector_store_service is None:
        from app.core.config import settings
        _vector_store_service = VectorStoreService(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            model_name=settings.EMBEDDING_MODEL_NAME,
        )
    return _vector_store_service
