"""
Show the literal HTTP response for decryption failure
"""

print("Literal HTTP Response for Decryption Failure:")
print("=" * 80)
print()

print("When StoredDocumentParser.parse() encounters a decryption failure,")
print("it raises an HTTPException with the following response:")
print()

print("HTTP/1.1 422 Unprocessable Entity")
print("Content-Type: application/json")
print()
print("{")
print('  "detail": "Document file cannot be read: Stored file could not be decrypted. The file may be corrupted or encryption may have failed during upload."')
print("}")
print()

print("=" * 80)
print("Code path:")
print("  1. StoredDocumentParser.parse() calls read_encrypted_document_bytes()")
print("  2. read_encrypted_document_bytes() calls encryption_service.decrypt_bytes()")
print("  3. decrypt_bytes() raises InvalidToken (cryptography.fernet)")
print("  4. read_encrypted_document_bytes() catches InvalidToken and raises HTTPException:")
print("     - status_code: 500")
print("     - detail: 'Stored file could not be decrypted.'")
print("  5. StoredDocumentParser.parse() catches HTTPException and re-raises with:")
print("     - status_code: 422")
print("     - detail: 'Document file cannot be read: {original_detail}. The file may be corrupted or encryption may have failed during upload.'")
print("  6. rag_pipeline.py catches the HTTPException (or it propagates to the API layer)")
print("  7. User sees the 422 response with the detailed error message")
print("=" * 80)
