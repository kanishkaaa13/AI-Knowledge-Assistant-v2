"""
Test ReAct agent looping with a specific search term that the LLM can understand.
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_react_with_specific_query():
    """Test ReAct looping with a specific search term."""
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
    print("REACT LOOPING TEST WITH SPECIFIC QUERY")
    print("=" * 80)
    print(f"User ID: {user_id}")
    
    # Use a specific search term that the LLM can extract
    test_query = "search for 'machine learning' in my documents, then summarize the first result"
    
    print(f"\nQuery: {test_query}")
    print("=" * 80)
    
    agent_url = f"{BASE_URL}/api/v1/agent/run"
    agent_data = {
        "query": test_query
    }
    
    print(f"Calling agent/run at {time.time()}")
    start_time = time.time()
    response = requests.post(agent_url, json=agent_data, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}, timeout=120)
    elapsed = time.time() - start_time
    
    print(f"Agent response: {response.status_code} (took {elapsed:.2f}s)")
    
    if response.status_code == 200:
        result = response.json()
        tools_called = result.get("tools_called", [])
        reasoning_steps = result.get("reasoning_steps", [])
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Tools called: {tools_called}")
        print(f"Number of tool calls: {len(tools_called)}")
        print(f"Number of reasoning steps: {len(reasoning_steps)}")
        print(f"Answer: {result.get('answer', '')[:500]}...")
        
        print("\n" + "=" * 80)
        print("REASONING STEPS (FULL)")
        print("=" * 80)
        for i, step in enumerate(reasoning_steps):
            print(f"\nStep {i+1}: {step['type']}")
            if step['type'] == 'reasoning':
                print(f"  AI Reasoning: {step['content'][:300]}...")
            elif step['type'] == 'tool_call':
                print(f"  Tool: {step['tool']}")
                print(f"  Args: {step['args']}")
            elif step['type'] == 'tool_output':
                print(f"  Tool: {step['tool']}")
                print(f"  Output: {step['output'][:300]}...")
        
        print("=" * 80)
        
        if len(tools_called) > 1:
            print("\n✓ Multiple tools called in single request - ReAct looping confirmed")
        else:
            print(f"\n⚠ Only {len(tools_called)} tool(s) called")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_react_with_specific_query()
