import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Document Intelligence API"
    ENVIRONMENT: str = "development"

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "doc_intel")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey_please_change_me_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Extraction
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)

    class Config:
        case_sensitive = True


settings = Settings()
