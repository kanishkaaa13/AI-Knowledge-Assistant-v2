"""
Fix Unit 4's DB chunk records (ChromaDB already has its vectors from the previous run).
Also update document status to 'indexed' for both docs.
Run with: .venv\Scripts\python reindex_all.py
"""
import sys
sys.path.append(".")

from app.core.config import settings
from app.db.session import db_manager
from app.models.uploaded_document import UploadedDocument
from app.services.rag_pipeline import RAGIngestionService

print("=" * 60)
print("FORCE REINDEX ALL DOCUMENTS")
print("=" * 60)

with db_manager.session_factory() as db:
    docs = db.query(UploadedDocument).all()
    print(f"Found {len(docs)} document(s) in DB\n")

    for doc in docs:
        text_len = len(doc.extracted_text or "")
        print(f"[DOC] '{doc.file_name}'")
        print(f"      id       = {doc.id}")
        print(f"      status   = {doc.status}")
        print(f"      text_len = {text_len} chars")

        if not doc.extracted_text or not doc.extracted_text.strip():
            print(f"      SKIP: no extracted_text")
            continue

        print(f"      Calling index_document...")
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

print("\nDone.")
