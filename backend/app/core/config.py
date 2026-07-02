import os
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra fields in .env (like frontend variables)
    )

    PROJECT_NAME: str = "AI Knowledge Assistant"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = Field(
        default="sqlite:///./ai_knowledge_assistant.db"
    )
    JWT_SECRET_KEY: str = "replace-this-development-jwt-secret-with-32-plus-characters"
    FERNET_SECRET_KEY: str = "change-me-change-me-change-me-32bytes"
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = 7
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_MAX_REQUESTS: int = 120
    RATE_LIMIT_AUTH_MAX_REQUESTS: int = 20
    RATE_LIMIT_UPLOAD_MAX_REQUESTS: int = 20
    UPLOAD_ROOT_DIR: str = os.getenv(
        "UPLOAD_DIR",
        "/opt/render/project/src/uploads"
    )
    MAX_UPLOAD_SIZE_BYTES: int = 10485760
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md"]
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY", 
        "/opt/render/project/src/chroma_data"
    )
    CHROMA_COLLECTION_NAME: str = "knowledge_chunks"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 4
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    # Supported: "llama3.2:3b" (others can be added in LLM service mapping)
    LLM_MODEL_NAME: str = "llama3.2:3b"
    LLM_API_KEY: str | None = None
    LLM_BASE_URL: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2:3b"
    OLLAMA_KEEP_ALIVE: str = "5m"
    ENFORCE_LOCAL_ONLY_AI: bool = False
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long.")
        return value

    @field_validator("FERNET_SECRET_KEY")
    @classmethod
    def validate_fernet_secret(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32:
            raise ValueError("FERNET_SECRET_KEY must be at least 32 bytes long.")
        return value

    @model_validator(mode="after")
    def validate_local_only_ai(self) -> "Settings":
        if self.ENFORCE_LOCAL_ONLY_AI:
            parsed = urlparse(self.OLLAMA_BASE_URL)
            if parsed.hostname not in {"localhost", "127.0.0.1"}:
                raise ValueError("OLLAMA_BASE_URL must point to a local host when ENFORCE_LOCAL_ONLY_AI is enabled.")

            if self.LLM_PROVIDER.lower() != "ollama":
                self.LLM_PROVIDER = "ollama"

        if self.APP_ENV.lower() == "production" and self.JWT_SECRET_KEY == "change-me-in-production":
            raise ValueError("JWT_SECRET_KEY must be replaced in production.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
