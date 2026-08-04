"""
Direct test of agent function to see print output.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.router_agent import run_agent

# Test with a real user_id
test_user_id = "17348232-89f1-447a-8662-6c05c5c8fda2"
test_query = "find the exact term 'test' in my documents"

print("=" * 80)
print("DIRECT AGENT TEST")
print("=" * 80)
print(f"User ID: {test_user_id}")
print(f"Query: {test_query}")
print("=" * 80)

result = run_agent(user_query=test_query, user_id=test_user_id)

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)
print(f"Tools called: {result.get('tools_called', [])}")
print(f"Answer: {result.get('answer', '')[:500]}...")
print("=" * 80)
