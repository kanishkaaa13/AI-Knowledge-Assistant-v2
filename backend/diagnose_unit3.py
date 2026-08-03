import sqlite3
import uuid

# Get Unit 3 document ID from database
conn = sqlite3.connect('ai_knowledge_assistant.db')
cur = conn.cursor()

print("=== STEP A: Find Unit 3 document ID ===")
cur.execute('SELECT id, title, file_name, status FROM uploaded_documents WHERE file_name LIKE "%Unit 3%" OR title LIKE "%Unit 3%"')
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
if rows:
    for row in rows:
        print(dict(zip(cols, row)))
        unit3_id = row[0]
else:
    print("No Unit 3 document found in database")
    conn.close()
    exit(1)

print(f"\nUnit 3 Document ID: {unit3_id}")

# Check chunks in database for Unit 3
print("\n=== STEP B: Check chunks in database for Unit 3 ===")
cur.execute('SELECT COUNT(*) FROM document_chunks WHERE document_id = ?', (str(unit3_id),))
db_chunk_count = cur.fetchone()[0]
print(f"Chunks in SQL database for Unit 3: {db_chunk_count}")

conn.close()

# Check ChromaDB
print("\n=== STEP B (continued): Check ChromaDB for Unit 3 ===")
import chromadb
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings

# Get user ID from chunks query
conn = sqlite3.connect('ai_knowledge_assistant.db')
cur = conn.cursor()
cur.execute('SELECT user_id FROM uploaded_documents WHERE id = ?', (str(unit3_id),))
user_id = cur.fetchone()[0]
conn.close()

print(f"User ID for Unit 3: {user_id}")

# Connect to ChromaDB
client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
collection_name = f"user_collection_{user_id}"
print(f"ChromaDB collection name: {collection_name}")

try:
    collection = client.get_collection(name=collection_name)
    total_count = collection.count()
    print(f"Total vectors in collection: {total_count}")
    
    # Query for Unit 3 chunks only
    results = collection.get(
        where={"document_id": str(unit3_id)},
        include=["documents", "metadatas"]
    )
    unit3_chunk_count = len(results.get("ids", []))
    print(f"Chunks in ChromaDB for Unit 3: {unit3_chunk_count}")
    
    if unit3_chunk_count > 0:
        print(f"\nFirst few metadata entries for Unit 3:")
        for i in range(min(3, unit3_chunk_count)):
            print(f"  Chunk {i+1}: {results['metadatas'][i]}")
except Exception as e:
    print(f"ChromaDB error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== STEP C: Test retrieval with simple query ===")
try:
    collection = client.get_collection(name=collection_name)
    test_results = collection.query(
        query_texts=["summary"],
        n_results=5,
        where={"document_id": str(unit3_id)},
        include=["documents", "metadatas", "distances"]
    )
    
    result_count = len(test_results.get("ids", [[]])[0])
    print(f"Test query 'summary' returned {result_count} results")
    
    if result_count > 0:
        print(f"\nFirst result:")
        print(f"  Distance: {test_results['distances'][0][0]}")
        print(f"  Document snippet: {test_results['documents'][0][0][:200]}...")
        print(f"  Metadata: {test_results['metadatas'][0][0]}")
    else:
        print("No results returned from test query")
except Exception as e:
    print(f"Test query error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== DIAGNOSIS COMPLETE ===")
