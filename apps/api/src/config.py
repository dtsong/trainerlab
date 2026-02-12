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
    database_password: str | None = None  # Override password if set

    @property
    def effective_database_url(self) -> str:
        """Get database URL with password injected if DATABASE_PASSWORD is set."""
        if self.database_password:
            # Replace password in URL
            # URL format: postgresql+asyncpg://user:password@host:port/db
            # or: postgresql+asyncpg://user@host:port/db (no password)
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(self.database_url)
            if parsed.username:
                # Reconstruct with new password
                netloc = f"{parsed.username}:{self.database_password}@{parsed.hostname}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                new_url = urlunparse((parsed.scheme, netloc, parsed.path, "", "", ""))
                return new_url
        return self.database_url

    # TCGdex
    tcgdex_url: str = "https://api.tcgdex.net/v2"

    # OpenAI (optional)
    openai_api_key: str | None = None

    # Anthropic (Claude API)
    anthropic_api_key: str | None = None

    # Auth (NextAuth.js shared secret for JWT verification)
    nextauth_secret: str | None = None

    # Admin (comma-separated emails)
    admin_emails: str = ""

    # Ops alerts (GitHub Actions / webhooks)
    # Shared secret used by scheduled readiness alert checks
    readiness_alert_token: str | None = None

    # CORS (comma-separated list of origins)
    cors_origins: str = "http://localhost:3000"

    # Cloud Scheduler (for pipeline auth)
    # The Cloud Run service URL (audience for OIDC tokens)
    cloud_run_url: str | None = None
    # Service account email for Cloud Scheduler
    scheduler_service_account: str | None = None
    # Service account email for Operations (manual testing)
    operations_service_account: str | None = None
    # Bypass scheduler auth in development
    scheduler_auth_bypass: bool = False

    # Cloud Tasks (tournament scrape pipeline)
    cloud_tasks_queue_path: str | None = None
    cloud_tasks_location: str | None = None
    # API service account email (used by Cloud Tasks for OIDC auth)
    api_service_account: str | None = None

    # Cloud Storage (creator exports)
    exports_bucket: str = "trainerlab-exports"

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
