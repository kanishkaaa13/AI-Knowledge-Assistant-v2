"""
Demonstrate the literal HTTP response for decryption failure
by creating a file with invalid encryption
"""

import uuid
from pathlib import Path
from app.db.session import get_db
from app.models.uploaded_document import UploadedDocument
from app.services.document_parser import StoredDocumentParser
from fastapi import HTTPException
from app.core.crypto import encryption_service

print("Testing decryption failure HTTP response:")
print("=" * 80)
print()

# Create a file with invalid (non-encrypted) data to simulate decryption failure
test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
test_dir = Path("C:\\Users\\Kanishka\\Desktop\\AI-Knowledge Assistant\\backend\\storage\\uploads\\00000000-0000-0000-0000-000000000001")
test_dir.mkdir(parents=True, exist_ok=True)

test_file = test_dir / "test_corrupted.pdf"
test_file.write_bytes(b"This is not encrypted data - it should fail decryption")

print("Created test file with invalid encryption")
print(f"File path: {test_file}")
print()

# Create a mock document pointing to this file
class MockDocument:
    def __init__(self):
        self.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        self.file_name = "corrupted.pdf"
        self.file_extension = ".pdf"
        self.file_path = str(test_file)
        self.extracted_text = "Some text"

mock_doc = MockDocument()

print("Attempting to parse a document with corrupted encryption...")
print()

try:
    parser = StoredDocumentParser()
    pages = parser.parse(mock_doc)
    print(f"✗ Unexpected success: parsed {len(pages)} pages")
except HTTPException as e:
    print("HTTPException raised:")
    print(f"  Status Code: {e.status_code}")
    print(f"  Detail: {e.detail}")
    print()
    print("Literal HTTP Response:")
    print("-" * 40)
    print(f"HTTP/1.1 {e.status_code} Unprocessable Entity")
    print("Content-Type: application/json")
    print()
    print("{")
    print(f'  "detail": "{e.detail}"')
    print("}")
    print("-" * 40)
except Exception as e:
    print(f"Other exception: {type(e).__name__}: {e}")

# Cleanup
if test_file.exists():
    test_file.unlink()
    print()
    print("Test file cleaned up")

print()
print("=" * 80)
print("NOTE: This is the exact response a user would see if:")
print("  1. A file was uploaded but encryption failed during write")
print("  2. The file was corrupted on disk")
print("  3. The encryption key changed between write and read")
print("=" * 80)
