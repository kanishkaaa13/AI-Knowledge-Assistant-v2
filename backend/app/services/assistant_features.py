from __future__ import annotations

import json

from app.models.user import User
from app.services.ollama_llm import OllamaLLMService
from app.services.prompt_builder import (
    build_quiz_prompt,
    build_summary_prompt,
    build_suggested_prompts_prompt,
)
from app.services.vector_store import VectorStoreService


class AssistantFeatureService:
    def __init__(self, vector_store: VectorStoreService) -> None:
        self.vector_store = vector_store
        self.ollama = OllamaLLMService()

    async def summarize_documents(
        self,
        *,
        user: User,
        query: str,
        model: str,
        top_k: int = 4,
        document_ids: list[str] | None = None,
    ) -> dict:
        # Retrieve context from ChromaDB
        search_results = await self.vector_store.similarity_search(
            user_id=user.id,
            query=query,
            top_k=top_k,
            document_ids=document_ids,
        )

        if not search_results:
            return {
                "summary": "I was unable to generate a response. Please try again.",
                "chunks": [],
                "context": "",
            }

        # Build context from retrieved chunks
        context = "\n\n".join([result.document for result in search_results])
        
        # Build summary prompt
        prompt = build_summary_prompt(query=query, context=context)
        summary = await self.ollama.generate(prompt=prompt, model=model)
        
        return {
            "summary": summary.strip() or "I was unable to generate a response. Please try again.",
            "chunks": [{"content": result.document, "metadata": result.metadata} for result in search_results],
            "context": context,
        }

    async def generate_quiz(
        self,
        *,
        user: User,
        query: str,
        model: str,
        count: int = 3,
        document_ids: list[str] | None = None,
    ) -> dict:
        # Retrieve context from ChromaDB
        search_results = await self.vector_store.similarity_search(
            user_id=user.id,
            query=query,
            top_k=max(count, 4),
            document_ids=document_ids,
        )

        if not search_results:
            return {
                "questions": [],
                "chunks": [],
                "context": "",
            }

        # Build context from retrieved chunks
        context = "\n\n".join([result.document for result in search_results])
        
        # Build quiz prompt with JSON format specification
        prompt = build_quiz_prompt(query=query, context=context, count=count)
        raw = await self.ollama.generate(prompt=prompt, model=model)
        
        try:
            # Try to parse JSON response
            questions = json.loads(raw)
            # Ensure questions have the required format
            formatted_questions = []
            for q in questions if isinstance(questions, list) else []:
                formatted_questions.append({
                    "question": q.get("question", ""),
                    "answer": q.get("answer", ""),
                    "difficulty": q.get("difficulty", "medium")
                })
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty array
            formatted_questions = []
        
        return {
            "questions": formatted_questions,
            "chunks": [{"content": result.document, "metadata": result.metadata} for result in search_results],
            "context": context,
        }

    async def suggested_prompts(
        self,
        *,
        user: User,
        query: str,
        model: str,
        document_ids: list[str] | None = None,
    ) -> dict:
        # Retrieve context from ChromaDB
        search_results = await self.vector_store.similarity_search(
            user_id=user.id,
            query=query,
            top_k=6,
            document_ids=document_ids,
        )

        if not search_results:
            return {
                "prompts": [],
                "chunks": [],
            }

        # Build context from retrieved chunks
        context = "\n\n".join([result.document for result in search_results])
        
        # Build suggested prompts prompt
        prompt = build_suggested_prompts_prompt(query=query, context=context)
        raw = await self.ollama.generate(prompt=prompt, model=model)
        
        # Parse prompts from response
        prompts = [line.strip("- ").strip() for line in raw.splitlines() if line.strip()]
        
        return {
            "prompts": prompts[:3],
            "chunks": [{"content": result.document, "metadata": result.metadata} for result in search_results],
        }

    async def generate_study_notes(
        self,
        *,
        user: User,
        query: str,
        model: str,
        document_ids: list[str] | None = None,
    ) -> dict:
        # Retrieve context from ChromaDB
        search_results = await self.vector_store.similarity_search(
            user_id=user.id,
            query=query,
            top_k=8,  # Retrieve more context for high-quality comprehensive notes!
            document_ids=document_ids,
        )

        if not search_results:
            return {
                "notes": "I was unable to generate study notes because no document content matched the query. Please ensure your documents are selected and indexed.",
                "chunks": [],
                "context": "",
            }

        # Build context from retrieved chunks
        context = "\n\n".join([result.document for result in search_results])
        
        # Build study notes prompt
        from app.services.prompt_builder import build_study_notes_prompt
        prompt = build_study_notes_prompt(query=query, context=context)
        notes_content = await self.ollama.generate(prompt=prompt, model=model)
        
        return {
            "notes": notes_content.strip() or "I was unable to generate study notes. Please try again.",
            "chunks": [{"content": result.document, "metadata": result.metadata} for result in search_results],
            "context": context,
        }
