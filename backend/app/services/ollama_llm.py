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

    async def generate(self, *, prompt: str, model: str, temperature: float | None = None) -> str:
        if self.provider == "openai":
            return await self._openai_generate(prompt, temperature)
        if self.provider == "groq":
            return await self._groq_generate(prompt, temperature)
        if self.provider == "ollama":
            return await self._ollama_generate(prompt, model, temperature)
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {self.provider!r}")

    # ------------------------------------------------------------------
    # Streaming generation
    # ------------------------------------------------------------------

    async def stream_generate(
        self, *, prompt: str, model: str | None = None, temperature: float | None = None
    ) -> AsyncIterator[str]:
        if self.provider == "openai":
            async for token in self._openai_stream(prompt, temperature):
                yield token
        elif self.provider == "groq":
            async for token in self._groq_stream(prompt, temperature):
                yield token
        elif self.provider == "ollama":
            model_name = model or settings.DEFAULT_CHAT_MODEL
            async for token in self._ollama_stream(prompt, model_name, temperature):
                yield token
        else:
            raise RuntimeError(f"Unsupported LLM_PROVIDER: {self.provider!r}")

    # ==================================================================
    # OpenAI
    # ==================================================================

    async def _openai_generate(self, prompt: str, temperature: float | None = None) -> str:
        client = _get_openai_client()
        logger.info("OpenAI generate -> model=%s, temperature=%s", settings.OPENAI_MODEL_NAME, temperature)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature if temperature is not None else 0.0,
        )
        return response.choices[0].message.content or ""

    async def _openai_stream(self, prompt: str, temperature: float | None = None) -> AsyncIterator[str]:
        client = _get_openai_client()
        logger.info("OpenAI stream -> model=%s, temperature=%s", settings.OPENAI_MODEL_NAME, temperature)
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ]
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL_NAME,
            messages=messages,
            stream=True,
            temperature=temperature if temperature is not None else 0.0,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    # ==================================================================
    # Groq  (OpenAI-compatible REST API)
    # ==================================================================

    async def _groq_generate(self, prompt: str, temperature: float | None = None) -> str:
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
            "temperature": temperature if temperature is not None else 0.0,
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

    async def _groq_stream(self, prompt: str, temperature: float | None = None) -> AsyncIterator[str]:
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
            "temperature": temperature if temperature is not None else 0.0,
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
                        except (json.JSONDecodeError, KeyError, IndexError) as exc:
                            logger.warning(
                                "Skipping unreadable Groq stream chunk (%s): %r", exc, data_str
                            )
                            continue

    # ==================================================================
    # Ollama
    # ==================================================================

    async def _ollama_generate(self, prompt: str, model: str, temperature: float | None = None) -> str:
        import os
        import time

        base_url = os.environ.get("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
        resolved_model = await self._resolve_model(model, base_url)
        logger.info("Ollama generate -> model=%s (requested: %s), temperature=%s", resolved_model, model, temperature)
        
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        }
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
        
        logger.info("[OLLAMA REQUEST] Payload: %s", json.dumps(payload, indent=2))
        
        start_time = time.time()
        logger.info("[TIMING] Ollama request sent at %.3f", start_time)
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(600.0, connect=10.0)
            ) as client:
                try:
                    resp = await client.post(
                        f"{base_url}/api/generate",
                        json=payload,
                    )
                except httpx.ConnectError as e:
                    logger.error("[OLLAMA ERROR] Connection failed: %s", e)
                    raise RuntimeError(
                        "Ollama is not running or is unreachable. "
                        f"Please ensure Ollama is running at {base_url}"
                    ) from e
                except httpx.TimeoutException as e:
                    logger.error("[OLLAMA ERROR] Timeout: %s", e)
                    raise RuntimeError(
                        f"Ollama request timed out. The model may be loading slowly."
                    ) from e
                
                logger.info("[OLLAMA RESPONSE] Status: %d", resp.status_code)
                
                if resp.status_code != 200:
                    logger.error("[OLLAMA ERROR] Non-200 response: %s", resp.text)
                    raise RuntimeError(
                        f"Ollama returned error {resp.status_code}: {resp.text[:200]}"
                    )
                
                end_time = time.time()
                logger.info("[TIMING] Ollama response received at %.3f (duration: %.3f seconds)", end_time, end_time - start_time)
                return resp.json()["response"]
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            logger.error("[OLLAMA ERROR] Unexpected error: %s", e)
            raise RuntimeError(f"Ollama generation failed: {str(e)}") from e

    async def _ollama_stream(self, prompt: str, model: str, temperature: float | None = None) -> AsyncIterator[str]:
        import os
        import time

        base_url = os.environ.get("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
        resolved_model = await self._resolve_model(model, base_url)
        logger.info("Ollama stream -> model=%s (requested: %s), temperature=%s", resolved_model, model, temperature)
        
        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        }
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
        
        logger.info("[OLLAMA STREAM REQUEST] Payload: %s", json.dumps(payload, indent=2))
        
        start_time = time.time()
        logger.info("[TIMING] Ollama stream request sent at %.3f", start_time)
        first_token_time = None
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(600.0, connect=10.0)
            ) as client:
                try:
                    async with client.stream(
                        "POST",
                        f"{base_url}/api/generate",
                        json=payload,
                    ) as response:
                        logger.info("[OLLAMA STREAM RESPONSE] Status: %d", response.status_code)
                        
                        if response.status_code != 200:
                            logger.error("[OLLAMA STREAM ERROR] Non-200 response: %s", await response.aread())
                            raise RuntimeError(
                                f"Ollama stream returned error {response.status_code}"
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
                                if first_token_time is None:
                                    first_token_time = time.time()
                                    logger.info("[TIMING] First token received at %.3f (time to first token: %.3f seconds)", first_token_time, first_token_time - start_time)
                                yield token
                            if chunk.get("done", False):
                                break
                except httpx.ConnectError as e:
                    logger.error("[OLLAMA STREAM ERROR] Connection failed: %s", e)
                    raise RuntimeError(
                        "Ollama is not running or is unreachable. "
                        f"Please ensure Ollama is running at {base_url}"
                    ) from e
                except httpx.TimeoutException as e:
                    logger.error("[OLLAMA STREAM ERROR] Timeout: %s", e)
                    raise RuntimeError(
                        f"Ollama stream request timed out. The model may be loading slowly."
                    ) from e
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            logger.error("[OLLAMA STREAM ERROR] Unexpected error: %s", e)
            raise RuntimeError(f"Ollama stream generation failed: {str(e)}") from e
