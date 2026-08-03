"""
Report reindexing metrics
"""
import sys
sys.path.append(".")

from app.core.config import settings
from app.db.session import db_manager
from app.models.uploaded_document import UploadedDocument
from app.models.document_chunk import DocumentChunk
import chromadb

print("=" * 60)
print("REINDEXING METRICS REPORT")
print("=" * 60)

with db_manager.session_factory() as db:
    # Get all documents
    docs = db.query(UploadedDocument).all()
    print(f"\n1. Total documents in database: {len(docs)}")
    
    # Get chunks per document
    print("\n2. Per-document chunk counts:")
    total_chunks = 0
    for doc in docs:
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).count()
        total_chunks += chunk_count
        print(f"   {doc.file_name}: {chunk_count} chunks")
    
    print(f"\n   Total chunks across all documents: {total_chunks}")
    
    # Check for section metadata
    print("\n3. Section metadata analysis:")
    docs_with_sections = 0
    docs_without_sections = 0
    
    for doc in docs:
        # Get a sample chunk to check for section metadata
        sample_chunk = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc.id
        ).first()
        
        if sample_chunk:
            # We need to check ChromaDB for section metadata
            pass
    
    # Check ChromaDB collections
    print("\n4. ChromaDB vector counts:")
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
    for col in client.list_collections():
        c = client.get_collection(col.name)
        count = c.count()
        print(f"   {col.name}: {count} vectors")
        
        # Check for section metadata in sample
        if count > 0:
            sample = c.get(limit=1)
            if sample['metadatas']:
                has_section = 'section' in sample['metadatas'][0]
                has_section_level = 'section_level' in sample['metadatas'][0]
                print(f"      Has section metadata: {has_section}")
                print(f"      Has section_level metadata: {has_section_level}")
                if has_section:
                    print(f"      Sample section: {sample['metadatas'][0].get('section', 'N/A')}")

print("\n" + "=" * 60)
print("REINDEXING COMPLETE")
print("=" * 60)
