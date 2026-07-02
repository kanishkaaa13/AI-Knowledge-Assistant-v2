import uuid
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.flashcard import Flashcard
from app.repositories.flashcard import FlashcardRepository
from app.schemas.flashcard import FlashcardCreate, FlashcardUpdate
from app.services.vector_store import get_vector_store_service
from app.services.ollama_llm import OllamaLLMService

logger = logging.getLogger(__name__)

class FlashcardService:
    def __init__(self, db: Session) -> None:
        self.repository = FlashcardRepository(db)
        self.vector_store = get_vector_store_service()
        self.ollama = OllamaLLMService()

    def list_flashcards(self, user: User, document_id: Optional[uuid.UUID] = None) -> List[Flashcard]:
        return self.repository.list_by_user(user.id, document_id=document_id)

    def get_flashcard(self, user: User, flashcard_id: uuid.UUID) -> Flashcard:
        card = self.repository.get_by_user(user.id, flashcard_id)
        if not card:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flashcard not found.")
        return card

    def create_flashcard(self, user: User, schema: FlashcardCreate) -> Flashcard:
        card_data = schema.model_dump()
        card_data["user_id"] = user.id
        return self.repository.create(**card_data)

    def update_flashcard(self, user: User, flashcard_id: uuid.UUID, schema: FlashcardUpdate) -> Flashcard:
        card = self.get_flashcard(user, flashcard_id)
        update_data = schema.model_dump(exclude_unset=True)
        return self.repository.update(card, **update_data)

    def delete_flashcard(self, user: User, flashcard_id: uuid.UUID) -> None:
        card = self.get_flashcard(user, flashcard_id)
        self.repository.delete(card)

    async def generate_flashcards(
        self,
        user: User,
        document_ids: List[str],
        query: Optional[str] = None,
        count: int = 5,
        model: str = "llama3"
    ) -> List[Flashcard]:
        # Clean document list
        cleaned_doc_ids = [doc_id for doc_id in document_ids if doc_id]

        if not cleaned_doc_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please select at least one document to generate flashcards."
            )

        # Retrieve relevant text context for generation
        search_query = query if query and query.strip() else "key concepts, definitions, main facts"
        try:
            search_results = await self.vector_store.similarity_search(
                user_id=user.id,
                query=search_query,
                top_k=max(count, 6),
                document_ids=cleaned_doc_ids
            )
        except Exception as e:
            logger.exception("Failed to retrieve context for flashcard generation")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to query document content: {str(e)}"
            )

        if not search_results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No content found in the selected documents. Ensure they are indexed."
            )

        # Build context sections
        context = "\n\n".join([
            f"[Source: {r.metadata.get('filename', 'Unknown')} | Page {r.metadata.get('page', 1)}]\n{r.document}"
            for r in search_results
        ])

        from app.services.prompt_builder import build_flashcard_prompt

        # Build quiz prompt with JSON format specification
        prompt = build_flashcard_prompt(context=context, count=count)

        try:
            raw_response = await self.ollama.generate(prompt=prompt, model=model)
            raw_response = raw_response.strip()
            
            # Clean possible markdown wrap from local model
            if raw_response.startswith("```json"):
                raw_response = raw_response.replace("```json", "", 1)
            if raw_response.endswith("```"):
                raw_response = raw_response.rsplit("```", 1)[0]
            raw_response = raw_response.strip()

            cards_data = json.loads(raw_response)
        except Exception as e:
            logger.exception("Failed to generate or parse flashcards from local model")
            # Create a simple fallback flashcard rather than complete failure
            cards_data = [{
                "front": "What is the primary topic of the selected documents?",
                "back": f"Based on retrieval, this document talks about: {search_results[0].document[:200]}...",
                "difficulty": "medium"
            }]

        created_cards = []
        doc_uuid = uuid.UUID(cleaned_doc_ids[0]) if cleaned_doc_ids else None

        for card in cards_data:
            front = card.get("front", "").strip()
            back = card.get("back", "").strip()
            if not front or not back:
                continue

            created = self.repository.create(
                user_id=user.id,
                document_id=doc_uuid,
                front=front,
                back=back,
                difficulty=card.get("difficulty", "medium"),
                tags="AI Generated",
                source_context=context[:1000]
            )
            created_cards.append(created)

        return created_cards
