import logging
import sys
import re

# Force UTF-8 output on Windows (prevents cp1252 UnicodeEncodeError from print statements)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://ai-knowledge-app-3.vercel.app",
    "https://ai-knowledge-app-3-git-main-kanishkaarde99-4507s-projects.vercel.app",
]

def is_origin_allowed(origin: str) -> bool:
    if not origin:
        return False
    if origin in ALLOWED_ORIGINS:
        return True
    if re.match(r"^https://ai-knowledge-app-3.*\.vercel\.app$", origin):
        return True
    return False

from app.api.v1.router import api_router
from app import models  # noqa: F401
from app.core.config import settings
from app.core.middleware import CORSFallbackMiddleware, JWTContextMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.core import security


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logging.error(f"Unhandled exception: {exc}", exc_info=True)
        origin = request.headers.get("origin", "")
        headers = {}
        if is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"

        if settings.APP_ENV.lower() == "production":
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers=headers
            )
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
            headers=headers
        )


def create_application() -> FastAPI:
    # Configure logging
    log_level = "INFO" if settings.APP_ENV.lower() == "production" else "DEBUG"
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    import asyncio
    import httpx
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        import time
        import os
        from app.services.vector_store import get_vector_store_service
        
        # Ensure ChromaDB persist directory exists
        os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        os.makedirs(settings.UPLOAD_ROOT_DIR, exist_ok=True)

        # Pre-warm the embedding model in a thread so the event loop stays free
        t0 = time.time()
        print(f"[STARTUP] Pre-warming embedding model '{settings.EMBEDDING_MODEL_NAME}'...")
        try:
            vs = get_vector_store_service()
            await asyncio.to_thread(vs._get_embedding_model_sync)
            print(f"[STARTUP] Embedding model ready in {time.time() - t0:.2f}s")
        except Exception as exc:
            print(f"[STARTUP] Warning: could not pre-warm embedding model: {exc}")

        print(f"[STARTUP] LLM provider: {settings.LLM_PROVIDER} | model: {settings.DEFAULT_CHAT_MODEL}")
        
        # Verify local Ollama availability at startup if selected as provider
        if settings.LLM_PROVIDER.lower() == "ollama":
            print(f"[STARTUP] Checking if local Ollama is reachable at {settings.OLLAMA_BASE_URL}...")
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(settings.OLLAMA_BASE_URL)
                    resp.raise_for_status()
                print("[STARTUP] Ollama check: OK")
            except Exception as exc:
                print("\n" + "="*80)
                print(" [STARTUP ERROR] LOCAL OLLAMA SERVICE IS UNREACHABLE!")
                print(f" Reason: {exc}")
                print("-"*80)
                print(" To fix this, please start the Ollama service locally:")
                print("   1. Open a command prompt / terminal")
                print("   2. Run command: ollama serve")
                print("   3. Run command: ollama pull qwen2.5:3b-instruct (if not pulled already)")
                print("="*80 + "\n")
                raise SystemExit(1)

        yield  # App runs here
        
        print("[SHUTDOWN] Cleaning up...")

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        docs_url="/docs" if settings.APP_ENV.lower() != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV.lower() != "production" else None,
        lifespan=lifespan,
    )

    @app.exception_handler(HTTPException)
    async def cors_aware_http_exception_handler(request: Request, exc: HTTPException):
        origin = request.headers.get("origin", "")
        headers = {}
        if is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=headers,
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_origin_regex=r"^https://ai-knowledge-app-3.*\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(JWTContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CORSFallbackMiddleware)
    
    register_exception_handlers(app)

    # Mount static file serving for uploads
    upload_dir = Path(settings.UPLOAD_ROOT_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        return {"message": f"{settings.PROJECT_NAME} API is running.", "environment": settings.APP_ENV}

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "environment": settings.APP_ENV}

    @app.get("/cors-test")
    async def cors_test(request: Request):
        return JSONResponse(
            content={"origin_received": request.headers.get("origin", "none")},
            headers={
                "Access-Control-Allow-Origin": request.headers.get(
                    "origin", "https://ai-knowledge-app-3.vercel.app"
                ),
                "Access-Control-Allow-Credentials": "true",
            }
        )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_application()
