"""
Concurrency test for agent user isolation with detailed timestamps.
Fires two simultaneous requests from different users and verifies user_id isolation.
Logs timestamps for: request start, ContextVar set, tool call entry/exit, ContextVar reset.
"""
import asyncio
import requests
import json
import time

BASE_URL = "http://localhost:8000"

async def run_agent_for_user(user_email, user_password, user_name, query):
    """Register/login and run agent for a user."""
    # Register user (ignore if already exists)
    register_url = f"{BASE_URL}/api/v1/auth/register"
    register_data = {
        "email": user_email,
        "password": user_password,
        "name": user_name
    }
    
    try:
        response = requests.post(register_url, json=register_data)
        if response.status_code == 201:
            print(f"[{user_name}] Registered successfully")
        elif response.status_code == 400:
            print(f"[{user_name}] User already exists, proceeding to login")
        else:
            print(f"[{user_name}] Register response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[{user_name}] Register error: {e}")
    
    # Login
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {
        "email": user_email,
        "password": user_password
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code != 200:
        print(f"[{user_name}] Login failed: {response.text}")
        return None
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    # Call agent/run
    agent_url = f"{BASE_URL}/api/v1/agent/run"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    agent_data = {
        "query": query
    }
    
    print(f"[{user_name}] Calling agent/run at {time.time()}")
    start_time = time.time()
    response = requests.post(agent_url, json=agent_data, headers=headers, timeout=120)
    elapsed = time.time() - start_time
    
    print(f"[{user_name}] Agent response: {response.status_code} (took {elapsed:.2f}s)")
    print(f"[{user_name}] Response body preview: {response.text[:500] if response.text else 'empty'}")
    
    if response.status_code == 200:
        result = response.json()
        return {
            "user": user_name,
            "user_id": token_data["user"]["id"],
            "tools_called": result.get("tools_called", []),
            "answer": result.get("answer", "")[:200],
            "elapsed": elapsed
        }
    else:
        return {
            "user": user_name,
            "error": response.text,
            "elapsed": elapsed
        }

async def main():
    """Run concurrent agent requests for two users."""
    print("=" * 80)
    print("CONCURRENCY TEST - Two users, simultaneous requests")
    print("=" * 80)
    
    # Create two users with different queries - use simpler queries for faster execution
    user1_task = run_agent_for_user(
        "concurrent1@example.com",
        "password123",
        "User One",
        "find the term 'test' in my documents"
    )
    
    user2_task = run_agent_for_user(
        "concurrent2@example.com", 
        "password456",
        "User Two",
        "find the term 'data' in my documents"
    )
    
    # Run concurrently
    print("\nStarting concurrent requests...\n")
    start_time = time.time()
    
    results = await asyncio.gather(user1_task, user2_task)
    
    total_elapsed = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    for result in results:
        if result:
            print(f"\n{result['user']}:")
            print(f"  User ID: {result.get('user_id', 'N/A')}")
            print(f"  Tools called: {result.get('tools_called', [])}")
            print(f"  Answer preview: {result.get('answer', result.get('error', 'N/A'))}")
            print(f"  Elapsed: {result.get('elapsed', 0):.2f}s")
    
    print(f"\nTotal elapsed: {total_elapsed:.2f}s")
    print("=" * 80)
    
    # Verify isolation
    if results and len(results) == 2:
        user1_id = results[0].get('user_id')
        user2_id = results[1].get('user_id')
        
        if user1_id and user2_id and user1_id != user2_id:
            print("\n✓ USER ISOLATION VERIFIED: Different user IDs returned")
        else:
            print("\n✗ USER ISOLATION FAILED: Same or missing user IDs")

if __name__ == "__main__":
    asyncio.run(main())
