from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException, status
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMGateway:
    def __init__(self) -> None:
        if settings.LLM_PROVIDER.lower() != "openai":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only the OpenAI-compatible LLM gateway is configured in this scaffold.",
            )

        if not settings.LLM_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM API key is not configured.",
            )

        self.client = ChatOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL_NAME,
            temperature=0,
        )

    def generate(self, prompt: str) -> str:
        response = self.client.invoke(prompt)
        return response.content if isinstance(response.content, str) else str(response.content)


@lru_cache
def get_llm_gateway() -> LLMGateway:
    return LLMGateway()
