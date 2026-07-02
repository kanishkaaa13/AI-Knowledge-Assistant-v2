from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

from dotenv import load_dotenv
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

async def generate_response(prompt: str) -> str:
    print(f"[LLM] Sending prompt to {OLLAMA_BASE_URL}/api/generate")
    print(f"[LLM] Model: {OLLAMA_MODEL}")
    print(f"[LLM] Prompt preview: {prompt[:100]}")

    print(f"[LLM] Using model: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            data = response.json()
            print(f"[LLM] Success. Response length: {len(data.get('response', ''))}")
            return data["response"]

    except httpx.ConnectError as e:
        print(f"[LLM ERROR] Cannot connect to Ollama: {e}")
        raise Exception("Cannot connect to Ollama at " + OLLAMA_BASE_URL)
    except httpx.TimeoutException as e:
        print(f"[LLM ERROR] Ollama timed out: {e}")
        raise Exception("Ollama request timed out after 300s")
    except Exception as e:
        print(f"[LLM ERROR] Unexpected error: {e}")
        raise

DEFAULT_MODEL = getattr(settings, 'OLLAMA_DEFAULT_MODEL', 'llama3.2:3b')
SUPPORTED_OLLAMA_MODELS = [DEFAULT_MODEL, "deepseek-r1:1.5b", "deepseek-r1:14b", "llama3", "mistral", "llama3.2:3b"]


class OllamaLLMService:
    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.keep_alive = settings.OLLAMA_KEEP_ALIVE
        parsed = urlparse(self.base_url)
        if settings.ENFORCE_LOCAL_ONLY_AI and parsed.hostname not in {"localhost", "127.0.0.1"}:
            raise RuntimeError("OLLAMA_BASE_URL must stay local for privacy-first inference.")

    def _validate_model(self, model: str | None) -> str:
        if not model:
            return DEFAULT_MODEL
        normalized = model.strip().lower()
        if normalized not in SUPPORTED_OLLAMA_MODELS:
            return DEFAULT_MODEL
        return normalized

    async def generate(self, *, prompt: str, model: str) -> str:
        return await generate_response(prompt)

    async def stream_generate(self, *, prompt: str, model: str | None = None) -> AsyncIterator[str]:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ]

        if settings.LLM_PROVIDER == "groq":
            if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "PASTE_YOUR_GROQ_KEY_HERE":
                raise RuntimeError(
                    "Groq API key is not set. Go to https://console.groq.com/keys, "
                    "create a free key, and paste it as GROQ_API_KEY in backend/.env"
                )
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": settings.GROQ_MODEL,
                "messages": messages,
                "stream": True,
                "max_tokens": 1024
            }
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status_code == 401:
                        raise RuntimeError("Invalid Groq API key. Check your GROQ_API_KEY in backend/.env")
                    if response.status_code != 200:
                        body = await response.aread()
                        raise RuntimeError(f"Groq API error {response.status_code}: {body.decode()}")
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]": break
                            try:
                                chunk = json.loads(data)
                                token = chunk["choices"][0]["delta"].get("content", "")
                                if token:
                                    yield token
                            except Exception:
                                continue
            return

        import os
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        selected_model = os.environ.get("OLLAMA_MODEL", "llama3")
        url = f"{base_url}/api/generate"
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": True  # Real token-by-token streaming
        }

        print(f"[OLLAMA] STREAM POST {url} model={selected_model}")

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        raise RuntimeError(f"Ollama returned {response.status_code}: {body.decode()}")

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

                        # Ollama signals completion with done=True
                        if chunk.get("done", False):
                            print("[OLLAMA] Stream complete")
                            break

        except httpx.ConnectError:
            raise RuntimeError("Cannot connect to Ollama. Make sure it is running: ollama serve")
        except httpx.TimeoutException:
            raise RuntimeError("Ollama request timed out. The AI model may be loading, try again.")
