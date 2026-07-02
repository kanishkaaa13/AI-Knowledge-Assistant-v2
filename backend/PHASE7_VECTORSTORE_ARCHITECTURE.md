# Phase 7 ChromaDB Integration

This phase upgrades the vector layer into a reusable service architecture with per-user collections, richer metadata, and hybrid retrieval.

## Collection Strategy

- Each user gets a separate Chroma collection.
- Collection names follow:
  - `knowledge_chunks_<user_uuid>`
- This keeps vector search isolated per user without relying only on metadata filters.

## Stored Metadata

Every vector record stores:

- `filename`
- `page`
- `chunk_id`
- `upload_timestamp`
- `document_id`
- `document_title`
- `user_id`
- `chunk_index`

## Service Layer

Main implementation:

- `backend/app/services/vector_store.py`

Key operations:

- `upsert_vectors(...)`
- `update_vectors(...)`
- `delete_vectors(...)`
- `semantic_similarity_search(...)`
- `hybrid_similarity_search(...)`

## Hybrid Retrieval

Hybrid retrieval works by:

1. Running semantic similarity search in the user’s collection
2. Expanding the candidate pool
3. Calculating lexical overlap between query terms and chunk text
4. Combining semantic and keyword signals into a reranked score

Current weighting:

- semantic score: `75%`
- keyword overlap score: `25%`

## RAG Integration

- Upload indexing now writes vectors into the user’s own Chroma collection
- Re-indexing updates vectors through upsert behavior
- Deleting a document removes its vector ids from the matching user collection
- Retrieval returns page and filename metadata alongside chunk text
