"""Tests for the EvolutionArticleGenerator."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.clients.claude import ClaudeError
from src.models.adaptation import Adaptation
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.evolution_article import EvolutionArticle
from src.models.lab_note import LabNote
from src.services.evolution_article_generator import (
    ArticleGeneratorError,
    EvolutionArticleGenerator,
)

_UNSET = object()


def _make_execute_result(*, scalar_one_or_none=_UNSET, scalars_all=_UNSET):
    """Create a mock result from session.execute()."""
    mock_result = MagicMock()
    if scalar_one_or_none is not _UNSET:
        mock_result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not _UNSET:
        mock_result.scalars.return_value.all.return_value = scalars_all
    return mock_result


def _make_snapshot(**kwargs) -> MagicMock:
    """Create a mock ArchetypeEvolutionSnapshot."""
    mock = MagicMock(spec=ArchetypeEvolutionSnapshot)
    mock.id = kwargs.get("id", uuid4())
    mock.archetype = kwargs.get("archetype", "Charizard ex")
    mock.meta_share = kwargs.get("meta_share", 0.12)
    mock.top_cut_conversion = kwargs.get("top_cut_conversion", 0.35)
    mock.best_placement = kwargs.get("best_placement", 2)
    mock.deck_count = kwargs.get("deck_count", 8)
    mock.meta_context = kwargs.get("meta_context")
    return mock


def _make_adaptation(**kwargs) -> MagicMock:
    """Create a mock Adaptation."""
    mock = MagicMock(spec=Adaptation)
    mock.type = kwargs.get("type", "tech")
    mock.description = kwargs.get("description", "Added Drapion V")
    mock.cards_added = kwargs.get("cards_added", [{"name": "Drapion V", "quantity": 1}])
    mock.cards_removed = kwargs.get("cards_removed")
    return mock


class TestGenerateArticle:
    """Tests for article generation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def generator(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> EvolutionArticleGenerator:
        return EvolutionArticleGenerator(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_generates_article(
        self,
        generator: EvolutionArticleGenerator,
        mock_session: AsyncMock,
        mock_claude: AsyncMock,
    ) -> None:
        """Should generate an article with title, intro, conclusion."""
        snapshots = [_make_snapshot() for _ in range(3)]
        adaptations = [_make_adaptation()]

        mock_claude.classify.return_value = {
            "title": "Charizard ex: Adapting to the New Meta",
            "excerpt": "How Charizard ex evolved through recent tournaments.",
            "introduction": "Charizard ex has undergone significant changes.",
            "conclusion": "Looking ahead, Charizard ex remains a top contender.",
        }

        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=snapshots),  # snapshots
            _make_execute_result(scalars_all=adaptations),  # adaptations
            _make_execute_result(scalar_one_or_none=None),  # no prediction
        ]

        article = await generator.generate_article("Charizard ex")

        assert isinstance(article, EvolutionArticle)
        assert article.archetype_id == "Charizard ex"
        assert article.title == "Charizard ex: Adapting to the New Meta"
        assert article.excerpt is not None
        assert article.introduction is not None
        assert article.conclusion is not None
        assert article.status == "draft"
        assert "charizard-ex" in article.slug

    @pytest.mark.asyncio
    async def test_raises_when_no_snapshots(
        self,
        generator: EvolutionArticleGenerator,
        mock_session: AsyncMock,
    ) -> None:
        """Should raise ArticleGeneratorError when no snapshots found."""
        mock_session.execute.return_value = _make_execute_result(scalars_all=[])

        with pytest.raises(ArticleGeneratorError, match="No snapshots"):
            await generator.generate_article("Unknown Archetype")

    @pytest.mark.asyncio
    async def test_raises_on_claude_error(
        self,
        generator: EvolutionArticleGenerator,
        mock_session: AsyncMock,
        mock_claude: AsyncMock,
    ) -> None:
        """Should raise ArticleGeneratorError on Claude failure."""
        snapshots = [_make_snapshot()]

        mock_claude.classify.side_effect = ClaudeError("API error")

        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=snapshots),
            _make_execute_result(scalars_all=[]),  # no adaptations
            _make_execute_result(scalar_one_or_none=None),  # no prediction
        ]

        with pytest.raises(ArticleGeneratorError, match="Failed to generate"):
            await generator.generate_article("Charizard ex")

    @pytest.mark.asyncio
    async def test_includes_prediction_context(
        self,
        generator: EvolutionArticleGenerator,
        mock_session: AsyncMock,
        mock_claude: AsyncMock,
    ) -> None:
        """Should include prediction data when available."""
        snapshots = [_make_snapshot()]
        prediction = MagicMock(spec=ArchetypePrediction)
        prediction.predicted_tier = "S"
        prediction.predicted_meta_share = {"mid": 0.15}
        prediction.methodology = "Strong trajectory."
        prediction.created_at = datetime.now(UTC)

        mock_claude.classify.return_value = {
            "title": "Charizard ex Evolution",
            "introduction": "Intro text.",
            "conclusion": "Conclusion text.",
        }

        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=snapshots),  # snapshots
            _make_execute_result(scalars_all=[]),  # no adaptations
            _make_execute_result(scalar_one_or_none=prediction),  # prediction
        ]

        article = await generator.generate_article("Charizard ex")
        assert article.title == "Charizard ex Evolution"

        call_args = mock_claude.classify.call_args
        assert "Strong trajectory" in call_args.kwargs["user"]


class TestLinkSnapshots:
    """Tests for snapshot linking."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def generator(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> EvolutionArticleGenerator:
        return EvolutionArticleGenerator(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_creates_junction_records(
        self, generator: EvolutionArticleGenerator
    ) -> None:
        """Should create EvolutionArticleSnapshot records with positions."""
        article = MagicMock(spec=EvolutionArticle)
        article.id = uuid4()

        ids = [uuid4(), uuid4(), uuid4()]
        links = await generator.link_snapshots(article, ids)

        assert len(links) == 3
        assert links[0].article_id == article.id
        assert links[0].snapshot_id == ids[0]
        assert links[0].position == 0
        assert links[1].position == 1
        assert links[2].position == 2


class TestPublishArticle:
    """Tests for article publishing."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def generator(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> EvolutionArticleGenerator:
        return EvolutionArticleGenerator(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_publishes_and_creates_lab_note(
        self,
        generator: EvolutionArticleGenerator,
        mock_session: AsyncMock,
    ) -> None:
        """Should set published status and create a LabNote."""
        article = MagicMock(spec=EvolutionArticle)
        article.id = uuid4()
        article.archetype_id = "Charizard ex"
        article.slug = "charizard-ex-evolution-20260203"
        article.title = "Charizard ex Evolution"
        article.excerpt = "How Charizard adapted."
        article.introduction = "Intro."
        article.conclusion = "Conclusion."

        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=article
        )

        lab_note = await generator.publish_article(article.id)

        assert article.status == "published"
        assert article.published_at is not None
        assert lab_note is not None
        assert isinstance(lab_note, LabNote)
        assert lab_note.note_type == "archetype_evolution"
        assert lab_note.title == "Charizard ex Evolution"
        assert lab_note.is_published is True
        assert "evolution" in lab_note.tags
        mock_session.add.assert_called_once_with(lab_note)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_article_not_found(
        self,
        generator: EvolutionArticleGenerator,
        mock_session: AsyncMock,
    ) -> None:
        """Should return None when article doesn't exist."""
        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=None
        )

        result = await generator.publish_article(uuid4())
        assert result is None


class TestGenerateSlug:
    """Tests for slug generation."""

    @pytest.fixture
    def generator(self) -> EvolutionArticleGenerator:
        return EvolutionArticleGenerator(AsyncMock(), AsyncMock())

    def test_generates_valid_slug(self, generator: EvolutionArticleGenerator) -> None:
        """Should produce a URL-safe slug."""
        slug = generator._generate_slug("Charizard ex")
        assert "charizard-ex" in slug
        assert "evolution" in slug
        # Should not contain special characters
        assert " " not in slug
        assert slug == slug.lower()

    def test_handles_special_characters(
        self, generator: EvolutionArticleGenerator
    ) -> None:
        """Should strip special characters from slug."""
        slug = generator._generate_slug("Lugia VSTAR/Archeops")
        assert (
            "lugia-vstararcheops" in slug
            or "lugia-vstar" in slug.split("-evolution")[0]
        )
