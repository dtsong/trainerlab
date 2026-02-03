"""Tests for Claude API client."""

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from anthropic import APIConnectionError, APIStatusError, RateLimitError

from src.clients.claude import (
    MODEL_HAIKU,
    MODEL_SONNET,
    ClaudeClient,
    ClaudeError,
    TokenUsage,
    TranslationResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_httpx_response(status_code: int = 429) -> httpx.Response:
    """Create a real httpx.Response for exception constructors."""
    return httpx.Response(
        status_code=status_code,
        request=httpx.Request("POST", "https://api.anthropic.com"),
    )


def _make_httpx_request() -> httpx.Request:
    """Create a real httpx.Request for exception constructors."""
    return httpx.Request("POST", "https://api.anthropic.com")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class TestTokenUsage:
    def test_creation(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total == 150

    def test_total_property(self):
        usage = TokenUsage(input_tokens=0, output_tokens=0)
        assert usage.total == 0


class TestTranslationResult:
    def test_creation(self):
        result = TranslationResult(
            translated_text="Translated content",
            glossary_terms_used=["ex draw", "supporter"],
            confidence="high",
        )
        assert result.translated_text == "Translated content"
        assert result.glossary_terms_used == ["ex draw", "supporter"]
        assert result.confidence == "high"

    def test_default_glossary(self):
        result = TranslationResult(
            translated_text="Text",
            confidence="medium",
        )
        assert result.glossary_terms_used == []


class TestClaudeError:
    def test_inherits_exception(self):
        err = ClaudeError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"


# ---------------------------------------------------------------------------
# Client init
# ---------------------------------------------------------------------------


class TestClaudeClientInit:
    def test_default_model(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            client = ClaudeClient()
            assert client._default_model == MODEL_SONNET

    def test_custom_model(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            client = ClaudeClient(default_model=MODEL_HAIKU)
            assert client._default_model == MODEL_HAIKU

    def test_raises_without_api_key(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = None
            with pytest.raises(ClaudeError, match="ANTHROPIC_API_KEY"):
                ClaudeClient()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestClaudeClientContextManager:
    async def test_context_manager(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            async with ClaudeClient() as client:
                assert client._client is not None

    async def test_close(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            client = ClaudeClient()
            await client.close()


# ---------------------------------------------------------------------------
# _call method
# ---------------------------------------------------------------------------


class TestClaudeClientCall:
    @pytest.fixture
    def client(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            c = ClaudeClient()
            c._retry_delay = 0.01  # Fast tests
            yield c

    def _mock_response(self, text="response text", input_tokens=10, output_tokens=5):
        """Create a mock Anthropic message response."""
        mock = MagicMock()
        mock.content = [MagicMock(text=text)]
        mock.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
        mock.model = MODEL_SONNET
        mock.stop_reason = "end_turn"
        return mock

    async def test_call_success(self, client):
        mock_resp = self._mock_response(text="hello")
        client._client.messages.create = AsyncMock(return_value=mock_resp)

        text, usage = await client._call(
            system="You are helpful.",
            user="Hi",
            model=MODEL_SONNET,
            max_tokens=1024,
        )
        assert text == "hello"
        assert usage.input_tokens == 10
        assert usage.output_tokens == 5

    async def test_call_retry_on_rate_limit(self, client):
        mock_resp = self._mock_response()
        call_count = 0

        async def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(
                    message="rate limited",
                    response=_make_httpx_response(429),
                    body=None,
                )
            return mock_resp

        client._client.messages.create = AsyncMock(side_effect=side_effect)

        text, usage = await client._call(
            system="sys", user="msg", model=MODEL_SONNET, max_tokens=100
        )
        assert call_count == 2
        assert text == "response text"

    async def test_call_retry_on_connection_error(self, client):
        mock_resp = self._mock_response()
        call_count = 0

        async def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APIConnectionError(request=_make_httpx_request())
            return mock_resp

        client._client.messages.create = AsyncMock(side_effect=side_effect)

        text, usage = await client._call(
            system="sys", user="msg", model=MODEL_SONNET, max_tokens=100
        )
        assert call_count == 2

    async def test_call_max_retries_exceeded(self, client):
        async def side_effect(**kwargs):
            raise RateLimitError(
                message="rate limited",
                response=_make_httpx_response(429),
                body=None,
            )

        client._client.messages.create = AsyncMock(side_effect=side_effect)

        with pytest.raises(ClaudeError, match="Max retries exceeded"):
            await client._call(
                system="sys", user="msg", model=MODEL_SONNET, max_tokens=100
            )

    async def test_call_non_retryable_error(self, client):
        async def side_effect(**kwargs):
            raise APIStatusError(
                message="invalid api key",
                response=_make_httpx_response(401),
                body=None,
            )

        client._client.messages.create = AsyncMock(side_effect=side_effect)

        with pytest.raises(ClaudeError, match="Claude API error 401"):
            await client._call(
                system="sys", user="msg", model=MODEL_SONNET, max_tokens=100
            )

    async def test_call_logs_token_usage(self, client, caplog):
        mock_resp = self._mock_response(input_tokens=100, output_tokens=50)
        client._client.messages.create = AsyncMock(return_value=mock_resp)

        with caplog.at_level(logging.INFO, logger="src.clients.claude"):
            await client._call(
                system="sys", user="msg", model=MODEL_SONNET, max_tokens=100
            )
        assert "tokens: 100 in, 50 out" in caplog.text


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------


class TestClaudeClientClassify:
    @pytest.fixture
    def client(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            yield ClaudeClient()

    async def test_classify_returns_parsed_json(self, client):
        json_text = '{"category": "aggro", "confidence": 0.95}'
        mock_usage = TokenUsage(input_tokens=50, output_tokens=20)
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            return_value=(json_text, mock_usage),
        ):
            result = await client.classify(
                system="Classify this deck.",
                user="4x Charizard ex, 4x Rare Candy...",
            )
            assert result == {"category": "aggro", "confidence": 0.95}

    async def test_classify_uses_haiku_by_default(self, client):
        json_text = '{"type": "control"}'
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            return_value=(json_text, mock_usage),
        ) as mock_call:
            await client.classify(system="sys", user="msg")
            mock_call.assert_called_once_with(
                system="sys",
                user="msg",
                model=MODEL_HAIKU,
                max_tokens=1024,
            )

    async def test_classify_strips_markdown_fences(self, client):
        json_text = '```json\n{"category": "combo"}\n```'
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            return_value=(json_text, mock_usage),
        ):
            result = await client.classify(system="sys", user="msg")
            assert result == {"category": "combo"}

    async def test_classify_invalid_json_raises(self, client):
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with (
            patch.object(
                client,
                "_call",
                new_callable=AsyncMock,
                return_value=("not json", mock_usage),
            ),
            pytest.raises(ClaudeError, match="Failed to parse JSON"),
        ):
            await client.classify(system="sys", user="msg")


# ---------------------------------------------------------------------------
# generate()
# ---------------------------------------------------------------------------


class TestClaudeClientGenerate:
    @pytest.fixture
    def client(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            yield ClaudeClient()

    async def test_generate_returns_text(self, client):
        mock_usage = TokenUsage(input_tokens=50, output_tokens=200)
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            return_value=("Generated article.", mock_usage),
        ):
            result = await client.generate(
                system="Write an article.",
                user="Topic: meta analysis",
            )
            assert result == "Generated article."

    async def test_generate_uses_sonnet_by_default(self, client):
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with patch.object(
            client, "_call", new_callable=AsyncMock, return_value=("text", mock_usage)
        ) as mock_call:
            await client.generate(system="sys", user="msg")
            mock_call.assert_called_once_with(
                system="sys",
                user="msg",
                model=MODEL_SONNET,
                max_tokens=4096,
            )

    async def test_generate_custom_model_and_tokens(self, client):
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with patch.object(
            client, "_call", new_callable=AsyncMock, return_value=("text", mock_usage)
        ) as mock_call:
            await client.generate(
                system="sys", user="msg", model=MODEL_HAIKU, max_tokens=512
            )
            mock_call.assert_called_once_with(
                system="sys",
                user="msg",
                model=MODEL_HAIKU,
                max_tokens=512,
            )


# ---------------------------------------------------------------------------
# translate()
# ---------------------------------------------------------------------------


class TestClaudeClientTranslate:
    @pytest.fixture
    def client(self):
        with patch("src.clients.claude.get_settings") as mock_settings:
            mock_settings.return_value.anthropic_api_key = "sk-ant-test"
            yield ClaudeClient()

    async def test_translate_returns_translation_result(self, client):
        json_response = json.dumps(
            {
                "translated_text": "Charizard ex deck wins tournament",
                "glossary_terms_used": ["ex"],
                "confidence": "high",
            }
        )
        mock_usage = TokenUsage(input_tokens=100, output_tokens=50)
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            return_value=(json_response, mock_usage),
        ):
            result = await client.translate(
                text="\u30ea\u30b6\u30fc\u30c9\u30f3ex\u30c7\u30c3\u30ad\u304c\u5927\u4f1a\u3067\u512a\u52dd",
                context="Pokemon TCG tournament report",
                glossary={"\u30ea\u30b6\u30fc\u30c9\u30f3": "Charizard", "ex": "ex"},
            )
            assert isinstance(result, TranslationResult)
            assert result.translated_text == "Charizard ex deck wins tournament"
            assert result.glossary_terms_used == ["ex"]
            assert result.confidence == "high"

    async def test_translate_builds_system_prompt_with_glossary(self, client):
        json_response = json.dumps(
            {
                "translated_text": "text",
                "glossary_terms_used": [],
                "confidence": "medium",
            }
        )
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            return_value=(json_response, mock_usage),
        ) as mock_call:
            await client.translate(
                text="\u30c6\u30b9\u30c8",
                context="test context",
                glossary={"\u30c6\u30b9\u30c8": "test"},
            )
            call_kwargs = mock_call.call_args
            system_prompt = call_kwargs.kwargs["system"]
            assert "\u30c6\u30b9\u30c8" in system_prompt
            assert "test" in system_prompt

    async def test_translate_empty_glossary(self, client):
        json_response = json.dumps(
            {
                "translated_text": "translated",
                "glossary_terms_used": [],
                "confidence": "high",
            }
        )
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with patch.object(
            client,
            "_call",
            new_callable=AsyncMock,
            return_value=(json_response, mock_usage),
        ):
            result = await client.translate(text="\u30c6\u30b9\u30c8", context="ctx")
            assert result.translated_text == "translated"

    async def test_translate_invalid_json_raises(self, client):
        mock_usage = TokenUsage(input_tokens=10, output_tokens=5)
        with (
            patch.object(
                client,
                "_call",
                new_callable=AsyncMock,
                return_value=("bad json", mock_usage),
            ),
            pytest.raises(ClaudeError, match="Failed to parse translation"),
        ):
            await client.translate(text="\u30c6\u30b9\u30c8", context="ctx")
