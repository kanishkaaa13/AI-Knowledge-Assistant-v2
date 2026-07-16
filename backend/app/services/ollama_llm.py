from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared async OpenAI client (reused across calls — avoids per-request overhead)
# ---------------------------------------------------------------------------
_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. "
                "Set it in backend/.env and restart the server."
            )
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


class OllamaLLMService:
    """
    Unified LLM service.

    Routes to the provider configured by ``LLM_PROVIDER`` in settings:
      - ``openai`` (default) — uses the async OpenAI SDK
      - ``groq``  — uses Groq's OpenAI-compatible REST API via httpx
      - ``ollama`` — uses a local Ollama instance (opt-in only)

    Ollama is **never** used as a silent fallback.  If the configured
    provider fails, the error propagates immediately.
    """

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER.lower()

    # ------------------------------------------------------------------
    # Non-streaming generation
    # ------------------------------------------------------------------

    async def generate(self, *, prompt: str, model: str) -> str:
        if self.provider == "openai":
            return await self._openai_generate(prompt)
        if self.provider == "groq":
            return await self._groq_generate(prompt)
        if self.provider == "ollama":
            return await self._ollama_generate(prompt)
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {self.provider!r}")

    # ------------------------------------------------------------------
    # Streaming generation
    # ------------------------------------------------------------------

    async def stream_generate(
        self, *, prompt: str, model: str | None = None
    ) -> AsyncIterator[str]:
        if self.provider == "openai":
            async for token in self._openai_stream(prompt):
                yield token
        elif self.provider == "groq":
            async for token in self._groq_stream(prompt):
                yield token
        elif self.provider == "ollama":
            async for token in self._ollama_stream(prompt):
                yield token
        else:
            raise RuntimeError(f"Unsupported LLM_PROVIDER: {self.provider!r}")

    # ==================================================================
    # OpenAI
    # ==================================================================

    async def _openai_generate(self, prompt: str) -> str:
        client = _get_openai_client()
        logger.info("OpenAI generate -> model=%s", settings.OPENAI_MODEL_NAME)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return response.choices[0].message.content or ""

    async def _openai_stream(self, prompt: str) -> AsyncIterator[str]:
        client = _get_openai_client()
        logger.info("OpenAI stream -> model=%s", settings.OPENAI_MODEL_NAME)
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ]
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            stream=True,
            temperature=0.0,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    # ==================================================================
    # Groq  (OpenAI-compatible REST API)
    # ==================================================================

    async def _groq_generate(self, prompt: str) -> str:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _groq_stream(self, prompt: str) -> AsyncIterator[str]:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
            "max_tokens": 1024,
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code == 401:
                    raise RuntimeError("Invalid Groq API key.")
                if response.status_code != 200:
                    body = await response.aread()
                    raise RuntimeError(
                        f"Groq API error {response.status_code}: {body.decode()}"
                    )
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            token = chunk["choices"][0]["delta"].get("content", "")
                            if token:
                                yield token
                        except Exception:
                            continue

    # ==================================================================
    # Ollama  (opt-in only via LLM_PROVIDER=ollama)
    # ==================================================================

    async def _ollama_generate(self, prompt: str) -> str:
        import os

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        model = os.environ.get("OLLAMA_MODEL", settings.OLLAMA_DEFAULT_MODEL)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(600.0, connect=10.0)
        ) as client:
            resp = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def _ollama_stream(self, prompt: str) -> AsyncIterator[str]:
        import os

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        model = os.environ.get("OLLAMA_MODEL", settings.OLLAMA_DEFAULT_MODEL)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(600.0, connect=10.0)
        ) as client:
            async with client.stream(
                "POST",
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": True},
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise RuntimeError(
                        f"Ollama returned {response.status_code}: {body.decode()}"
                    )
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        break
