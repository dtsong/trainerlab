"""Tests for the AdaptationClassifier."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.clients.claude import ClaudeError
from src.models.adaptation import Adaptation
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.meta_snapshot import MetaSnapshot
from src.services.adaptation_classifier import (
    AdaptationClassifier,
    AdaptationClassifierError,
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


def _make_adaptation(**kwargs) -> MagicMock:
    """Create a mock Adaptation."""
    mock = MagicMock(spec=Adaptation)
    mock.type = kwargs.get("type", "tech")
    mock.description = kwargs.get("description", "Added Drapion V")
    mock.cards_added = kwargs.get("cards_added", [{"name": "Drapion V", "quantity": 1}])
    mock.cards_removed = kwargs.get("cards_removed")
    mock.confidence = kwargs.get("confidence")
    mock.prevalence = kwargs.get("prevalence")
    mock.target_archetype = kwargs.get("target_archetype")
    mock.source = kwargs.get("source", "diff")
    mock.snapshot_id = kwargs.get("snapshot_id", uuid4())
    return mock


class TestClassify:
    """Tests for adaptation classification."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def classifier(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> AdaptationClassifier:
        return AdaptationClassifier(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_classifies_adaptation(
        self, classifier: AdaptationClassifier, mock_claude: AsyncMock
    ) -> None:
        """Should update adaptation fields from Claude response."""
        mock_claude.classify.return_value = {
            "type": "tech",
            "description": "Drapion V added to counter Gardevoir ex",
            "target_archetype": "Gardevoir ex",
            "confidence": 0.85,
            "prevalence": 0.6,
        }

        adaptation = _make_adaptation()
        result = await classifier.classify(adaptation)

        assert result.type == "tech"
        assert result.description == "Drapion V added to counter Gardevoir ex"
        assert result.target_archetype == "Gardevoir ex"
        assert result.confidence == 0.85
        assert result.prevalence == 0.6
        assert result.source == "claude"

    @pytest.mark.asyncio
    async def test_classifies_with_meta_context(
        self, classifier: AdaptationClassifier, mock_claude: AsyncMock
    ) -> None:
        """Should pass meta context to Claude."""
        mock_claude.classify.return_value = {
            "type": "consistency",
            "description": "Increased draw support",
            "confidence": 0.7,
            "prevalence": 0.4,
        }

        adaptation = _make_adaptation()
        meta_ctx = {"top_archetypes": {"Charizard ex": 0.15}}
        result = await classifier.classify(adaptation, meta_context=meta_ctx)

        assert result.type == "consistency"
        # Verify Claude was called with meta context in user prompt
        call_args = mock_claude.classify.call_args
        assert "Charizard ex" in call_args.kwargs["user"]

    @pytest.mark.asyncio
    async def test_raises_on_claude_error(
        self, classifier: AdaptationClassifier, mock_claude: AsyncMock
    ) -> None:
        """Should raise AdaptationClassifierError on Claude failure."""
        mock_claude.classify.side_effect = ClaudeError("API error")

        adaptation = _make_adaptation()
        with pytest.raises(AdaptationClassifierError, match="Failed to classify"):
            await classifier.classify(adaptation)


class TestGenerateMetaContext:
    """Tests for meta context generation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def classifier(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> AdaptationClassifier:
        return AdaptationClassifier(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_generates_context_string(
        self, classifier: AdaptationClassifier, mock_claude: AsyncMock
    ) -> None:
        """Should return a context string from Claude."""
        expected = (
            "Charizard ex adapts to the Gardevoir-heavy meta by adding "
            "Drapion V as a tech counter."
        )
        mock_claude.generate.return_value = expected

        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.archetype = "Charizard ex"
        snapshot.meta_share = 0.12
        snapshot.top_cut_conversion = 0.4
        snapshot.best_placement = 2
        snapshot.deck_count = 8

        adaptations = [_make_adaptation()]

        result = await classifier.generate_meta_context(snapshot, adaptations)
        assert result == expected
        mock_claude.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_meta_snapshot_data(
        self, classifier: AdaptationClassifier, mock_claude: AsyncMock
    ) -> None:
        """Should include meta snapshot data when provided."""
        mock_claude.generate.return_value = "Context with meta data."

        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.archetype = "Charizard ex"
        snapshot.meta_share = 0.12
        snapshot.top_cut_conversion = 0.4
        snapshot.best_placement = 2
        snapshot.deck_count = 8

        meta_snapshot = MagicMock(spec=MetaSnapshot)
        meta_snapshot.archetype_shares = {
            "Charizard ex": 0.15,
            "Gardevoir ex": 0.12,
        }
        meta_snapshot.jp_signals = {"rising": ["Dragapult ex"]}
        meta_snapshot.trends = {}

        result = await classifier.generate_meta_context(
            snapshot, [_make_adaptation()], meta_snapshot
        )
        assert result == "Context with meta data."

        call_args = mock_claude.generate.call_args
        assert "Gardevoir ex" in call_args.kwargs["user"]

    @pytest.mark.asyncio
    async def test_raises_on_claude_error(
        self, classifier: AdaptationClassifier, mock_claude: AsyncMock
    ) -> None:
        """Should raise AdaptationClassifierError on Claude failure."""
        mock_claude.generate.side_effect = ClaudeError("API error")

        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.archetype = "Charizard ex"
        snapshot.meta_share = 0.12
        snapshot.top_cut_conversion = 0.4
        snapshot.best_placement = 2
        snapshot.deck_count = 8

        with pytest.raises(AdaptationClassifierError, match="Failed to generate"):
            await classifier.generate_meta_context(snapshot, [_make_adaptation()])


class TestClassifyAndContextualize:
    """Tests for the convenience method."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def classifier(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> AdaptationClassifier:
        return AdaptationClassifier(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_snapshot(
        self,
        classifier: AdaptationClassifier,
        mock_session: AsyncMock,
    ) -> None:
        """Should return None when snapshot not found."""
        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=None
        )

        result = await classifier.classify_and_contextualize(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_adaptations(
        self,
        classifier: AdaptationClassifier,
        mock_session: AsyncMock,
    ) -> None:
        """Should return None when no adaptations exist."""
        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=snapshot),
            _make_execute_result(scalars_all=[]),
        ]

        result = await classifier.classify_and_contextualize(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_classifies_and_generates_context(
        self,
        classifier: AdaptationClassifier,
        mock_session: AsyncMock,
        mock_claude: AsyncMock,
    ) -> None:
        """Should classify adaptations and generate meta context."""
        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.archetype = "Charizard ex"
        snapshot.meta_share = 0.12
        snapshot.top_cut_conversion = 0.4
        snapshot.best_placement = 2
        snapshot.deck_count = 8

        adaptation = _make_adaptation()

        mock_claude.classify.return_value = {
            "type": "tech",
            "description": "Counter card",
            "confidence": 0.8,
            "prevalence": 0.5,
        }
        mock_claude.generate.return_value = "Generated context."

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=snapshot),
            _make_execute_result(scalars_all=[adaptation]),
            _make_execute_result(scalar_one_or_none=None),  # no meta snapshot
        ]

        result = await classifier.classify_and_contextualize(uuid4())
        assert result == "Generated context."
        assert snapshot.meta_context == "Generated context."
        mock_session.commit.assert_called_once()
