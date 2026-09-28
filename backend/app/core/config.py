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


def get_settings() -> Settings:
    return Settings()
