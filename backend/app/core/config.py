from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = (
        "postgresql+psycopg://dharohar:dharohar@localhost:5432/dharohar"
    )
    TEST_DATABASE_URL: str = (
        "postgresql+psycopg://dharohar:dharohar@localhost:5432/dharohar_test"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:5173"

    # Security & JWT
    SECRET_KEY: str = "dharohar-secret-key-development-minimum-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage
    STORAGE_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".jpg", ".jpeg", ".png"]

    # Thresholds
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    LOW_CONFIDENCE_THRESHOLD: float = 0.65

    # Models
    ENHANCEMENT_MODEL_PATH: str = "models/enhancement/best.pt"
    OCR_MODEL_PATH: str = "models/ocr/best.pt"

    # Celery execution mode
    CELERY_ALWAYS_EAGER: bool = False

    # Environment
    ENVIRONMENT: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance — reads .env once per process."""
    return Settings()
