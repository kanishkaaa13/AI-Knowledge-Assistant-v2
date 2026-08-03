from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Tuple

from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.db.session import db_manager
from app.models.document_chunk import DocumentChunk
from app.models.uploaded_document import UploadedDocument

logger = logging.getLogger(__name__)


class BM25IndexService:
    """BM25 keyword search index service per user."""
    
    def __init__(self):
        # Cache BM25 indexes per user: {user_id: (bm25_index, chunk_ids, chunk_texts)}
        self._indexes: Dict[uuid.UUID, Tuple[BM25Okapi, List[str], List[str]]] = {}
    
    def build_index_for_user(self, user_id: uuid.UUID) -> None:
        """Build BM25 index from all chunks for a user."""
        with db_manager.session_factory() as db:
            # Get all documents for user
            documents = db.query(UploadedDocument).filter(
                UploadedDocument.user_id == user_id
            ).all()
            
            if not documents:
                logger.info(f"No documents found forユーザー {user_id}")
                return
            
            # Get all chunks for these documents
            document_ids = [str(doc.id) for doc in documents]
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id.in_(document_ids)
            ).order_by(DocumentChunk.chunk_index).all()
            
            if not chunks:
                logger.info(f"No chunks found for user {user_id}")
                return
            
            # Prepare corpus: tokenize chunk texts
            chunk_texts = []
            chunk_ids = []
            
            for chunk in chunks:
                chunk_texts.append(self._tokenize(chunk.content))
                chunk_ids.append(chunk.vector_id or f"{chunk.document_id}:{chunk.chunk_index}")
            
            # Build BM25 index
            bm25_index = BM25Okapi(chunk_texts)
            
            # Cache the index
            self._indexes[user_id] = (bm25_index, chunk_ids, chunk_texts)
            
            logger.info(f"Built BM25 index for user {user_id} with {len(chunk_ids)} chunks")
    
    def search(
        self,
        user_id: uuid.UUID,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search BM25 index for query.
        
        Returns:
            List of (chunk_id, score) tuples, sorted by score descending
        """
        if user_id not in self._indexes:
            self.build_index_for_user(user_id)
            
        if user_id not in self._indexes:
            logger.warning(f"Could not build BM25 index for user {user_id}")
            return []
        
        bm25_index, chunk_ids, _ = self._indexes[user_id]
        
        # Tokenize query
        tokenized_query = self._tokenize(query)
        
        # Get BM25 scores
        scores = bm25_index.get_scores(tokenized_query)
        
        # Sort by score descending and get top_k
        scored_results = list(zip(chunk_ids, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return scored_results[:top_k]
    
    def invalidate_user(self, user_id: uuid.UUID) -> None:
        """Invalidate BM25 index for a user (call after document changes)."""
        if user_id in self._indexes:
            del self._indexes[user_id]
            logger.info(f"Invalidated BM25 index for user {user_id}")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on whitespace/punctuation
        import re
        tokens = re.findall(r'\w+', text.lower())
        return tokens


# Singleton instance
_bm25_service: BM25IndexService | None = None


def get_bm25_service() -> BM25IndexService:
    """Return the application-wide singleton BM25IndexService."""
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25IndexService()
    return _bm25_service
