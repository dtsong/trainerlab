"""Async client for Claude API (Anthropic SDK)."""

import asyncio
import json
import logging
import secrets
from dataclasses import dataclass, field
from typing import Any, Self

import anthropic
from anthropic import APIConnectionError, APIStatusError, RateLimitError
from anthropic.types import TextBlock

from src.config import get_settings

logger = logging.getLogger(__name__)

MODEL_SONNET = "claude-sonnet-4-5-20250929"
MODEL_HAIKU = "claude-haiku-4-5-20251001"


class ClaudeError(Exception):
    """Exception raised for Claude API errors."""


@dataclass
class TokenUsage:
    """Token usage for a single API call."""

    input_tokens: int
    output_tokens: int

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class TranslationResult:
    """Structured result from translate() method."""

    translated_text: str
    confidence: str
    glossary_terms_used: list[str] = field(default_factory=list)


class ClaudeClient:
    """Async client for Claude API."""

    def __init__(
        self,
        max_retries: int = 5,
        retry_delay: float = 5.0,
        timeout: float = 60.0,
    ):
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ClaudeError(
                "ANTHROPIC_API_KEY is not configured. "
                "Set it in environment or .env file."
            )

        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=timeout,
        )

    async def __aenter__(self) -> Self:
        """Enter async context."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context and close client."""
        await self.close()

    async def close(self) -> None:
        """Close the Anthropic client."""
        await self._client.close()

    async def _call(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
    ) -> tuple[str, TokenUsage]:
        """Make a Claude API call with retry logic.

        Returns:
            Tuple of (response text, token usage).

        Raises:
            ClaudeError: On API error after retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = await self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )

                usage = TokenUsage(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
                logger.info(
                    "Claude API call (%s): tokens: %d in, %d out",
                    model,
                    usage.input_tokens,
                    usage.output_tokens,
                )

                block = response.content[0]
                if not isinstance(block, TextBlock):
                    msg = f"Expected TextBlock, got {type(block)}"
                    raise TypeError(msg)
                text = block.text
                return text, usage

            except RateLimitError as e:
                jitter = secrets.randbelow(int(self._retry_delay * 1000)) / 1000
                delay = self._retry_delay * (2**attempt) + jitter
                logger.warning(
                    "Claude rate limited, retrying in %.1fs (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    self._max_retries,
                )
                await asyncio.sleep(delay)
                last_error = e

            except APIConnectionError as e:
                jitter = secrets.randbelow(int(self._retry_delay * 1000)) / 1000
                delay = self._retry_delay * (2**attempt) + jitter
                logger.warning(
                    "Claude connection error, retrying in %.1fs (attempt %d/%d): %s",
                    delay,
                    attempt + 1,
                    self._max_retries,
                    e,
                )
                await asyncio.sleep(delay)
                last_error = e

            except APIStatusError as e:
                raise ClaudeError(
                    f"Claude API error {e.status_code}: {e.message}"
                ) from e

        raise ClaudeError("Max retries exceeded for Claude API call") from last_error

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        """Strip markdown code fences from text if present."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]).strip()
        return cleaned

    async def classify(
        self,
        system: str,
        user: str,
        model: str = MODEL_HAIKU,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Classify input and return structured JSON.

        Uses Haiku by default for speed/cost.

        Returns:
            Parsed JSON dict from Claude's response.

        Raises:
            ClaudeError: On API or JSON parse error.
        """
        text, _usage = await self._call(
            system=system, user=user, model=model, max_tokens=max_tokens
        )

        cleaned = self._strip_code_fences(text)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ClaudeError(f"Failed to parse JSON from Claude response: {e}") from e

    async def generate(
        self,
        system: str,
        user: str,
        model: str = MODEL_SONNET,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text content.

        Uses Sonnet by default.

        Returns:
            Generated text.

        Raises:
            ClaudeError: On API error.
        """
        text, _usage = await self._call(
            system=system, user=user, model=model, max_tokens=max_tokens
        )
        return text

    async def translate(
        self,
        text: str,
        context: str,
        glossary: dict[str, str] | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        content_type: str | None = None,
    ) -> TranslationResult:
        """Translate Japanese text to English with domain glossary.

        Args:
            text: Japanese text to translate.
            context: Context for the translation.
            glossary: Optional {jp: en} glossary dict.
            model: Claude model to use. Auto-selected from
                content_type if None.
            max_tokens: Max response tokens.
            content_type: "tier_list" or "article" for
                content-specific instructions and model
                selection.

        Returns:
            TranslationResult with translated text and metadata.

        Raises:
            ClaudeError: On API or parse error.
        """
        # Auto-select model from content_type when not
        # explicitly provided
        if model is None:
            model = MODEL_HAIKU if content_type == "tier_list" else MODEL_SONNET

        content_instruction = ""
        if content_type == "tier_list":
            content_instruction = (
                " Preserve tier designations (S/A/B/C),"
                " numerical data, and percentage values"
                " exactly as written."
            )
        elif content_type == "article":
            content_instruction = (
                " Preserve strategic reasoning and analysis structure."
            )

        glossary_section = ""
        if glossary:
            terms = "\n".join(f"- {jp} \u2192 {en}" for jp, en in glossary.items())
            glossary_section = f"\n\nGlossary (use these exact translations):\n{terms}"

        system_prompt = (
            "You are a Japanese-to-English translator"
            " specializing in Pokemon TCG content."
            " Translate accurately, preserving game"
            " terminology. Return JSON with keys:"
            " translated_text (string),"
            " glossary_terms_used (list of glossary"
            " terms you applied), confidence"
            ' ("high", "medium", or "low").'
            f"{content_instruction}{glossary_section}"
        )

        user_prompt = f"Context: {context}\n\nTranslate:\n{text}"

        raw, _usage = await self._call(
            system=system_prompt,
            user=user_prompt,
            model=model,
            max_tokens=max_tokens,
        )

        cleaned = self._strip_code_fences(raw)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ClaudeError(f"Failed to parse translation response JSON: {e}") from e

        if "translated_text" not in data:
            raise ClaudeError("Translation response missing 'translated_text' key")

        return TranslationResult(
            translated_text=data["translated_text"],
            glossary_terms_used=data.get("glossary_terms_used", []),
            confidence=data.get("confidence", "medium"),
        )
