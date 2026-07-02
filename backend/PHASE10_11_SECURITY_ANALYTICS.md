# Phases 10 and 11: Security, Privacy, and Analytics

## Security and Privacy

- JWT cookies are now protected with CSRF tokens and stricter auth context checks.
- Files are stored encrypted at rest with Fernet and decrypted only when downloaded.
- Uploads are validated by extension, MIME type, size, emptiness, and duplicate checksum.
- User prompts, titles, and search inputs are sanitized before persistence or retrieval.
- Rate limiting is applied globally and reinforced on auth, assistant, conversation, and upload flows.
- Chroma metadata now carries `user_id`, and vector queries are filtered to that same user.
- Local-only inference is enforced by configuration so Ollama must remain on `localhost` or `127.0.0.1`.

## Analytics

- Analytics are generated from live PostgreSQL data for:
  - total documents
  - total chats
  - storage usage
  - recent uploads
  - AI usage stats
- The backend exposes:
  - `GET /api/v1/assistant/summary`
  - `GET /api/v1/assistant/analytics`
- The frontend analytics page uses Recharts for upload, chat, and message activity visuals.

## Architecture Notes

- Security middleware stays centralized in `app/core/middleware.py`.
- Encryption stays isolated in `app/core/crypto.py`.
- Sanitization and rate-limiting helpers are reusable across route modules.
- Analytics use repository-level aggregate methods rather than loading whole datasets into memory.
