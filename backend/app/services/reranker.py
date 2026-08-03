from __future__ import annotations

import logging
from sentence_transformers import CrossEncoder
from typing import List

from app.services.vector_store import VectorSearchResult

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Cross-encoder reranker for improving retrieval relevance."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)
        logger.info(f"Loaded cross-encoder reranker: {model_name}")
    
    def rerank(
        self, 
        query: str, 
        results: List[VectorSearchResult], 
        top_k: int = 4
    ) -> List[VectorSearchResult]:
        """Rerank results using cross-encoder, return top_k.
        
        Args:
            query: The search query
            results: List of VectorSearchResult from initial retrieval
            top_k: Number of results to return after reranking
            
        Returns:
            Reranked list of VectorSearchResult with rerank_score field set
        """
        if not results:
            return results
        
        # Log pre-rerank order
        logger.info(f"[RERANK] Pre-rerank: {[(r.id, r.semantic_score) for r in results]}")
        
        # Prepare pairs for cross-encoder
        pairs = [[query, result.document] for result in results]
        
        # Compute cross-encoder scores
        scores = self.model.predict(pairs)
        
        # Attach rerank scores to results
        for i, result in enumerate(results):
            result.rerank_score = float(scores[i])
        
        # Sort by rerank score (descending)
        reranked = sorted(results, key=lambda x: x.rerank_score, reverse=True)
        
        # Log post-rerank order
        logger.info(f"[RERANK] Post-rerank: {[(r.id, r.rerank_score) for r in reranked[:top_k]]}")
        
        return reranked[:top_k]


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_reranker_service: CrossEncoderReranker | None = None


def get_reranker_service() -> CrossEncoderReranker:
    """Return the application-wide singleton CrossEncoderReranker."""
    global _reranker_service
    if _reranker_service is None:
        _reranker_service = CrossEncoderReranker()
    return _reranker_service
