from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


class DatabaseSessionManager:
    def __init__(self, database_url: str) -> None:
        # Check if using SQLite
        is_sqlite = database_url.startswith("sqlite")
        
        # Production-optimized database connection settings
        engine_kwargs = {
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "echo": settings.APP_ENV.lower() == "development",  # Log SQL in dev only
        }
        
        # SQLite-specific settings
        if is_sqlite:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            # PostgreSQL settings
            engine_kwargs.update({
                "pool_size": 10,  # Base pool size
                "max_overflow": 20,  # Additional connections when pool is full
            })
            
            # Additional production settings for PostgreSQL
            if settings.APP_ENV.lower() == "production":
                engine_kwargs.update({
                    "pool_size": 20,
                    "max_overflow": 40,
                    "connect_args": {
                        "connect_timeout": 10,
                        "sslmode": "require",  # Require SSL in production
                    }
                })
        
        self.engine: Engine = create_engine(database_url, **engine_kwargs)
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def get_session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()


db_manager = DatabaseSessionManager(settings.DATABASE_URL)
engine = db_manager.engine


def get_db() -> Generator[Session, None, None]:
    yield from db_manager.get_session()
