"""
Check actual distances for the test queries to understand threshold behavior.
"""

import asyncio
import uuid
from app.services.vector_store import get_vector_store_service

user_id = uuid.UUID("b33330fc-1239-460b-b3c8-36775950c677")

queries = [
    "What is machine learning?",
    "What is agentic AI and how does it differ from traditional AI?",
    "What is the capital of Australia?",
    "What are the steps in risk management?",
    "What is project management?",
]

print("=" * 80)
print("DISTANCE CHECK FOR THRESHOLD VALIDATION")
print("=" * 80)
print()

vector_store = get_vector_store_service()

for query in queries:
    try:
        results = asyncio.run(vector_store.similarity_search(
            user_id=user_id,
            query=query,
            top_k=10
        ))
        
        print(f"Query: {query}")
        print(f"  Results: {len(results)}")
        if results:
            for i, res in enumerate(results[:5], 1):
                print(f"    {i}. Distance: {res.distance:.4f}, Content: {res.document[:50]}...")
        print()
    except Exception as e:
        print(f"Error for '{query}': {e}")
        print()
