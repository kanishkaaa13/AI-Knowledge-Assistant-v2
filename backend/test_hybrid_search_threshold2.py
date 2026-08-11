"""
Test hybrid search distance threshold with low-relevance query
"""

import uuid
from app.db.session import get_db
from app.models.user import User
from app.services.rag_pipeline import RAGRetrievalService

with next(get_db()) as db:
    user = db.query(User).filter(
        User.id == uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")
    ).first()
    
    print("Hybrid Search Distance Threshold Test:")
    print("=" * 80)
    print()
    print(f"User: {user.email}")
    print(f"Query: 'data structures and algorithms' (somewhat related but low relevance)")
    print()
    
    retrieval_service = RAGRetrievalService(db)
    
    # Test with hybrid search
    print("Testing HYBRID search (with 1.4 distance threshold):")
    try:
        import asyncio
        results = asyncio.run(retrieval_service.retrieve(
            user=user,
            query="data structures and algorithms",
            top_k=10,
            hybrid=True
        ))
        
        print(f"  Results returned: {len(results.chunks)}")
        if results.chunks:
            for i, chunk in enumerate(results.chunks[:3], 1):
                print(f"    Result {i}:")
                print(f"      Score: {chunk.score:.4f}")
                print(f"      Semantic: {chunk.semantic_score:.4f}")
                print(f"      Keyword: {chunk.keyword_score:.4f}")
                print(f"      Page: {chunk.page}")
                print(f"      Preview: {chunk.content[:80]}...")
        else:
            print(f"  ✓ No results (threshold filtered out low-relevance matches)")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Test with semantic-only search
    print("Testing SEMANTIC-ONLY search (no distance threshold):")
    try:
        results = asyncio.run(retrieval_service.retrieve(
            user=user,
            query="data structures and algorithms",
            top_k=10,
            hybrid=False
        ))
        
        print(f"  Results returned: {len(results.chunks)}")
        if results.chunks:
            for i, chunk in enumerate(results.chunks[:3], 1):
                print(f"    Result {i}:")
                print(f"      Score: {chunk.score:.4f}")
                print(f"      Semantic: {chunk.semantic_score:.4f}")
                print(f"      Page: {chunk.page}")
                print(f"      Preview: {chunk.content[:80]}...")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    print("=" * 80)
