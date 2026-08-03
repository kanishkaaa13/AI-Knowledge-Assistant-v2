"""
Reindex only test documents (Unit-3.pdf and machine-learning-cheat-sheet.pdf)
to test structure-aware chunking with section detection.
Run with: python reindex_test_docs.py
"""
import sys
sys.path.append(".")

from app.core.config import settings
from app.db.session import db_manager
from app.models.uploaded_document import UploadedDocument
from app.services.rag_pipeline import RAGIngestionService

print("=" * 60)
print("REINDEX TEST DOCUMENTS (Structure-Aware Chunking)")
print("=" * 60)

# Target documents to reindex
TARGET_DOCS = [
    "Unit-3.pdf",
    "machine-learning-cheat-sheet.pdf"
]

with db_manager.session_factory() as db:
    docs = db.query(UploadedDocument).filter(
        UploadedDocument.file_name.in_(TARGET_DOCS)
    ).all()
    
    print(f"Found {len(docs)} target document(s) in DB\n")
    
    if len(docs) == 0:
        print("No target documents found. Available documents:")
        all_docs = db.query(UploadedDocument).all()
        for doc in all_docs:
            print(f"  - {doc.file_name}")
        sys.exit(1)
    
    for doc in docs:
        text_len = len(doc.extracted_text or "")
        print(f"[DOC] '{doc.file_name}'")
        print(f"      id       = {doc.id}")
        print(f"      status   = {doc.status}")
        print(f"      text_len = {text_len} chars")

        if not doc.extracted_text or not doc.extracted_text.strip():
            print(f"      SKIP: no extracted_text")
            continue

        print(f"      Calling index_document with section detection...")
        try:
            service = RAGIngestionService(db)
            chunks = service.index_document(doc)
            print(f"      SUCCESS: {len(chunks)} chunks indexed [OK]")
        except Exception as e:
            import traceback
            print(f"      FAILED: {e}")
            traceback.print_exc()
        print()

print("=" * 60)
print("Verifying ChromaDB state after reindex...")
print("=" * 60)
import chromadb
client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
for col in client.list_collections():
    c = client.get_collection(col.name)
    count = c.count()
    print(f"  Collection '{col.name}': {count} chunks")
    if count > 0:
        sample = c.get(limit=1)
        print(f"  Sample metadata keys: {list(sample['metadatas'][0].keys()) if sample['metadatas'] else 'none'}")
        if 'section' in sample['metadatas'][0]:
            print(f"  Sample section: {sample['metadatas'][0].get('section', 'N/A')}")
            print(f"  Sample section_level: {sample['metadatas'][0].get('section_level', 'N/A')}")

print("\nDone.")
