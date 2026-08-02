# RAG Pipeline Implementation Explained

This document traces through the actual RAG (Retrieval-Augmented Generation) pipeline implementation in the AI Knowledge Assistant, using real code, libraries, and parameter values.

## Pipeline Flow Diagrams

### Indexing Pipeline (Upload → Storage)
```
Upload File → Parse Text → Chunk Text → Embed Chunks → Store in ChromaDB
     ↓              ↓           ↓            ↓                ↓
  /documents    pypdf/      Recursive   DefaultEmbedding   VectorStore
   /upload      python-docx  Character     Function         Service
                            TextSplitter
```

### Retrieval Pipeline (Query → Generation)
```
User Query → Embed Query → Search ChromaDB → Retrieve Chunks → Build Context → LLM Generation
     ↓            ↓              ↓               ↓              ↓              ↓
  /assistant   DefaultEmbedding  Semantic/    Top-k chunks   Prompt        Ollama/
   /query       Function         Hybrid        (k=4)          Template      OpenAI
```

---

## 1. Document Upload & Entry Point

**File:** `backend/app/api/v1/routes/documents.py`
**Function:** `upload_document()` (line 83)

**Route:** `POST /documents/upload`

**Process:**
1. User uploads file via multipart form data
2. Rate limiting applied (5 uploads per user)
3. File validation (type, size, content-type)
4. Calls `DocumentProcessor.process_document()` for full pipeline

**Libraries Used:**
- FastAPI `UploadFile` for file handling
- `python-docx` for DOCX parsing
- `pypdf` for PDF parsing

---

## 2. File Parsing (Text Extraction)

**File:** `backend/app/services/document_processor.py`
**Function:** `extract_text()` (line 36)

**Implementation by File Type:**

### PDF Files
```python
from pypdf import PdfReader
reader = PdfReader(BytesIO(file_bytes))
text = "\n".join(page.extract_text() or "" for page in reader.pages)
return text, len(reader.pages)
```
- **Library:** `pypdf` (PyPDF2)
- **Method:** `page.extract_text()` per page
- **Returns:** Extracted text + page count

### DOCX Files
```python
from docx import Document as DocxDocument
document = DocxDocument(BytesIO(file_bytes))
text = "\n".join(paragraph.text for paragraph in document.paragraphs)
return text, len(document.paragraphs)
```
- **Library:** `python-docx`
- **Method:** Extract all paragraphs
- **Returns:** Extracted text + paragraph count

### TXT/MD Files
```python
try:
    return file_bytes.decode("utf-8"), None
except UnicodeDecodeError:
    return file_bytes.decode("latin-1"), None
```
- **Method:** Direct UTF-8/Latin-1 decoding
- **Returns:** Extracted text + None (no page count)

---

## 3. Text Chunking

**File:** `backend/app/services/rag_pipeline.py`
**Function:** `index_document()` (line 60)

**Chunking Strategy:**
- **Library:** `langchain_text_splitters.RecursiveCharacterTextSplitter`
- **Chunk Size:** 500 characters (from `settings.RAG_CHUNK_SIZE`)
- **Chunk Overlap:** 50 characters (from `settings.RAG_CHUNK_OVERLAP`)
- **Separators:** `["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]`

**Implementation:**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.RAG_CHUNK_SIZE,  # 500
    chunk_overlap=settings.RAG_CHUNK_OVERLAP,  # 50
    separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
)
```

**Paragraph-Aware Chunking:**
The pipeline first splits text by paragraphs (double newlines), then chunks each paragraph if it exceeds 500 characters. This preserves paragraph boundaries.

**Chunk Metadata:**
Each chunk includes:
- `chunk_index`: Global index across document
- `page`: Page number from source document
- `paragraph_index`: Paragraph position within page
- `document_id`: Source document UUID
- `filename`: Original file name
- `okf_type`: OKF concept type (if matched)
- `okf_tags`: OKF tags (if matched)

---

## 4. Tokenization

**Implementation:** No explicit tokenization step.

**Details:**
- Chunking is **character-based**, not token-based
- Token counting is done post-chunking for metadata: `len(chunk_text.split())`
- Embedding model handles tokenization internally

---

## 5. Embedding Generation

**File:** `backend/app/services/vector_store.py`
**Function:** `_get_embedding_model_sync()` (line 64)

**Embedding Model:**
- **Library:** ChromaDB's `DefaultEmbeddingFunction`
- **Model:** `"default-onnx-embedding"` (ChromaDB's built-in ONNX model)
- **Not:** Sentence Transformers (despite config comment)
- **Vector Dimension:** 384 (ChromaDB default)

**Implementation:**
```python
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

self._embedding_function = DefaultEmbeddingFunction()
# Pre-warm by embedding dummy string
self._embedding_function(["warmup"])
```

**Embedding Process:**
1. Embedding function is loaded lazily on first use
2. For sync ingestion (upload): loaded in thread pool
3. For async retrieval: loaded via `asyncio.to_thread()`
4. ChromaDB automatically handles embedding when upserting vectors

---

## 6. Vector Storage (ChromaDB)

**File:** `backend/app/services/vector_store.py`
**Function:** `add_documents_to_vector_store()` (line 96)

**Storage Details:**
- **Vector Database:** ChromaDB (PersistentClient)
- **Storage Path:** `storage/chromadb/`
- **Collection Naming:** `user_collection_{user_id}` (per-user isolation)
- **Operation:** `upsert` (update or insert)

**Metadata Stored per Chunk:**
```python
metadata = {
    "user_id": str(user_id),
    "document_id": str(document.id),
    "document_title": document.title,
    "filename": document.file_name,
    "chunk_index": global_chunk_index,
    "chunk_id": vector_id,
    "page": str(page.page_number),
    "paragraph_index": str(p_idx),
    "upload_timestamp": document.created_at.isoformat(),
    "tags": document.tags or "",
    "okf_type": best_okf.type,  # if matched
    "okf_tags": ",".join(best_okf.tags),  # if matched
}
```

**Storage Process:**
1. Create/get user-specific collection
2. Prepare chunk IDs, documents, and metadata
3. Stringify non-scalar metadata values (ChromaDB requirement)
4. Call `collection.upsert(ids, documents, metadatas)`
5. ChromaDB automatically generates embeddings

---

## 7. Retrieval (Query Time)

**File:** `backend/app/services/rag_pipeline.py`
**Function:** `retrieve()` (line 247)

**Retrieval Configuration:**
- **Default top_k:** 4 (from `settings.RAG_TOP_K`)
- **Search Method:** Semantic similarity (cosine similarity)
- **Optional:** Hybrid search (semantic + keyword BM25)

**Query Flow:**
```python
# Check cache first
cache_key = f"retrieval:{user.id}:{query}:{top_k}:{hybrid}:{document_ids}"
cached = app_cache.get(cache_key)

if not cached:
    k = top_k or settings.RAG_TOP_K  # defaults to 4
    
    if hybrid:
        results = await self.vector_store.hybrid_similarity_search(
            user_id=user.id, query=query, top_k=k, document_ids=document_ids
        )
    else:
        results = await self.vector_store.semantic_similarity_search(
            user_id=user.id, query=query, top_k=k, document_ids=document_ids
        )
```

**Similarity Search Implementation:**
**File:** `backend/app/services/vector_store.py`
**Function:** `similarity_search()` (line 211)

```python
results = collection.query(
    query_texts=[query],
    n_results=min(top_k, count),  # Clamp to collection size
    where=where_clause,  # Filter by user_id, document_id, etc.
    include=["documents", "metadatas", "distances"],
)
```

**Filtering Options:**
- `user_id`: Always applied (per-user isolation)
- `document_ids`: Optional (filter to specific documents)
- `okf_type`: Optional (filter by OKF concept type)
- `okf_tags`: Optional (filter by OKF tags)

**No Reranking:**
- Straight top-k return based on cosine similarity
- No additional reranking step
- Hybrid search uses Reciprocal Rank Fusion (RRF) if enabled

---

## 8. Context Assembly

**File:** `backend/app/services/rag_pipeline.py`
**Function:** `retrieve()` (line 350)

**Context Format:**
```python
context_sections.append(
    f"[Source: {db_document.file_name}, Page {chunk.page_number or 1}, Paragraph {chunk.paragraph_index or 1}]\n{chunk.content}"
)
context = "\n\n".join(context_sections)
```

**Example Context:**
```
[Source: research_paper.pdf, Page 5, Paragraph 2]
The experimental results showed a 23% improvement in accuracy...

[Source: research_paper.pdf, Page 7, Paragraph 1]
Further analysis revealed that the model performed better on...
```

---

## 9. Prompt Template

**File:** `backend/app/services/prompt_builder.py`
**Function:** `build_rag_prompt()` (line 89)

**RAG Prompt Template:**
```python
GROUNDED_RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    """You are a helpful AI study assistant. Your task is to answer the user's question using ONLY the provided document context.

Rules:
1. Ground your answers strictly in the provided DOCUMENT CONTEXT.
2. You MUST include source citations in your answer when referencing specific information. Format citations exactly like this: [Source: filename, Page X, Paragraph Y].
3. Do NOT make up information or reference external knowledge not present in the context.
4. If the provided context does not contain the answer, reply EXACTLY with: "I couldn't find this information in the selected documents."

DOCUMENT CONTEXT:
{context}

USER QUESTION: {query}

ANSWER:"""
)
```

**Prompt Assembly:**
```python
from app.services.prompt_builder import build_rag_prompt

prompt = build_rag_prompt(
    query=user_query,
    context=retrieved_context  # Formatted chunks with citations
)
```

---

## 10. LLM Generation

**File:** `backend/app/services/ollama_llm.py`
**Function:** `stream_generate()` (line 111)

**LLM Configuration:**
- **Provider:** Ollama (default) or OpenAI/Groq (configurable)
- **Model:** `qwen2.5:3b-instruct` (default) or user-specified
- **Temperature:** 0.2 (for RAG answers, set in `assistant_chat.py`)
- **Streaming:** Enabled (Server-Sent Events)

**Generation Process:**
```python
async for token in self.ollama_service.stream_generate(
    prompt=prompt,  # RAG-augmented prompt
    model=model,
    temperature=0.2  # Low temperature for deterministic answers
):
    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
```

**Response Flow:**
1. LLM generates tokens one by one
2. Each token sent as SSE event to frontend
3. Frontend appends tokens to message bubble in real-time
4. Final answer persisted to conversation history

---

## Configuration Values

**File:** `backend/app/core/config.py`

```python
RAG_CHUNK_SIZE: int = 500
RAG_CHUNK_OVERLAP: int = 50
RAG_TOP_K: int = 4
EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"  # Not actually used
OLLAMA_KEEP_ALIVE: str = "5m"
DEFAULT_CHAT_MODEL: str = "qwen2.5:3b-instruct"
LLM_PROVIDER: str = "ollama"
```

---

## Key Implementation Notes

1. **Per-User Isolation:** Each user has their own ChromaDB collection (`user_collection_{user_id}`)
2. **Paragraph-Aware Chunking:** Preserves paragraph boundaries for better context
3. **OKF Integration:** Chunks are tagged with matching OKF concepts for enhanced filtering
4. **Caching:** Retrieval results cached for 45 seconds to reduce repeated queries
5. **No Explicit Tokenization:** Character-based chunking, embedding model handles tokenization
6. **Low Temperature:** RAG answers use temperature=0.2 for deterministic, grounded responses
7. **Citation Format:** `[Source: filename, Page X, Paragraph Y]` format enforced in prompt
8. **Hybrid Search Optional:** Can combine semantic + keyword search via RRF

---

## File Reference Summary

| Stage | File | Function |
|-------|------|----------|
| Upload | `app/api/v1/routes/documents.py` | `upload_document()` |
| Parsing | `app/services/document_processor.py` | `extract_text()` |
| Chunking | `app/services/rag_pipeline.py` | `index_document()` |
| Embedding | `app/services/vector_store.py` | `_get_embedding_model_sync()` |
| Storage | `app/services/vector_store.py` | `add_documents_to_vector_store()` |
| Retrieval | `app/services/rag_pipeline.py` | `retrieve()` |
| Context | `app/services/rag_pipeline.py` | `retrieve()` (line 350) |
| Prompt | `app/services/prompt_builder.py` | `build_rag_prompt()` |
| Generation | `app/services/ollama_llm.py` | `stream_generate()` |
