"""
Analyze similarity score distribution for sample queries.
"""

import asyncio
import uuid
from app.db.session import get_db
from app.services.vector_store import get_vector_store_service
from app.models.user import User

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

# Sample queries from eval set
queries = [
    "What is machine learning?",
    "What is agentic AI and how does it differ from traditional AI?",
    "What are the steps in risk management?",
    "What is the capital of Australia?",  # Out-of-scope query
]

print("=" * 80)
print("SIMILARITY SCORE DISTRIBUTION ANALYSIS")
print("=" * 80)
print()

vector_store = get_vector_store_service()

for query in queries:
    print(f"Query: {query}")
    print("-" * 80)
    
    try:
        results = asyncio.run(vector_store.similarity_search(
            user_id=user_id,
            query=query,
            top_k=10  # Get more results to see distribution
        ))
        
        print(f"Total results: {len(results)}")
        print()
        
        if results:
            print("Score distribution:")
            for i, result in enumerate(results[:10], 1):
                print(f"  [{i}] Score: {result.semantic_score:.4f}")
                print(f"      Distance: {result.distance:.4f}")
                print(f"      Document: {result.metadata.get('document_title', 'unknown')}")
                print(f"      Page: {result.metadata.get('page', 'unknown')}")
                print(f"      Content preview: {result.document[:100].replace(chr(10), ' ')}...")
                print()
        else:
            print("  No results returned")
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print()
