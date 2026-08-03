"""
Test script to call /agent/run endpoint with authentication.
"""
import requests
import json

# Register a new test user
register_url = "http://localhost:8000/api/v1/auth/register"
register_data = {
    "email": "agenttest@example.com",
    "password": "agentpass123",
    "name": "Agent Test User"
}

print("Registering test user...")
response = requests.post(register_url, json=register_data)
print(f"Register response: {response.status_code}")
print(f"Register body: {response.text}")

# Login to get token
login_url = "http://localhost:8000/api/v1/auth/login"
login_data = {
    "email": "agenttest@example.com",
    "password": "agentpass123"
}

print("\nLogging in...")
response = requests.post(login_url, json=login_data)
print(f"Login response: {response.status_code}")
print(f"Login body: {response.text}")

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    # Call agent/run endpoint
    agent_url = "http://localhost:8000/api/v1/agent/run"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    agent_data = {
        "query": "find the exact term 'test' in my documents"
    }
    
    print(f"\nCalling agent/run with query: {agent_data['query']}")
    response = requests.post(agent_url, json=agent_data, headers=headers)
    print(f"Agent response: {response.status_code}")
    print(f"Agent body: {json.dumps(response.json(), indent=2)}")
else:
    print("Login failed")
