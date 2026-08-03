"""
Query database for documents with 'Unit' or 'unit' in filename
"""
import sys
sys.path.append(".")

from app.core.config import settings
from app.db.session import db_manager
from app.models.uploaded_document import UploadedDocument

print("=" * 60)
print("QUERYING DATABASE FOR UNIT DOCUMENTS")
print("=" * 60)

with db_manager.session_factory() as db:
    # Query for documents with 'unit' in filename (case-insensitive)
    unit_docs = db.query(UploadedDocument).filter(
        UploadedDocument.file_name.ilike("%unit%")
    ).all()
    
    print(f"Found {len(unit_docs)} document(s) with 'unit' in filename:\n")
    
    for doc in unit_docs:
        print(f"[DOC] '{doc.file_name}'")
        print(f"      id       = {doc.id}")
        print(f"      status   = {doc.status}")
        print(f"      title    = {doc.title}")
        print(f"      text_len = {len(doc.extracted_text or '')} chars")
        print(f"      page_count = {doc.page_count}")
        print()
    
    # Also show all documents for reference
    all_docs = db.query(UploadedDocument).all()
    print(f"\nTotal documents in database: {len(all_docs)}")
    print("All document filenames:")
    for doc in all_docs:
        print(f"  - {doc.file_name}")

print("\nDone.")
