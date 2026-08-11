"""
Test hybrid search distance threshold behavior with tangential query
"""

import uuid
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.models.user import User
from app.services.rag_pipeline import RAGRetrievalService

with next(get_db()) as db:
    # Get a user with documents
    user = db.query(User).filter(
        User.id == uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")
    ).first()
    
    print("Hybrid Search Distance Threshold Test:")
    print("=" * 80)
    print()
    print(f"User: {user.email}")
    print(f"Query: 'cooking recipes' (tangential to machine learning content)")
    print()
    
    retrieval_service = RAGRetrievalService(db)
    
    # Test with hybrid search (should use 1.4 threshold)
    print("Testing HYBRID search (with 1.4 distance threshold):")
    try:
        import asyncio
        results = asyncio.run(retrieval_service.retrieve(
            user=user,
            query="cooking recipes and baking techniques",
            top_k=10,
            hybrid=True
        ))
        
        print(f"  Results returned: {len(results.chunks)}")
        if results.chunks:
            print(f"  Top result score: {results.chunks[0].score:.4f}")
            print(f"  Top result semantic score: {results.chunks[0].semantic_score:.4f}")
            print(f"  Top result keyword score: {results.chunks[0].keyword_score:.4f}")
            print(f"  Top result preview: {results.chunks[0].content[:100]}...")
        else:
            print(f"  ✓ No results returned (threshold working correctly)")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Test with semantic-only search (no threshold)
    print("Testing SEMANTIC-ONLY search (no distance threshold):")
    try:
        results = asyncio.run(retrieval_service.retrieve(
            user=user,
            query="cooking recipes and baking techniques",
            top_k=10,
            hybrid=False
        ))
        
        print(f"  Results returned: {len(results.chunks)}")
        if results.chunks:
            print(f"  Top result score: {results.chunks[0].score:.4f}")
            print(f"  Top result semantic score: {results.chunks[0].semantic_score:.4f}")
            print(f"  Top result preview: {results.chunks[0].content[:100]}...")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    print("=" * 80)
    print("VERIFICATION:")
    print("  If hybrid returns fewer/no results compared to semantic-only,")
    print("  the 1.4 distance threshold is working correctly.")
    print("=" * 80)
