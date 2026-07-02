import sys
sys.path.append(".")
from app.core.config import settings
import chromadb
import os

print(f"CHROMA_PERSIST_DIRECTORY: {settings.CHROMA_PERSIST_DIRECTORY}")
print(f"Absolute path: {os.path.abspath(settings.CHROMA_PERSIST_DIRECTORY)}")
print(f"Directory exists: {os.path.exists(settings.CHROMA_PERSIST_DIRECTORY)}")
print(f"Directory contents: {os.listdir(settings.CHROMA_PERSIST_DIRECTORY) if os.path.exists(settings.CHROMA_PERSIST_DIRECTORY) else 'MISSING'}")

print("\n--- PersistentClient ---")
try:
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
    collections = client.list_collections()
    print(f"Collections found: {[c.name for c in collections]}")
    for c in collections:
        col = client.get_collection(c.name)
        count = col.count()
        print(f"  Collection '{c.name}': {count} chunks")
        if count > 0:
            sample = col.get(limit=2)
            print(f"  Sample IDs: {sample['ids']}")
            print(f"  Sample metadata: {sample['metadatas']}")
        else:
            print(f"  Collection is EMPTY")
except Exception as e:
    import traceback
    print(f"PersistentClient error: {e}")
    traceback.print_exc()

print("\n--- Also checking VectorStoreService directly ---")
try:
    from app.services.vector_store import get_vector_store_service
    vs = get_vector_store_service()
    print(f"VectorStore persist_directory: {vs.client._settings.persist_directory if hasattr(vs.client, '_settings') else 'unknown'}")
    print(f"VectorStore model_name: {vs.model_name}")
    cols = vs.client.list_collections()
    print(f"Collections via VectorStore singleton: {[c.name for c in cols]}")
    for c in cols:
        col = vs.client.get_collection(c.name)
        print(f"  '{c.name}': {col.count()} chunks")
except Exception as e:
    import traceback
    print(f"VectorStoreService error: {e}")
    traceback.print_exc()

print("\n--- DB check: uploaded documents ---")
try:
    from app.db.session import get_db
    from app.models.uploaded_document import UploadedDocument
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    with Session() as session:
        docs = session.query(UploadedDocument).all()
        print(f"Total documents in DB: {len(docs)}")
        for doc in docs:
            text_len = len(doc.extracted_text or "")
            print(f"  [{doc.status}] '{doc.file_name}' | id={doc.id} | user_id={doc.user_id} | extracted_text={text_len} chars")
except Exception as e:
    import traceback
    print(f"DB check error: {e}")
    traceback.print_exc()

print("\n--- In-memory client (sanity check) ---")
try:
    client2 = chromadb.EphemeralClient()
    print(f"In-memory client collections: {client2.list_collections()}")
except Exception as e:
    print(f"In-memory client error: {e}")
