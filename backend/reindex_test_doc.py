"""
Reindex the test document to ensure it's available in the vector store.
"""
import requests

BASE_URL = "http://localhost:8000"

def reindex_document():
    """Reindex the test document."""
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
    
    # List documents to get the document ID
    docs_url = f"{BASE_URL}/api/v1/documents"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(docs_url, headers=headers)
    if response.status_code == 200:
        docs_data = response.json()
        if docs_data.get('items'):
            doc_id = docs_data['items'][0]['id']
            print(f"Found document ID: {doc_id}")
            
            # Reindex the document
            reindex_url = f"{BASE_URL}/api/v1/documents/{doc_id}/reindex"
            response = requests.post(reindex_url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Reindex successful!")
                print(f"Document status: {result.get('status')}")
            else:
                print(f"Reindex failed: {response.text}")
        else:
            print("No documents found")
    else:
        print(f"Failed to list documents: {response.text}")

if __name__ == "__main__":
    reindex_document()
