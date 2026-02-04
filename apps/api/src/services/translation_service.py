"""Translation service with 3-layer architecture.

Layer 1: Deterministic - exact glossary matches (free, instant)
Layer 2: Template - structured patterns like tournament results
Layer 3: Claude - full AI translation with glossary context
"""

import logging
import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.claude import ClaudeClient
from src.data.tcg_glossary import TCG_GLOSSARY, get_claude_glossary
from src.models.translated_content import TranslatedContent
from src.models.translation_term_override import TranslationTermOverride
from src.schemas.translation import (
    ArticleTranslationRequest,
    ArticleTranslationResponse,
    BatchTranslationItem,
    BatchTranslationResponse,
    BatchTranslationResult,
    ContentType,
    TournamentStandingRow,
    TournamentStandingsTranslation,
    TranslationResponse,
)

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """Raised when translation fails."""


class TranslationService:
    """3-layer translation service for Japanese TCG content."""

    PLACEMENT_PATTERN = re.compile(
        r"^(\d+)[位番]?[：:]?\s*(.+?)(?:\s*[\(（](\d+-\d+(?:-\d+)?)[\)）])?$"
    )
    TOURNAMENT_HEADER_PATTERN = re.compile(
        r"(?:シティリーグ|チャンピオンズリーグ|ジムバトル).*?(\d+)名"
    )

    def __init__(
        self,
        db: AsyncSession,
        claude_client: ClaudeClient | None = None,
    ) -> None:
        self.db = db
        self._claude = claude_client
        self._merged_glossary: dict[str, str] | None = None

    async def _get_merged_glossary(self) -> dict[str, str]:
        """Get glossary merged with DB overrides (overrides take precedence)."""
        if self._merged_glossary is not None:
            return self._merged_glossary

        glossary = get_claude_glossary()

        try:
            query = select(TranslationTermOverride).where(
                TranslationTermOverride.is_active == True  # noqa: E712
            )
            result = await self.db.execute(query)
            overrides = result.scalars().all()

            for override in overrides:
                glossary[override.term_jp] = override.term_en

        except SQLAlchemyError as e:
            logger.warning(
                "Failed to load term overrides, using static glossary: %s", e
            )

        self._merged_glossary = glossary
        return glossary

    def _layer1_glossary_translate(
        self, text: str, glossary: dict[str, str]
    ) -> tuple[str, list[str]]:
        """Layer 1: Replace exact glossary matches."""
        translated = text
        terms_used = []

        for jp_term, en_term in sorted(
            glossary.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if jp_term in translated:
                translated = translated.replace(jp_term, en_term)
                terms_used.append(jp_term)

        return translated, terms_used

    def _layer2_tournament_standings(
        self, text: str, glossary: dict[str, str]
    ) -> TournamentStandingsTranslation | None:
        """Layer 2: Parse tournament standings format."""
        lines = text.strip().split("\n")
        standings: list[TournamentStandingRow] = []
        event_name_jp = None
        event_name_en = None
        participant_count = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            header_match = self.TOURNAMENT_HEADER_PATTERN.search(line)
            if header_match:
                participant_count = int(header_match.group(1))
                event_name_jp = line
                event_name_en, _ = self._layer1_glossary_translate(line, glossary)
                continue

            match = self.PLACEMENT_PATTERN.match(line)
            if match:
                placement = int(match.group(1))
                deck_name_jp = match.group(2).strip()
                record = match.group(3)

                deck_name_en, _ = self._layer1_glossary_translate(
                    deck_name_jp, glossary
                )

                standings.append(
                    TournamentStandingRow(
                        placement=placement,
                        deck_name_jp=deck_name_jp,
                        deck_name_en=deck_name_en,
                        record=record,
                    )
                )

        if not standings:
            return None

        return TournamentStandingsTranslation(
            event_name_jp=event_name_jp,
            event_name_en=event_name_en,
            standings=standings,
            participant_count=participant_count,
        )

    def _is_fully_translated(self, text: str) -> bool:
        """Check if text contains significant Japanese characters."""

        def is_jp_char(c: str) -> bool:
            return (
                "\u3040" <= c <= "\u309f"  # Hiragana
                or "\u30a0" <= c <= "\u30ff"  # Katakana
                or "\u4e00" <= c <= "\u9fff"  # Kanji
            )

        jp_chars = sum(1 for c in text if is_jp_char(c))
        return jp_chars < len(text) * 0.1

    async def translate(
        self,
        text: str,
        content_type: ContentType,
        context: str | None = None,
    ) -> TranslationResponse:
        """Translate Japanese text using 3-layer architecture."""
        glossary = await self._get_merged_glossary()

        layer1_result, terms_used = self._layer1_glossary_translate(text, glossary)

        if self._is_fully_translated(layer1_result):
            return TranslationResponse(
                original_text=text,
                translated_text=layer1_result,
                layer_used="glossary",
                confidence="high",
                glossary_terms_used=terms_used,
                uncertainties=[],
            )

        if content_type == "tournament_result":
            standings = self._layer2_tournament_standings(text, glossary)
            if standings and standings.standings:
                formatted = self._format_standings(standings)
                return TranslationResponse(
                    original_text=text,
                    translated_text=formatted,
                    layer_used="template",
                    confidence="high",
                    glossary_terms_used=terms_used,
                    uncertainties=[],
                )

        if self._claude is None:
            return TranslationResponse(
                original_text=text,
                translated_text=layer1_result,
                layer_used="glossary",
                confidence="low",
                glossary_terms_used=terms_used,
                uncertainties=["Claude client not available for full translation"],
            )

        try:
            claude_result = await self._claude.translate(
                text=text,
                context=context or f"Pokemon TCG {content_type}",
                glossary=glossary,
            )
            return TranslationResponse(
                original_text=text,
                translated_text=claude_result.translated_text,
                layer_used="claude",
                confidence=claude_result.confidence,  # type: ignore[arg-type]
                glossary_terms_used=claude_result.glossary_terms_used,
                uncertainties=[],
            )
        except Exception as e:
            logger.error("Claude translation failed: %s", e)
            return TranslationResponse(
                original_text=text,
                translated_text=layer1_result,
                layer_used="glossary",
                confidence="low",
                glossary_terms_used=terms_used,
                uncertainties=[f"Claude translation failed: {e}"],
            )

    def _format_standings(self, standings: TournamentStandingsTranslation) -> str:
        """Format standings into readable text."""
        lines = []

        if standings.event_name_en:
            header = standings.event_name_en
            if standings.participant_count:
                header += f" ({standings.participant_count} players)"
            lines.append(header)
            lines.append("")

        for row in standings.standings:
            line = f"{row.placement}. {row.deck_name_en}"
            if row.record:
                line += f" ({row.record})"
            lines.append(line)

        return "\n".join(lines)

    async def translate_article(
        self, request: ArticleTranslationRequest
    ) -> ArticleTranslationResponse:
        """Translate and persist an article."""
        try:
            existing_query = select(TranslatedContent).where(
                TranslatedContent.source_id == request.source_id,
                TranslatedContent.source_url == request.source_url,
            )
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()

            if existing and existing.status == "completed":
                return ArticleTranslationResponse(
                    id=str(existing.id),
                    source_id=existing.source_id,
                    source_url=existing.source_url,
                    original_text=existing.original_text,
                    translated_text=existing.translated_text,
                    status="completed",
                    translated_at=existing.translated_at,
                    uncertainties=(
                        list(existing.uncertainties) if existing.uncertainties else []
                    ),
                )

            translation = await self.translate(
                text=request.original_text,
                content_type=request.content_type,
                context=request.context,
            )

            content_id = existing.id if existing else uuid4()

            if existing:
                existing.translated_text = translation.translated_text
                existing.status = "completed"
                existing.translated_at = datetime.now(UTC)
                existing.uncertainties = translation.uncertainties or None
            else:
                new_content = TranslatedContent(
                    id=content_id,
                    source_id=request.source_id,
                    source_url=request.source_url,
                    content_type=request.content_type,
                    original_text=request.original_text,
                    translated_text=translation.translated_text,
                    status="completed",
                    translated_at=datetime.now(UTC),
                    uncertainties=translation.uncertainties or None,
                )
                self.db.add(new_content)

            await self.db.commit()

            return ArticleTranslationResponse(
                id=str(content_id),
                source_id=request.source_id,
                source_url=request.source_url,
                original_text=request.original_text,
                translated_text=translation.translated_text,
                status="completed",
                translated_at=datetime.now(UTC),
                uncertainties=translation.uncertainties,
            )

        except SQLAlchemyError as e:
            logger.error("Database error in translate_article: %s", e)
            await self.db.rollback()
            raise TranslationError("Failed to persist translation") from e

    async def batch_translate(
        self, items: list[BatchTranslationItem]
    ) -> BatchTranslationResponse:
        """Translate multiple items."""
        results: list[BatchTranslationResult] = []
        layer_counts: dict[str, int] = {"glossary": 0, "template": 0, "claude": 0}

        for item in items:
            translation = await self.translate(
                text=item.text,
                content_type=item.content_type,
                context=item.context,
            )

            results.append(
                BatchTranslationResult(
                    id=item.id,
                    translated_text=translation.translated_text,
                    layer_used=translation.layer_used,
                    confidence=translation.confidence,
                )
            )
            layer_counts[translation.layer_used] += 1

        return BatchTranslationResponse(
            results=results,
            total=len(items),
            layer_breakdown=layer_counts,
        )

    def get_glossary_stats(self) -> dict[str, int]:
        """Get glossary statistics by category."""
        stats: dict[str, int] = {}
        for entry in TCG_GLOSSARY.values():
            stats[entry.category] = stats.get(entry.category, 0) + 1
        return stats
