"""Tests for translation service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.clients.claude import ClaudeClient, TranslationResult
from src.models.translated_content import TranslatedContent
from src.schemas.translation import (
    ArticleTranslationRequest,
    BatchTranslationItem,
)
from src.services.translation_service import TranslationError, TranslationService


class TestLayer1GlossaryTranslate:
    """Tests for layer 1 glossary translation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    def test_replaces_exact_matches(self, service: TranslationService) -> None:
        glossary = {"リザードンex": "Charizard ex", "ルギアVSTAR": "Lugia VSTAR"}
        text = "リザードンexとルギアVSTARは強い"

        result, terms_used = service._layer1_glossary_translate(text, glossary)

        assert "Charizard ex" in result
        assert "Lugia VSTAR" in result
        assert "リザードンex" in terms_used
        assert "ルギアVSTAR" in terms_used

    def test_replaces_longer_terms_first(self, service: TranslationService) -> None:
        glossary = {"リザードン": "Charizard", "リザードンex": "Charizard ex"}
        text = "リザードンexは強い"

        result, terms_used = service._layer1_glossary_translate(text, glossary)

        assert result == "Charizard exは強い"
        assert "リザードンex" in terms_used

    def test_returns_empty_terms_when_no_matches(
        self, service: TranslationService
    ) -> None:
        glossary = {"リザードンex": "Charizard ex"}
        text = "Hello world"

        result, terms_used = service._layer1_glossary_translate(text, glossary)

        assert result == "Hello world"
        assert terms_used == []


class TestLayer2TournamentStandings:
    """Tests for layer 2 tournament standings parsing."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    def test_parses_tournament_standings(self, service: TranslationService) -> None:
        glossary = {"リザードンex": "Charizard ex", "ルギアVSTAR": "Lugia VSTAR"}
        text = """シティリーグ 東京 32名
1位: リザードンex (4-0-1)
2位: ルギアVSTAR (4-1)"""

        result = service._layer2_tournament_standings(text, glossary)

        assert result is not None
        assert result.participant_count == 32
        assert len(result.standings) == 2
        assert result.standings[0].placement == 1
        assert result.standings[0].deck_name_en == "Charizard ex"
        assert result.standings[0].record == "4-0-1"

    def test_returns_none_when_no_standings(self, service: TranslationService) -> None:
        glossary = {}
        text = "This is just regular text without standings."

        result = service._layer2_tournament_standings(text, glossary)

        assert result is None

    def test_handles_placement_without_record(
        self, service: TranslationService
    ) -> None:
        glossary = {"リザードンex": "Charizard ex"}
        text = """1位: リザードンex"""

        result = service._layer2_tournament_standings(text, glossary)

        assert result is not None
        assert result.standings[0].record is None


class TestIsFullyTranslated:
    """Tests for checking translation completeness."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    def test_returns_true_for_mostly_english(self, service: TranslationService) -> None:
        text = "This is mostly English with just a few words"
        assert service._is_fully_translated(text) is True

    def test_returns_false_for_mostly_japanese(
        self, service: TranslationService
    ) -> None:
        text = "これは日本語のテキストです"
        assert service._is_fully_translated(text) is False

    def test_threshold_at_10_percent(self, service: TranslationService) -> None:
        text = "A" * 90 + "あ" * 9  # 9% Japanese
        assert service._is_fully_translated(text) is True

        text = "A" * 89 + "あ" * 11  # 11% Japanese
        assert service._is_fully_translated(text) is False


class TestTranslate:
    """Tests for the main translate method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    @pytest.mark.asyncio
    async def test_uses_glossary_only_when_fully_translated(
        self, service: TranslationService
    ) -> None:
        text = "The Charizard ex deck won"  # English text

        result = await service.translate(text, content_type="article")

        assert result.layer_used == "glossary"
        assert result.confidence == "high"

    @pytest.mark.asyncio
    async def test_uses_template_for_tournament_results(
        self, mock_session: AsyncMock
    ) -> None:
        service = TranslationService(mock_session)
        text = """シティリーグ 東京 32名
1位: リザードンex (4-0)"""

        # Mock _get_merged_glossary to return a glossary with the deck name
        service._merged_glossary = {"リザードンex": "Charizard ex"}

        result = await service.translate(text, content_type="tournament_result")

        assert result.layer_used == "template"
        assert result.confidence == "high"

    @pytest.mark.asyncio
    async def test_returns_low_confidence_when_claude_unavailable(
        self, mock_session: AsyncMock
    ) -> None:
        service = TranslationService(mock_session, claude_client=None)
        text = "これは日本語のテキストです"

        result = await service.translate(text, content_type="article")

        assert result.layer_used == "glossary"
        assert result.confidence == "low"
        assert "Claude client not available" in result.uncertainties[0]

    @pytest.mark.asyncio
    async def test_uses_claude_for_complex_text(self, mock_session: AsyncMock) -> None:
        mock_claude = AsyncMock(spec=ClaudeClient)
        mock_claude.translate.return_value = TranslationResult(
            translated_text="This is a translated article",
            confidence="high",
            glossary_terms_used=["term1"],
        )

        service = TranslationService(mock_session, claude_client=mock_claude)
        text = "これは日本語のテキストです"

        result = await service.translate(text, content_type="article")

        assert result.layer_used == "claude"
        mock_claude.translate.assert_called_once()

    @pytest.mark.asyncio
    async def test_falls_back_on_claude_error(self, mock_session: AsyncMock) -> None:
        mock_claude = AsyncMock(spec=ClaudeClient)
        mock_claude.translate.side_effect = Exception("API error")

        service = TranslationService(mock_session, claude_client=mock_claude)
        text = "これは日本語のテキストです"

        result = await service.translate(text, content_type="article")

        assert result.layer_used == "glossary"
        assert result.confidence == "low"
        assert "Claude translation failed" in result.uncertainties[0]


class TestTranslateArticle:
    """Tests for article translation with persistence."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    @pytest.mark.asyncio
    async def test_returns_existing_completed_translation(
        self, service: TranslationService, mock_session: AsyncMock
    ) -> None:
        existing = TranslatedContent(
            id=uuid4(),
            source_id="src-1",
            source_url="https://example.com/article",
            content_type="article",
            original_text="Original text",
            translated_text="Translated text",
            status="completed",
            translated_at=datetime.now(UTC),
            uncertainties=None,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        request = ArticleTranslationRequest(
            source_id="src-1",
            source_url="https://example.com/article",
            original_text="Original text",
            content_type="article",
        )

        result = await service.translate_article(request)

        assert result.status == "completed"
        assert result.translated_text == "Translated text"
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_new_translation(self, mock_session: AsyncMock) -> None:
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        mock_glossary_result = MagicMock()
        mock_glossary_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            mock_existing_result,
            mock_glossary_result,
        ]

        service = TranslationService(mock_session)

        request = ArticleTranslationRequest(
            source_id="src-new",
            source_url="https://example.com/new-article",
            original_text="Hello world",  # English, should use glossary layer
            content_type="article",
        )

        result = await service.translate_article(request)

        assert result.status == "completed"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_database_error(
        self, service: TranslationService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        request = ArticleTranslationRequest(
            source_id="src-1",
            source_url="https://example.com/article",
            original_text="Text",
            content_type="article",
        )

        with pytest.raises(TranslationError, match="Failed to persist translation"):
            await service.translate_article(request)


class TestBatchTranslate:
    """Tests for batch translation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    @pytest.mark.asyncio
    async def test_translates_multiple_items(self, service: TranslationService) -> None:
        items = [
            BatchTranslationItem(id="1", text="Hello world", content_type="article"),
            BatchTranslationItem(id="2", text="Testing", content_type="article"),
        ]

        result = await service.batch_translate(items)

        assert result.total == 2
        assert len(result.results) == 2
        assert result.layer_breakdown["glossary"] == 2

    @pytest.mark.asyncio
    async def test_tracks_layer_breakdown(self, service: TranslationService) -> None:
        items = [
            BatchTranslationItem(id="1", text="Hello", content_type="article"),
        ]

        result = await service.batch_translate(items)

        assert "glossary" in result.layer_breakdown


class TestGetGlossaryStats:
    """Tests for glossary statistics."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    def test_returns_category_counts(self, service: TranslationService) -> None:
        stats = service.get_glossary_stats()

        assert isinstance(stats, dict)
        # At least some categories should exist
        total = sum(stats.values())
        assert total > 0


class TestGetMergedGlossary:
    """Tests for merged glossary with DB overrides."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> TranslationService:
        return TranslationService(mock_session)

    @pytest.mark.asyncio
    async def test_merges_db_overrides(
        self, service: TranslationService, mock_session: AsyncMock
    ) -> None:
        override = MagicMock()
        override.term_jp = "カスタム"
        override.term_en = "Custom Override"
        override.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [override]
        mock_session.execute.return_value = mock_result

        glossary = await service._get_merged_glossary()

        assert glossary["カスタム"] == "Custom Override"

    @pytest.mark.asyncio
    async def test_caches_merged_glossary(
        self, service: TranslationService, mock_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await service._get_merged_glossary()
        await service._get_merged_glossary()

        assert mock_session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_handles_db_error_gracefully(
        self, service: TranslationService, mock_session: AsyncMock
    ) -> None:
        mock_session.execute.side_effect = SQLAlchemyError("DB error")

        glossary = await service._get_merged_glossary()

        # Should still return static glossary
        assert isinstance(glossary, dict)
