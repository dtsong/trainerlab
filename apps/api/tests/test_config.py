"""Tests for config.py."""

from src.config import Settings, get_settings


class TestEffectiveDatabaseUrl:
    """Tests for effective_database_url property."""

    def test_returns_default_when_no_password(self) -> None:
        """Should return original URL when database_password is not set."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:oldpass@localhost:5432/db",
            database_password=None,
        )
        assert (
            settings.effective_database_url
            == "postgresql+asyncpg://user:oldpass@localhost:5432/db"
        )

    def test_injects_password_into_url(self) -> None:
        """Should replace password in URL when database_password is set."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:oldpass@localhost:5432/db",
            database_password="newpass",
        )
        result = settings.effective_database_url
        assert "newpass" in result
        assert "oldpass" not in result
        assert "user:" in result
        assert "localhost" in result

    def test_injects_password_with_port(self) -> None:
        """Should preserve port when injecting password."""
        settings = Settings(
            database_url="postgresql+asyncpg://myuser:oldpw@myhost:5432/mydb",
            database_password="secretpw",
        )
        result = settings.effective_database_url
        assert ":5432" in result
        assert "myuser:secretpw" in result
        assert "/mydb" in result

    def test_injects_password_without_existing_password(self) -> None:
        """Should handle URL without existing password."""
        settings = Settings(
            database_url="postgresql+asyncpg://user@localhost:5432/db",
            database_password="newpass",
        )
        result = settings.effective_database_url
        assert "user:newpass" in result


class TestEnvironmentProperties:
    """Tests for is_development and is_production."""

    def test_is_development_true(self) -> None:
        """Should return True when environment is development."""
        settings = Settings(environment="development")
        assert settings.is_development is True
        assert settings.is_production is False

    def test_is_production_true(self) -> None:
        """Should return True when environment is production."""
        settings = Settings(environment="production")
        assert settings.is_production is True
        assert settings.is_development is False

    def test_is_staging_neither(self) -> None:
        """Should return False for both when environment is staging."""
        settings = Settings(environment="staging")
        assert settings.is_development is False
        assert settings.is_production is False


class TestGetSettings:
    """Tests for get_settings function."""

    def test_returns_settings_instance(self) -> None:
        """Should return a Settings instance."""
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)
        get_settings.cache_clear()

    def test_returns_cached_instance(self) -> None:
        """Should return the same cached instance on multiple calls."""
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()
