"""
Multi-tool test via HTTP endpoint.
Tests ContextVar visibility across multiple tool calls in a single request.
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_multi_tool_http():
    """Test multi-tool ContextVar visibility via HTTP endpoint."""
    # Login as user
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "email": "concurrent1@example.com",
        "password": "password123"
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    user_id = token_data["user"]["id"]
    
    print("=" * 80)
    print("MULTI-TOOL HTTP TEST")
    print("=" * 80)
    print(f"User ID: {user_id}")
    
    # Query that should force multiple tool calls
    # Try to force the agent to search and then do something with results
    test_query = "search for 'test' in my documents, then summarize what you find"
    
    print(f"Query: {test_query}")
    print("=" * 80)
    
    agent_url = f"{BASE_URL}/api/v1/agent/run"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    agent_data = {
        "query": test_query
    }
    
    print(f"Calling agent/run at {time.time()}")
    start_time = time.time()
    response = requests.post(agent_url, json=agent_data, headers=headers, timeout=120)
    elapsed = time.time() - start_time
    
    print(f"Agent response: {response.status_code} (took {elapsed:.2f}s)")
    
    if response.status_code == 200:
        result = response.json()
        tools_called = result.get("tools_called", [])
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Tools called: {tools_called}")
        print(f"Number of tool calls: {len(tools_called)}")
        print(f"Answer: {result.get('answer', '')[:500]}...")
        print("=" * 80)
        
        if len(tools_called) > 1:
            print("\n✓ Multiple tools called in single request")
            print("✓ Check server logs (multi_tool_test.log) for ContextVar user_id in each tool")
        else:
            print(f"\n⚠ Only {len(tools_called)} tool(s) called - agent chose not to use multiple tools")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_multi_tool_http()
