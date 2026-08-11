"""
Test that DocumentProcessor.save_file() now encrypts bytes before writing
"""

import uuid
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
from app.services.document_processor import DocumentProcessor
from app.core.crypto import encryption_service

# Create a test PDF content (minimal valid PDF header)
test_pdf_content = b"%PDF-1.7\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000202 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n299\n%%EOF"

test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
test_filename = "test_encryption.pdf"

print("Testing DocumentProcessor.save_file() encryption:")
print(f"Test file size: {len(test_pdf_content)} bytes")
print(f"Test user ID: {test_user_id}")
print()

processor = DocumentProcessor()

# Save the file using DocumentProcessor
print("1. Saving file via DocumentProcessor.save_file()...")
file_path, checksum = processor.save_file(test_pdf_content, test_user_id, test_filename)
print(f"   File saved to: {file_path}")
print(f"   Checksum: {checksum}")
print()

# Read raw bytes from disk
print("2. Reading raw bytes from disk...")
disk_path = Path(file_path)
raw_disk_bytes = disk_path.read_bytes()
print(f"   Disk file size: {len(raw_disk_bytes)} bytes")
print(f"   First 50 bytes (hex): {raw_disk_bytes[:50].hex()}")
print()

# Check if raw bytes are valid PDF
print("3. Checking if raw bytes are valid PDF...")
try:
    reader = PdfReader(BytesIO(raw_disk_bytes))
    print(f"   ✗ FAIL: Raw bytes are valid PDF (not encrypted!)")
    print(f"   PDF pages: {len(reader.pages)}")
except Exception as e:
    print(f"   ✓ PASS: Raw bytes are NOT valid PDF (encrypted)")
    print(f"   Error: {e}")
print()

# Try to decrypt the bytes
print("4. Attempting to decrypt the bytes...")
try:
    decrypted = encryption_service.decrypt_bytes(raw_disk_bytes)
    print(f"   ✓ Decryption successful")
    print(f"   Decrypted size: {len(decrypted)} bytes")
    print(f"   First 50 bytes (hex): {decrypted[:50].hex()}")
    
    # Verify decrypted content matches original
    if decrypted == test_pdf_content:
        print(f"   ✓ Decrypted content matches original")
    else:
        print(f"   ✗ Decrypted content does NOT match original")
except Exception as e:
    print(f"   ✗ Decryption failed: {e}")
print()

# Clean up
print("5. Cleaning up test file...")
if disk_path.exists():
    disk_path.unlink()
    print(f"   Test file deleted")
else:
    print(f"   Test file not found (already deleted?)")
