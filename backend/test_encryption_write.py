"""
Test encryption at write time to see if it's actually working
"""

from pathlib import Path
from app.core.crypto import encryption_service

# Test encryption with sample data
test_data = b"This is a test PDF content: %PDF-1.7..."

print("Testing encryption service:")
print(f"Test data: {test_data}")
print()

try:
    encrypted = encryption_service.encrypt_bytes(test_data)
    print(f"✓ Encryption successful")
    print(f"Encrypted size: {len(encrypted)} bytes")
    print(f"Encrypted preview (hex): {encrypted[:50].hex()}")
    print()
    
    # Test decryption
    decrypted = encryption_service.decrypt_bytes(encrypted)
    print(f"✓ Decryption successful")
    print(f"Decrypted data: {decrypted}")
    print(f"Match: {decrypted == test_data}")
except Exception as e:
    print(f"✗ Encryption failed: {e}")
    import traceback
    traceback.print_exc()
