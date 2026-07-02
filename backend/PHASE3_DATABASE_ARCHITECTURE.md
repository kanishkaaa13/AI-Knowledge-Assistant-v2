# Phase 3 Database Architecture

This phase introduces the core PostgreSQL schema for the Personal AI Knowledge Assistant using SQLAlchemy ORM, Alembic migrations, UUID primary keys, cascading deletes, and a reusable repository layer.

## ER Diagram Explanation

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : owns
    CONVERSATIONS ||--o{ MESSAGES : contains
    USERS ||--o{ UPLOADED_DOCUMENTS : uploads
    UPLOADED_DOCUMENTS ||--o{ DOCUMENT_CHUNKS : splits_into
    USERS ||--|| SETTINGS : configures

    USERS {
        uuid id PK
        string name
        string email UK
        string hashed_password
        datetime created_at
        datetime updated_at
    }

    CONVERSATIONS {
        uuid id PK
        uuid user_id FK
        string title
        text summary
        datetime created_at
        datetime updated_at
    }

    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        int sequence_number
        datetime created_at
        datetime updated_at
    }

    UPLOADED_DOCUMENTS {
        uuid id PK
        uuid user_id FK
        string title
        string file_name
        string file_path
        string mime_type
        int file_size
        string status
        text extracted_text
        datetime created_at
        datetime updated_at
    }

    DOCUMENT_CHUNKS {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content
        int token_count
        datetime created_at
        datetime updated_at
    }

    SETTINGS {
        uuid id PK
        uuid user_id FK
        string theme
        string preferred_model
        boolean memory_enabled
        datetime created_at
        datetime updated_at
    }
```

## Relationship Design

- `users -> conversations` is one-to-many so each user can have many chat threads.
- `conversations -> messages` is one-to-many so each thread preserves an ordered message history.
- `users -> uploaded_documents` is one-to-many so a user can manage many source files.
- `uploaded_documents -> document_chunks` is one-to-many so retrieval pipelines can split files into embeddings-ready chunks.
- `users -> settings` is one-to-one so each user has a single configuration profile.

## Constraint and Index Strategy

- Every table uses a UUID primary key to support distributed creation and safer external references.
- Every relationship uses foreign keys with `ON DELETE CASCADE` so dependent records are removed automatically.
- Every table includes `created_at` and `updated_at` timestamps.
- Important lookup paths are indexed:
  - `users.email`
  - `conversations.user_id`, `conversations.user_id + updated_at`
  - `messages.conversation_id`, `messages.conversation_id + created_at`
  - `uploaded_documents.user_id`, `uploaded_documents.user_id + status`, `uploaded_documents.user_id + updated_at`
  - `document_chunks.document_id`, `document_chunks.document_id + chunk_index`
  - `settings.user_id`
- Ordering integrity is protected with unique constraints on:
  - `messages (conversation_id, sequence_number)`
  - `document_chunks (document_id, chunk_index)`

## Files Added In Phase 3

- SQLAlchemy models in `backend/app/models/`
- Pydantic schemas in `backend/app/schemas/`
- Repositories in `backend/app/repositories/`
- DB session manager in `backend/app/db/session.py`
- Alembic config in `backend/alembic.ini` and `backend/alembic/`

## Migration Workflow

From the `backend` folder:

```bash
alembic upgrade head
```

To generate future revisions after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```
