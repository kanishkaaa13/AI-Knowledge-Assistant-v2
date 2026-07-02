# Phases 12 and 13: Advanced Assistant Features and Production Optimization

## Advanced Assistant Features

- Hybrid retrieval remains the default and now supports optional document scoping.
- Multi-document querying is supported through `document_ids` on assistant routes.
- AI-generated summaries are available through `/assistant/summaries`.
- Quiz generation is available through `/assistant/quiz`.
- Semantic document search is available through `/assistant/document-search`.
- Suggested prompts are available through `/assistant/suggested-prompts`.
- Conversation export is available through `/conversations/{id}/export`.
- Voice input is handled on the frontend with the browser Speech Recognition API.
- Documents now support tags, favorites, AI summaries, and re-indexing.

## Production Optimization

- Retrieval responses are cached with a TTL cache in `app/core/cache.py`.
- Document ingestion runs in the background after upload returns.
- Uploads are queued with status transitions: `queued -> processing -> indexed/failed`.
- Retrieval avoids repeated N+1 chunk lookups by batching document and chunk loading.
- Frontend search uses debouncing.
- Documents use server-side pagination.
- Conversation and document surfaces use lightweight virtualization helpers.
- Large workspace-side tools are lazy-loaded where helpful.
- A reusable request batcher is included for future high-frequency UI fetches.

## Main Modules

- `app/services/rag_pipeline.py`
- `app/services/assistant_features.py`
- `app/services/background_jobs.py`
- `frontend/hooks/use-chat.ts`
- `frontend/hooks/use-documents.ts`
- `frontend/hooks/use-debounced-value.ts`
- `frontend/hooks/use-virtual-list.ts`
- `frontend/lib/request-batcher.ts`
