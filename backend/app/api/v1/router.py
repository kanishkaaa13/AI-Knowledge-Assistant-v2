from fastapi import APIRouter

from app.api.v1.routes import assistant, auth, conversations, documents, health, notes, flashcards

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["flashcards"])
