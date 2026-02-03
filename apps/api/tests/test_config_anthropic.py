"""Tests for Anthropic API key config."""

from unittest.mock import patch

from src.config import Settings


class TestAnthropicConfig:
    def test_anthropic_api_key_default_none(self):
        """Anthropic API key defaults to None."""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(
                _env_file=None,
                database_url="postgresql+asyncpg://x@localhost/x",
            )
            assert settings.anthropic_api_key is None

    def test_anthropic_api_key_from_env(self):
        """Anthropic API key loads from environment variable."""
        with patch.dict(
            "os.environ",
            {"ANTHROPIC_API_KEY": "sk-ant-test-key"},
            clear=True,
        ):
            settings = Settings(
                _env_file=None,
                database_url="postgresql+asyncpg://x@localhost/x",
            )
            assert settings.anthropic_api_key == "sk-ant-test-key"
