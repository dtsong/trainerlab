"""Tests for the PredictionEngine."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.clients.claude import ClaudeError
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.services.prediction_engine import (
    PredictionEngine,
    PredictionEngineError,
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


def _make_tournament(**kwargs) -> MagicMock:
    """Create a mock Tournament."""
    mock = MagicMock(spec=Tournament)
    mock.id = kwargs.get("id", uuid4())
    mock.tier = kwargs.get("tier", "major")
    mock.participant_count = kwargs.get("participant_count", 256)
    mock.date = kwargs.get("date", date(2026, 3, 15))
    return mock


def _make_snapshot(**kwargs) -> MagicMock:
    """Create a mock ArchetypeEvolutionSnapshot."""
    mock = MagicMock(spec=ArchetypeEvolutionSnapshot)
    mock.id = kwargs.get("id", uuid4())
    mock.archetype = kwargs.get("archetype", "Charizard ex")
    mock.meta_share = kwargs.get("meta_share", 0.12)
    mock.top_cut_conversion = kwargs.get("top_cut_conversion", 0.35)
    mock.best_placement = kwargs.get("best_placement", 2)
    mock.deck_count = kwargs.get("deck_count", 8)
    mock.tournament_id = kwargs.get("tournament_id", uuid4())
    return mock


class TestPredict:
    """Tests for prediction generation."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def engine(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> PredictionEngine:
        return PredictionEngine(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_generates_prediction(
        self,
        engine: PredictionEngine,
        mock_session: AsyncMock,
        mock_claude: AsyncMock,
    ) -> None:
        """Should generate a prediction with all fields populated."""
        tournament = _make_tournament()
        snapshots = [_make_snapshot() for _ in range(3)]

        mock_claude.classify.return_value = {
            "predicted_meta_share": {"low": 0.08, "mid": 0.12, "high": 0.16},
            "predicted_day2_rate": {"low": 0.3, "mid": 0.4, "high": 0.5},
            "predicted_tier": "A",
            "likely_adaptations": [{"type": "tech", "description": "Add Drapion V"}],
            "jp_signals": {"trending": True},
            "confidence": 0.75,
            "methodology": "Based on rising trajectory and JP signals.",
        }

        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=snapshots),  # recent snapshots
            _make_execute_result(scalar_one_or_none=tournament),  # tournament
            _make_execute_result(scalar_one_or_none=None),  # meta snapshot
            _make_execute_result(scalars_all=[]),  # upcoming sets
        ]

        prediction = await engine.predict("Charizard ex", tournament.id)

        assert isinstance(prediction, ArchetypePrediction)
        assert prediction.archetype_id == "Charizard ex"
        assert prediction.target_tournament_id == tournament.id
        assert prediction.predicted_tier == "A"
        assert prediction.predicted_meta_share == {
            "low": 0.08,
            "mid": 0.12,
            "high": 0.16,
        }
        assert prediction.confidence == 0.75
        assert prediction.methodology is not None

    @pytest.mark.asyncio
    async def test_raises_when_tournament_not_found(
        self,
        engine: PredictionEngine,
        mock_session: AsyncMock,
    ) -> None:
        """Should raise PredictionEngineError when tournament not found."""
        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=[]),  # recent snapshots
            _make_execute_result(scalar_one_or_none=None),  # no tournament
        ]

        with pytest.raises(PredictionEngineError, match="not found"):
            await engine.predict("Charizard ex", uuid4())

    @pytest.mark.asyncio
    async def test_raises_on_claude_error(
        self,
        engine: PredictionEngine,
        mock_session: AsyncMock,
        mock_claude: AsyncMock,
    ) -> None:
        """Should raise PredictionEngineError on Claude failure."""
        tournament = _make_tournament()

        mock_claude.classify.side_effect = ClaudeError("API error")

        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=[]),  # no snapshots
            _make_execute_result(scalar_one_or_none=tournament),  # tournament
            _make_execute_result(scalar_one_or_none=None),  # meta snapshot
            _make_execute_result(scalars_all=[]),  # upcoming sets
        ]

        with pytest.raises(PredictionEngineError, match="Failed to generate"):
            await engine.predict("Charizard ex", tournament.id)

    @pytest.mark.asyncio
    async def test_includes_meta_snapshot_context(
        self,
        engine: PredictionEngine,
        mock_session: AsyncMock,
        mock_claude: AsyncMock,
    ) -> None:
        """Should include meta snapshot data in prediction context."""
        tournament = _make_tournament()
        meta_snapshot = MagicMock(spec=MetaSnapshot)
        meta_snapshot.archetype_shares = {
            "Charizard ex": 0.15,
            "Gardevoir ex": 0.12,
        }
        meta_snapshot.jp_signals = {"rising": ["Dragapult ex"]}
        meta_snapshot.trends = {"Charizard ex": {"direction": "up"}}

        mock_claude.classify.return_value = {
            "predicted_meta_share": {"low": 0.10, "mid": 0.15, "high": 0.20},
            "predicted_tier": "S",
            "confidence": 0.8,
            "methodology": "Strong trajectory with JP support.",
        }

        mock_session.execute.side_effect = [
            _make_execute_result(scalars_all=[]),  # no snapshots
            _make_execute_result(scalar_one_or_none=tournament),  # tournament
            _make_execute_result(scalar_one_or_none=meta_snapshot),  # meta
            _make_execute_result(scalars_all=[]),  # no new sets
        ]

        prediction = await engine.predict("Charizard ex", tournament.id)
        assert prediction.predicted_tier == "S"

        call_args = mock_claude.classify.call_args
        assert "Gardevoir ex" in call_args.kwargs["user"]


class TestScorePrediction:
    """Tests for post-event scoring."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def mock_claude(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def engine(
        self, mock_session: AsyncMock, mock_claude: AsyncMock
    ) -> PredictionEngine:
        return PredictionEngine(mock_session, mock_claude)

    @pytest.mark.asyncio
    async def test_scores_prediction_accurately(
        self,
        engine: PredictionEngine,
        mock_session: AsyncMock,
    ) -> None:
        """Should compute accuracy score from actual vs predicted."""
        prediction = MagicMock(spec=ArchetypePrediction)
        prediction.archetype_id = "Charizard ex"
        prediction.target_tournament_id = uuid4()
        prediction.predicted_meta_share = {
            "low": 0.08,
            "mid": 0.12,
            "high": 0.16,
        }

        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.meta_share = 0.11  # Close to mid=0.12

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=prediction),
            _make_execute_result(scalar_one_or_none=snapshot),
        ]

        await engine.score_prediction(uuid4())

        assert prediction.actual_meta_share == 0.11
        # Error = |0.11 - 0.12| / 0.12 = 0.0833...
        # Accuracy = 1 - 0.0833 = 0.9167
        assert prediction.accuracy_score == round(1.0 - abs(0.11 - 0.12) / 0.12, 4)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_prediction_not_found(
        self,
        engine: PredictionEngine,
        mock_session: AsyncMock,
    ) -> None:
        """Should raise PredictionEngineError."""
        mock_session.execute.return_value = _make_execute_result(
            scalar_one_or_none=None
        )

        with pytest.raises(PredictionEngineError, match="not found"):
            await engine.score_prediction(uuid4())

    @pytest.mark.asyncio
    async def test_handles_missing_snapshot(
        self,
        engine: PredictionEngine,
        mock_session: AsyncMock,
    ) -> None:
        """Should return without scoring when no snapshot found."""
        prediction = MagicMock(spec=ArchetypePrediction)
        prediction.archetype_id = "Charizard ex"
        prediction.target_tournament_id = uuid4()

        mock_session.execute.side_effect = [
            _make_execute_result(scalar_one_or_none=prediction),
            _make_execute_result(scalar_one_or_none=None),  # no snapshot
        ]

        await engine.score_prediction(uuid4())
        mock_session.commit.assert_not_called()
