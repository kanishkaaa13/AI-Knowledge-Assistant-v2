"""
Validate 1.4 distance threshold with more queries.
"""

import asyncio
import uuid
from app.services.vector_store import get_vector_store_service

user_id = uuid.UUID("2f9c2a2c-2dac-4596-b117-6b2cffe01425")

# Extended query set for validation
queries = [
    # Relevant queries (should have distances < 1.4)
    "What is machine learning?",
    "What is agentic AI and how does it differ from traditional AI?",
    "What are the steps in risk management?",
    "What is project management?",
    "What are the types of machine learning?",
    "What is LangGraph?",
    "What is the ReAct pattern?",
    
    # Irrelevant queries (should have distances > 1.4)
    "What is the capital of Australia?",
    "Who won the World Cup in 2022?",
    "What is the population of Tokyo?",
    "How do I bake a chocolate cake?",
    "What are the best restaurants in Paris?",
    "How does photosynthesis work?",
    "What is the stock price of Apple?",
]

print("=" * 80)
print("DISTANCE THRESHOLD VALIDATION")
print("=" * 80)
print()

vector_store = get_vector_store_service()

relevant_distances = []
irrelevant_distances = []

for query in queries:
    try:
        results = asyncio.run(vector_store.similarity_search(
            user_id=user_id,
            query=query,
            top_k=5
        ))
        
        if results:
            # Get the distance of the top result
            top_distance = results[0].distance
            
            if "capital" in query.lower() or "world cup" in query.lower() or "population" in query.lower() or "bake" in query.lower() or "restaurants" in query.lower() or "photosynthesis" in query.lower() or "stock price" in query.lower():
                irrelevant_distances.append((query, top_distance))
                category = "IRRELEVANT"
            else:
                relevant_distances.append((query, top_distance))
                category = "RELEVANT"
            
            print(f"[{category}] {query}")
            print(f"  Top distance: {top_distance:.4f}")
            print()
    except Exception as e:
        print(f"Error for '{query}': {e}")

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print("RELEVANT QUERIES (should be < 1.4):")
for query, dist in relevant_distances:
    status = "✓" if dist < 1.4 else "✗"
    print(f"  {status} {query}: {dist:.4f}")

print()
print("IRRELEVANT QUERIES (should be > 1.4):")
for query, dist in irrelevant_distances:
    status = "✓" if dist > 1.4 else "✗"
    print(f"  {status} {query}: {dist:.4f}")

print()
print("Statistics:")
print(f"  Relevant queries: {len(relevant_distances)}")
print(f"  Irrelevant queries: {len(irrelevant_distances)}")
print(f"  Relevant avg distance: {sum(d for _, d in relevant_distances)/len(relevant_distances):.4f}" if relevant_distances else "  Relevant avg distance: N/A")
print(f"  Irrelevant avg distance: {sum(d for _, d in irrelevant_distances)/len(irrelevant_distances):.4f}" if irrelevant_distances else "  Irrelevant avg distance: N/A")
print(f"  Threshold 1.4 separation: {'GOOD' if (relevant_distances and irrelevant_distances and max(d for _, d in relevant_distances) < 1.4 < min(d for _, d in irrelevant_distances)) else 'NEEDS ADJUSTMENT'}")
