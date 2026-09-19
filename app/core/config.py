import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Document Intelligence API"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # Database — defaults to SQLite for local dev, PostgreSQL in Docker
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "doc_intel"
    DATABASE_URL: str = ""  # Override entirely via env var

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # 1. Explicit DATABASE_URL env var wins (Docker sets this)
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # 2. If postgres server is reachable, use it
        if self.POSTGRES_SERVER not in ("localhost", "127.0.0.1"):
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )
        # 3. Fall back to SQLite for local dev (no Docker required)
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "local.db")
        return f"sqlite:///{os.path.abspath(db_path)}"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "supersecretkey_please_change_in_production_32chars_min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Extraction
    GEMINI_API_KEY: str | None = None

    # File upload
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
