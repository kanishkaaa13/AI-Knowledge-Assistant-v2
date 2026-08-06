"""
Upload a test document for the test user.
"""
import requests
import os

BASE_URL = "http://localhost:8000"

def upload_test_document():
    """Upload test document for concurrent1@example.com user."""
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
    
    print("Login successful")
    
    # Upload document
    upload_url = f"{BASE_URL}/api/v1/documents/upload"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    doc_path = "test_document.txt"
    if not os.path.exists(doc_path):
        print(f"Error: {doc_path} not found")
        return
    
    with open(doc_path, 'rb') as f:
        files = {'file': (doc_path, f, 'text/plain')}
        data = {'title': 'Introduction to Machine Learning'}
        
        print(f"Uploading {doc_path}...")
        response = requests.post(upload_url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Upload successful!")
            print(f"Document ID: {result.get('id')}")
            print(f"Title: {result.get('title')}")
            print(f"Preview: {result.get('preview_text', '')[:100]}...")
        else:
            print(f"Upload failed: {response.text}")

if __name__ == "__main__":
    upload_test_document()
