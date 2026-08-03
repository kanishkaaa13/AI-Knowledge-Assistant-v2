"""
Investigate duplicate Unit 4.pdf entries
"""
import sys
sys.path.append(".")

from app.core.config import settings
from app.db.session import db_manager
from app.models.uploaded_document import UploadedDocument

print("=" * 60)
print("INVESTIGATING DUPLICATE UNIT 4.PDF ENTRIES")
print("=" * 60)

with db_manager.session_factory() as db:
    # Get both Unit 4.pdf entries
    unit4_docs = db.query(UploadedDocument).filter(
        UploadedDocument.file_name == "Unit 4.pdf"
    ).all()
    
    print(f"Found {len(unit4_docs)} Unit 4.pdf entries:\n")
    
    for i, doc in enumerate(unit4_docs, 1):
        print(f"[ENTRY {i}] '{doc.file_name}'")
        print(f"      id       = {doc.id}")
        print(f"      user_id  = {doc.user_id}")
        print(f"      status   = {doc.status}")
        print(f"      title    = {doc.title}")
        print(f"      file_size = {doc.file_size} bytes")
        print(f"      checksum = {doc.checksum}")
        print(f"      text_len = {len(doc.extracted_text or '')} chars")
        print(f"      page_count = {doc.page_count}")
        print(f"      created_at = {doc.created_at}")
        print()
    
    if len(unit4_docs) == 2:
        doc1, doc2 = unit4_docs
        print("COMPARISON:")
        print(f"  Checksums match: {doc1.checksum == doc2.checksum}")
        print(f"  File sizes match: {doc1.file_size == doc2.file_size}")
        print(f"  Text lengths match: {len(doc1.extracted_text or '') == len(doc2.extracted_text or '')}")
        print(f"  Page counts match: {doc1.page_count == doc2.page_count}")
        print(f"  User IDs match: {doc1.user_id == doc2.user_id}")
        
        if doc1.checksum == doc2.checksum:
            print("\n✓ IDENTICAL CONTENT - same checksum")
            print(f"  Recommendation: Delete the older entry")
            print(f"  Older ID: {doc1.id if doc1.created_at < doc2.created_at else doc2.id}")
            print(f"  Newer ID: {doc2.id if doc1.created_at < doc2.created_at else doc1.id}")
        else:
            print("\n✗ DIFFERENT CONTENT - different checksums")
            print("  These are different files with the same name")

print("\nDone.")
