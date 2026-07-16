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
      - ``openai`` — uses the async OpenAI SDK
      - ``groq``   — uses Groq's OpenAI-compatible REST API via httpx
      - ``ollama`` (default) — uses local Ollama with dynamic fallback resolution

    Ollama is the default provider. If the configured provider fails,
    the error propagates immediately.
    """

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER.lower()

    async def _resolve_model(self, requested_model: str, base_url: str) -> str:
        """
        Query Ollama's /api/tags endpoint to check if requested_model is installed.
        Falls back to llama3.2:3b or first available model if it is not available.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{base_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    installed_names = [m.get("name") for m in models if m.get("name")]
                    
                    # 1. Check exact match
                    if requested_model in installed_names:
                        return requested_model
                    
                    # 2. Check for tag-less match (e.g. "qwen2.5:3b-instruct" vs "qwen2.5:3b-instruct:latest")
                    for name in installed_names:
                        if name.startswith(requested_model + ":") or requested_model.startswith(name + ":"):
                            return name
                            
                    # 3. If requested qwen2.5, try variations or fallback to llama3.2:3b
                    if "qwen2.5" in requested_model.lower():
                        for name in installed_names:
                            if "qwen2.5" in name.lower() and "3b" in name.lower():
                                return name
                        for name in installed_names:
                            if "llama3.2" in name.lower() or "llama3" in name.lower():
                                return name

                    # 4. Check if standard fallback model is installed
                    if "llama3.2:3b" in installed_names:
                        return "llama3.2:3b"
                        
                    # 5. Fallback to first available model so the system doesn't crash
                    if installed_names:
                        logger.warning(
                            "Requested model %s is not installed. Falling back to first available: %s",
                            requested_model, installed_names[0]
                        )
                        return installed_names[0]
        except Exception as e:
            logger.warning("Failed to query Ollama /api/tags for model resolution: %s", e)
            
        return requested_model

    # ------------------------------------------------------------------
    # Non-streaming generation
    # ------------------------------------------------------------------

    async def generate(self, *, prompt: str, model: str) -> str:
        if self.provider == "openai":
            return await self._openai_generate(prompt)
        if self.provider == "groq":
            return await self._groq_generate(prompt)
        if self.provider == "ollama":
            return await self._ollama_generate(prompt, model)
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
            model_name = model or settings.DEFAULT_CHAT_MODEL
            async for token in self._ollama_stream(prompt, model_name):
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
    # Ollama
    # ==================================================================

    async def _ollama_generate(self, prompt: str, model: str) -> str:
        import os

        base_url = os.environ.get("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
        resolved_model = await self._resolve_model(model, base_url)
        logger.info("Ollama generate -> model=%s (requested: %s)", resolved_model, model)
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(600.0, connect=10.0)
        ) as client:
            payload = {
                "model": resolved_model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            }
            resp = await client.post(
                f"{base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def _ollama_stream(self, prompt: str, model: str) -> AsyncIterator[str]:
        import os

        base_url = os.environ.get("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
        resolved_model = await self._resolve_model(model, base_url)
        logger.info("Ollama stream -> model=%s (requested: %s)", resolved_model, model)
        
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(600.0, connect=10.0)
        ) as client:
            payload = {
                "model": resolved_model,
                "prompt": prompt,
                "stream": True,
                "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            }
            async with client.stream(
                "POST",
                f"{base_url}/api/generate",
                json=payload,
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
