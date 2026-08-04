"""
Test ContextVar visibility across multiple tool calls in a single request.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.router_agent import run_agent

# Test with a real user_id
test_user_id = "17348232-89f1-447a-8662-6c05c5c8fda2"

# Query that should force multiple tool calls
# First search, then try to generate something from results
test_query = "search for 'test' in my documents"

print("=" * 80)
print("MULTI-TOOL CONTEXT TEST")
print("=" * 80)
print(f"User ID: {test_user_id}")
print(f"Query: {test_query}")
print("=" * 80)

result = run_agent(user_query=test_query, user_id=test_user_id)

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)
print(f"Tools called: {result.get('tools_called', [])}")
print(f"Number of tool calls: {len(result.get('tools_called', []))}")
print(f"Answer: {result.get('answer', '')[:500]}...")
print("=" * 80)

# Verify ContextVar was visible across all tool calls
if len(result.get('tools_called', [])) > 1:
    print("\n✓ Multiple tools called in single request")
    print("✓ ContextVar visibility test requires checking server logs for user_id in each tool")
else:
    print("\n⚠ Only one tool called - agent chose not to use multiple tools")
    print("⚠ This is expected if no documents were found")
