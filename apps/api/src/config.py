"""Application configuration using Pydantic settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: str = "development"
    debug: bool = False

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/trainerlab"
    )

    # Redis
    redis_url: str = "redis://localhost:6379"

    # TCGdex
    tcgdex_url: str = "http://localhost:3001"

    # OpenAI (optional)
    openai_api_key: str | None = None

    # Firebase (optional)
    firebase_project_id: str | None = None

    # CORS (comma-separated list of origins)
    cors_origins: str = "http://localhost:3000"

    # Cloud Scheduler (for pipeline auth)
    # The Cloud Run service URL (audience for OIDC tokens)
    cloud_run_url: str | None = None
    # Service account email for Cloud Scheduler
    scheduler_service_account: str | None = None
    # Bypass scheduler auth in development
    scheduler_auth_bypass: bool = False

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
