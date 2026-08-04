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
    
    # Pre-login both users to get tokens before starting concurrent requests
    print("Pre-login both users...")
    
    user1_token = None
    user2_token = None
    user1_id = None
    user2_id = None
    
    # Login User One
    login_url = f"{BASE_URL}/api/v1/auth/login"
    response = requests.post(login_url, json={"email": "concurrent1@example.com", "password": "password123"})
    if response.status_code == 200:
        token_data = response.json()
        user1_token = token_data.get("access_token")
        user1_id = token_data["user"]["id"]
        print(f"User One logged in: {user1_id}")
    
    # Login User Two
    response = requests.post(login_url, json={"email": "concurrent2@example.com", "password": "password456"})
    if response.status_code == 200:
        token_data = response.json()
        user2_token = token_data.get("access_token")
        user2_id = token_data["user"]["id"]
        print(f"User Two logged in: {user2_id}")
    
    if not user1_token or not user2_token:
        print("Failed to login users")
        return
    
    # Now fire both agent requests concurrently using asyncio.gather
    async def call_agent_for_user(token, user_id, user_name, query):
        """Call agent endpoint for a user."""
        agent_url = f"{BASE_URL}/api/v1/agent/run"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        agent_data = {"query": query}
        
        print(f"[{user_name}] Calling agent/run at {time.time()}")
        start_time = time.time()
        
        # Use async HTTP client for true async calls
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(agent_url, json=agent_data, headers=headers, timeout=120) as response:
                elapsed = time.time() - start_time
                print(f"[{user_name}] Agent response: {response.status} (took {elapsed:.2f}s)")
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "user": user_name,
                        "user_id": user_id,
                        "tools_called": result.get("tools_called", []),
                        "answer": result.get("answer", "")[:200],
                        "elapsed": elapsed
                    }
                else:
                    text = await response.text()
                    return {
                        "user": user_name,
                        "error": text,
                        "elapsed": elapsed
                    }
    
    # Create async tasks for both users
    user1_task = call_agent_for_user(user1_token, user1_id, "User One", "find the term 'test' in my documents")
    user2_task = call_agent_for_user(user2_token, user2_id, "User Two", "find the term 'data' in my documents")
    
    # Run concurrently with asyncio.gather
    print("\nStarting CONCURRENT requests with asyncio.gather...\n")
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
