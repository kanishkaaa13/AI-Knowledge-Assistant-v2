"""
Test write path through actual API endpoint - with authentication
"""

import requests
import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.core.crypto import encryption_service

# API base URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Create a test PDF with multiple pages
test_pdf_content = b"%PDF-1.7\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R 5 0 R]\n/Count 2\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Page 1 Content) Tj\nET\nendstream\nendobj\n5 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 6 0 R\n>>\nendobj\n6 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test Page 2 Content) Tj\nET\nendstream\nendobj\nxref\n0 7\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000202 00000 n\n0000000275 00000 n\n0000000362 00000 n\ntrailer\n<<\n/Size 7\n/Root 1 0 R\n>>\nstartxref\n459\n%%EOF"

print("Testing Write Path Through Actual API Endpoint:")
print("=" * 80)
print()

# Step 1: Register a test user
print("Step 1: Register test user")
try:
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "name": "Test User",
            "email": "testapitest@example.com",
            "password": "TestPassword123!"
        },
        timeout=10
    )
    
    print(f"  Status Code: {register_response.status_code}")
    if register_response.status_code == 201:
        token = register_response.json().get("access_token")
        print(f"  ✓ Registered successfully")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print(f"  Response: {register_response.text}")
        # Try to login instead
        print("  Trying to login instead...")
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "testapitest@example.com",
                "password": "TestPassword123!"
            },
            timeout=10
        )
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print(f"  ✓ Login successful")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"  ✗ Login failed: {login_response.text}")
            headers = None
except Exception as e:
    print(f"  ✗ Error: {e}")
    headers = None

print()

# Step 2: Upload the PDF
if headers:
    print("Step 2: Upload PDF via /documents endpoint")
    files = {
        "file": ("test_api_upload.pdf", BytesIO(test_pdf_content), "application/pdf")
    }
    data = {
        "title": "API Test Document"
    }
    
    try:
        upload_response = requests.post(
            f"{BASE_URL}/documents",
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        print(f"  Status Code: {upload_response.status_code}")
        
        if upload_response.status_code == 201:
            result = upload_response.json()
            document_id = result.get("id")
            print(f"  ✓ Upload successful")
            print(f"  Document ID: {document_id}")
            print(f"  File path: {result.get('file_path')}")
            file_path = result.get('file_path')
        else:
            print(f"  ✗ Upload failed")
            print(f"  Response: {upload_response.text}")
            file_path = None
    except Exception as e:
        print(f"  ✗ Upload error: {e}")
        file_path = None
else:
    print("Step 2: Skipped (no auth)")
    file_path = None

print()

# Step 3: Check if file is encrypted
if file_path:
    print("Step 3: Read raw bytes from disk to confirm encryption")
    try:
        disk_path = Path(file_path)
        if disk_path.exists():
            raw_bytes = disk_path.read_bytes()
            print(f"  File size: {len(raw_bytes)} bytes")
            print(f"  First 50 bytes (hex): {raw_bytes[:50].hex()}")
            
            # Check if it's a valid PDF
            try:
                reader = PdfReader(BytesIO(raw_bytes))
                print(f"  ✗ File is valid PDF (NOT encrypted)")
            except Exception as pdf_err:
                print(f"  ✓ File is NOT valid PDF (encrypted)")
                print(f"  Error: {pdf_err}")
            
            # Try to decrypt
            try:
                decrypted = encryption_service.decrypt_bytes(raw_bytes)
                print(f"  ✓ Decryption successful")
                print(f"  Decrypted size: {len(decrypted)} bytes")
                
                # Verify it's a valid PDF after decryption
                reader = PdfReader(BytesIO(decrypted))
                print(f"  ✓ Decrypted file is valid PDF with {len(reader.pages)} pages")
            except Exception as decrypt_err:
                print(f"  ✗ Decryption failed: {decrypt_err}")
        else:
            print(f"  ✗ File not found on disk: {file_path}")
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
else:
    print("Step 3: Skipped (upload failed)")

print()
print("=" * 80)
