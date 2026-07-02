# Phase 6 RAG Architecture

This phase adds a reusable retrieval-augmented generation pipeline using LangChain, Sentence Transformers, and ChromaDB.

## Pipeline Flow

1. Uploaded documents are parsed and text is extracted during Phase 5.
2. `RAGIngestionService` chunks extracted text using `RecursiveCharacterTextSplitter`.
3. Chunks use:
   - `chunk_size = 500`
   - `chunk_overlap = 50`
4. Embeddings are generated with `sentence-transformers/all-MiniLM-L6-v2`.
5. Embeddings are stored in ChromaDB with persistent storage on disk.
6. Chunk rows are stored in PostgreSQL and linked back to their document.
7. `RAGRetrievalService` performs semantic similarity search with top-k retrieval.
8. `RAGAnswerService` assembles context and formats a prompt for the configured LLM.

## Reusable Services

- `backend/app/services/text_chunker.py`
- `backend/app/services/embeddings.py`
- `backend/app/services/vector_store.py`
- `backend/app/services/prompt_builder.py`
- `backend/app/services/llm_gateway.py`
- `backend/app/services/rag_pipeline.py`

## Retrieval Design

- Semantic search uses Chroma similarity search with metadata filtering by `user_id`.
- Retrieved chunks include chunk ids, document ids, scores, and source titles.
- Context is assembled as labeled sections so the model can attribute information back to a document.

## Prompt Strategy

The prompt template instructs the model to:

- answer using only the provided context
- say when the knowledge base is insufficient
- keep answers concise and grounded
- mention source document titles when useful

## Required Environment Variables

```env
CHROMA_PERSIST_DIRECTORY=storage/chroma
CHROMA_COLLECTION_NAME=knowledge_chunks
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=4
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4.1-mini
LLM_API_KEY=your-key
LLM_BASE_URL=
```

## API Surface

- `POST /api/v1/assistant/retrieve`
  Returns top-k retrieved chunks and assembled context.

- `POST /api/v1/assistant/query`
  Runs retrieval, assembles prompt, and sends grounded context to the configured LLM.
