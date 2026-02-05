"""Tests for compute_evolution pipeline."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.clients.claude import ClaudeError
from src.pipelines.compute_evolution import (
    ComputeEvolutionResult,
    _classify_adaptations,
    _generate_articles,
    _generate_meta_contexts,
    _generate_predictions,
    compute_evolution_intelligence,
)
from src.services.adaptation_classifier import AdaptationClassifierError
from src.services.evolution_article_generator import ArticleGeneratorError
from src.services.prediction_engine import PredictionEngineError


class TestComputeEvolutionResult:
    """Tests for the ComputeEvolutionResult dataclass."""

    def test_default_values(self) -> None:
        """Should have zero counts and no errors by default."""
        result = ComputeEvolutionResult()
        assert result.adaptations_classified == 0
        assert result.contexts_generated == 0
        assert result.predictions_generated == 0
        assert result.articles_generated == 0
        assert result.errors == []
        assert result.success is True

    def test_success_with_no_errors(self) -> None:
        """Should report success when no errors."""
        result = ComputeEvolutionResult(adaptations_classified=5)
        assert result.success is True

    def test_failure_with_errors(self) -> None:
        """Should report failure when errors present."""
        result = ComputeEvolutionResult(errors=["something went wrong"])
        assert result.success is False


class TestClassifyAdaptations:
    """Tests for _classify_adaptations helper."""

    @pytest.mark.asyncio
    async def test_classifies_unclassified_adaptations(self) -> None:
        """Should classify adaptations that aren't from Claude."""
        mock_adaptation = MagicMock()
        mock_adaptation.id = uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_adaptation]
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        result = ComputeEvolutionResult()

        await _classify_adaptations(session, classifier, result, dry_run=False)

        assert result.adaptations_classified == 1
        classifier.classify.assert_called_once_with(mock_adaptation)
        session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_dry_run_skips_classification(self) -> None:
        """Should count but not classify in dry_run mode."""
        mock_adaptation = MagicMock()
        mock_adaptation.id = uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_adaptation]
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        result = ComputeEvolutionResult()

        await _classify_adaptations(session, classifier, result, dry_run=True)

        assert result.adaptations_classified == 1
        classifier.classify.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_classification_error(self) -> None:
        """Should record errors when classification fails."""
        mock_adaptation = MagicMock()
        mock_adaptation.id = uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_adaptation]
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        classifier.classify.side_effect = AdaptationClassifierError("Failed")
        result = ComputeEvolutionResult()

        await _classify_adaptations(session, classifier, result, dry_run=False)

        assert result.adaptations_classified == 0
        assert len(result.errors) == 1
        assert "Classification failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_no_adaptations_to_classify(self) -> None:
        """Should handle empty adaptation list gracefully."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        result = ComputeEvolutionResult()

        await _classify_adaptations(session, classifier, result, dry_run=False)

        assert result.adaptations_classified == 0
        session.commit.assert_not_called()


class TestGenerateMetaContexts:
    """Tests for _generate_meta_contexts helper."""

    @pytest.mark.asyncio
    async def test_generates_contexts_for_missing_snapshots(self) -> None:
        """Should generate context for snapshots missing meta_context."""
        mock_snapshot = MagicMock()
        mock_snapshot.id = uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_snapshot]
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        classifier.classify_and_contextualize = AsyncMock(return_value="some context")
        result = ComputeEvolutionResult()

        await _generate_meta_contexts(session, classifier, result, dry_run=False)

        assert result.contexts_generated == 1
        classifier.classify_and_contextualize.assert_called_once_with(mock_snapshot.id)

    @pytest.mark.asyncio
    async def test_dry_run_counts_without_generating(self) -> None:
        """Should count but not generate in dry_run mode."""
        mock_snapshot = MagicMock()
        mock_snapshot.id = uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_snapshot]
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        result = ComputeEvolutionResult()

        await _generate_meta_contexts(session, classifier, result, dry_run=True)

        assert result.contexts_generated == 1
        classifier.classify_and_contextualize.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_context_generation_error(self) -> None:
        """Should record errors when context generation fails."""
        mock_snapshot = MagicMock()
        mock_snapshot.id = uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_snapshot]
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        classifier.classify_and_contextualize = AsyncMock(
            side_effect=ClaudeError("API error")
        )
        result = ComputeEvolutionResult()

        await _generate_meta_contexts(session, classifier, result, dry_run=False)

        assert result.contexts_generated == 0
        assert len(result.errors) == 1
        assert "Context generation failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_context_returns_none(self) -> None:
        """Should not count when classify_and_contextualize returns None."""
        mock_snapshot = MagicMock()
        mock_snapshot.id = uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_snapshot]
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        classifier = AsyncMock()
        classifier.classify_and_contextualize = AsyncMock(return_value=None)
        result = ComputeEvolutionResult()

        await _generate_meta_contexts(session, classifier, result, dry_run=False)

        assert result.contexts_generated == 0


class TestGeneratePredictions:
    """Tests for _generate_predictions helper."""

    @pytest.mark.asyncio
    async def test_no_upcoming_tournaments(self) -> None:
        """Should return early when no upcoming tournaments."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_db_result = MagicMock()
        mock_db_result.scalars.return_value = mock_scalars

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        engine = AsyncMock()
        result = ComputeEvolutionResult()

        await _generate_predictions(session, engine, result, dry_run=False)

        assert result.predictions_generated == 0
        engine.predict.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_archetypes(self) -> None:
        """Should return early when no archetypes found."""
        mock_tournament = MagicMock()
        mock_tournament.id = uuid4()
        mock_tournament.date = date.today() + timedelta(days=7)

        # First query: tournaments
        mock_scalars_1 = MagicMock()
        mock_scalars_1.all.return_value = [mock_tournament]
        mock_db_result_1 = MagicMock()
        mock_db_result_1.scalars.return_value = mock_scalars_1

        # Second query: archetypes (empty)
        mock_db_result_2 = MagicMock()
        mock_db_result_2.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[mock_db_result_1, mock_db_result_2])

        engine = AsyncMock()
        result = ComputeEvolutionResult()

        await _generate_predictions(session, engine, result, dry_run=False)

        assert result.predictions_generated == 0

    @pytest.mark.asyncio
    async def test_generates_predictions_dry_run(self) -> None:
        """Should count predictions without generating in dry_run."""
        mock_tournament = MagicMock()
        mock_tournament.id = uuid4()
        mock_tournament.date = date.today() + timedelta(days=7)

        # First query: tournaments
        mock_scalars_1 = MagicMock()
        mock_scalars_1.all.return_value = [mock_tournament]
        mock_db_result_1 = MagicMock()
        mock_db_result_1.scalars.return_value = mock_scalars_1

        # Second query: archetypes
        mock_db_result_2 = MagicMock()
        mock_db_result_2.all.return_value = [("Charizard ex",)]

        # Third query: existing predictions (none)
        mock_db_result_3 = MagicMock()
        mock_db_result_3.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[mock_db_result_1, mock_db_result_2, mock_db_result_3]
        )

        engine = AsyncMock()
        result = ComputeEvolutionResult()

        await _generate_predictions(session, engine, result, dry_run=True)

        assert result.predictions_generated == 1
        engine.predict.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_existing_predictions(self) -> None:
        """Should skip archetypes with existing predictions."""
        tournament_id = uuid4()
        mock_tournament = MagicMock()
        mock_tournament.id = tournament_id
        mock_tournament.date = date.today() + timedelta(days=7)

        # First query: tournaments
        mock_scalars_1 = MagicMock()
        mock_scalars_1.all.return_value = [mock_tournament]
        mock_db_result_1 = MagicMock()
        mock_db_result_1.scalars.return_value = mock_scalars_1

        # Second query: archetypes
        mock_db_result_2 = MagicMock()
        mock_db_result_2.all.return_value = [("Charizard ex",)]

        # Third query: existing predictions (already exists)
        mock_db_result_3 = MagicMock()
        mock_db_result_3.all.return_value = [("Charizard ex", tournament_id)]

        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[mock_db_result_1, mock_db_result_2, mock_db_result_3]
        )

        engine = AsyncMock()
        result = ComputeEvolutionResult()

        await _generate_predictions(session, engine, result, dry_run=True)

        assert result.predictions_generated == 0

    @pytest.mark.asyncio
    async def test_handles_prediction_error(self) -> None:
        """Should record errors when prediction fails."""
        mock_tournament = MagicMock()
        mock_tournament.id = uuid4()
        mock_tournament.date = date.today() + timedelta(days=7)

        mock_scalars_1 = MagicMock()
        mock_scalars_1.all.return_value = [mock_tournament]
        mock_db_result_1 = MagicMock()
        mock_db_result_1.scalars.return_value = mock_scalars_1

        mock_db_result_2 = MagicMock()
        mock_db_result_2.all.return_value = [("Lugia VSTAR",)]

        mock_db_result_3 = MagicMock()
        mock_db_result_3.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(
            side_effect=[mock_db_result_1, mock_db_result_2, mock_db_result_3]
        )

        engine = AsyncMock()
        engine.predict.side_effect = PredictionEngineError("Prediction failed")
        result = ComputeEvolutionResult()

        await _generate_predictions(session, engine, result, dry_run=False)

        assert result.predictions_generated == 0
        assert len(result.errors) == 1
        assert "Prediction failed" in result.errors[0]


class TestGenerateArticles:
    """Tests for _generate_articles helper."""

    @pytest.mark.asyncio
    async def test_no_eligible_archetypes(self) -> None:
        """Should handle no archetypes with sufficient data."""
        mock_db_result = MagicMock()
        mock_db_result.all.return_value = []

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        generator = AsyncMock()
        result = ComputeEvolutionResult()

        await _generate_articles(session, generator, result, dry_run=False)

        assert result.articles_generated == 0

    @pytest.mark.asyncio
    async def test_generates_articles_dry_run(self) -> None:
        """Should count without generating in dry_run mode."""
        mock_db_result = MagicMock()
        mock_db_result.all.return_value = [("Charizard ex",)]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        generator = AsyncMock()
        result = ComputeEvolutionResult()

        await _generate_articles(session, generator, result, dry_run=True)

        assert result.articles_generated == 1
        generator.generate_article.assert_not_called()
        session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_article_generation_error(self) -> None:
        """Should record errors when article generation fails."""
        mock_db_result = MagicMock()
        mock_db_result.all.return_value = [("Gardevoir ex",)]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_db_result)

        generator = AsyncMock()
        generator.generate_article.side_effect = ArticleGeneratorError("Failed")
        result = ComputeEvolutionResult()

        await _generate_articles(session, generator, result, dry_run=False)

        assert result.articles_generated == 0
        assert len(result.errors) == 1
        assert "Article generation failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_generates_article_with_snapshot_links(self) -> None:
        """Should generate article and link snapshots."""
        # First query: eligible archetypes
        mock_arch_result = MagicMock()
        mock_arch_result.all.return_value = [("Charizard ex",)]

        # Second query: snapshot IDs for linking
        snapshot_ids = [uuid4(), uuid4(), uuid4()]
        mock_snap_result = MagicMock()
        mock_snap_result.all.return_value = [(sid,) for sid in snapshot_ids]

        # Use MagicMock for session so .add() is not awaitable
        # (session.add is sync in SQLAlchemy, but session.execute/commit are async)
        session = MagicMock()
        session.execute = AsyncMock(side_effect=[mock_arch_result, mock_snap_result])
        session.commit = AsyncMock()

        mock_article = MagicMock()
        mock_links = [MagicMock(), MagicMock(), MagicMock()]

        generator = AsyncMock()
        generator.generate_article = AsyncMock(return_value=mock_article)
        generator.link_snapshots = AsyncMock(return_value=mock_links)
        result = ComputeEvolutionResult()

        await _generate_articles(session, generator, result, dry_run=False)

        assert result.articles_generated == 1
        generator.generate_article.assert_called_once_with("Charizard ex")
        generator.link_snapshots.assert_called_once_with(mock_article, snapshot_ids)
        # article + 3 links = 4 session.add calls
        assert session.add.call_count == 4
        session.commit.assert_called_once()


class TestComputeEvolutionIntelligence:
    """Tests for the main compute_evolution_intelligence function."""

    @pytest.mark.asyncio
    async def test_dry_run_completes_successfully(self) -> None:
        """Should complete dry run without errors."""
        # Mock all DB queries to return empty results
        mock_empty_scalars = MagicMock()
        mock_empty_scalars.all.return_value = []
        mock_empty_db_result = MagicMock()
        mock_empty_db_result.scalars.return_value = mock_empty_scalars

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_empty_db_result)

        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_claude = AsyncMock()
        mock_claude_ctx = AsyncMock()
        mock_claude_ctx.__aenter__ = AsyncMock(return_value=mock_claude)
        mock_claude_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "src.pipelines.compute_evolution.async_session_factory",
                return_value=mock_session_ctx,
            ),
            patch(
                "src.pipelines.compute_evolution.ClaudeClient",
                return_value=mock_claude_ctx,
            ),
            patch("src.pipelines.compute_evolution.AdaptationClassifier"),
            patch("src.pipelines.compute_evolution.PredictionEngine"),
            patch("src.pipelines.compute_evolution.EvolutionArticleGenerator"),
        ):
            result = await compute_evolution_intelligence(dry_run=True)

        assert result.success is True

    @pytest.mark.asyncio
    async def test_handles_database_error(self) -> None:
        """Should catch SQLAlchemy errors and record them."""
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(
            side_effect=SQLAlchemyError("Connection lost")
        )
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_claude_ctx = AsyncMock()
        mock_claude_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_claude_ctx.__aexit__ = AsyncMock(return_value=False)

        # Both context managers are entered together.
        # SQLAlchemy error during session creation will be
        # caught at the outer try.
        with (
            patch(
                "src.pipelines.compute_evolution.async_session_factory",
                return_value=mock_session_ctx,
            ),
            patch(
                "src.pipelines.compute_evolution.ClaudeClient",
                return_value=mock_claude_ctx,
            ),
        ):
            result = await compute_evolution_intelligence(dry_run=False)

        assert result.success is False
        assert len(result.errors) == 1
        assert (
            "Database error" in result.errors[0] or "error" in result.errors[0].lower()
        )

    @pytest.mark.asyncio
    async def test_handles_claude_error(self) -> None:
        """Should catch Claude API errors and record them."""
        mock_claude_ctx = AsyncMock()
        mock_claude_ctx.__aenter__ = AsyncMock(
            side_effect=ClaudeError("API key invalid")
        )
        mock_claude_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.compute_evolution.ClaudeClient",
            return_value=mock_claude_ctx,
        ):
            result = await compute_evolution_intelligence(dry_run=False)

        assert result.success is False
        assert len(result.errors) == 1
        assert "Claude API error" in result.errors[0]

    @pytest.mark.asyncio
    async def test_handles_unexpected_error(self) -> None:
        """Should catch unexpected errors and record them."""
        mock_claude_ctx = AsyncMock()
        mock_claude_ctx.__aenter__ = AsyncMock(
            side_effect=RuntimeError("Something unexpected")
        )
        mock_claude_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "src.pipelines.compute_evolution.ClaudeClient",
            return_value=mock_claude_ctx,
        ):
            result = await compute_evolution_intelligence(dry_run=False)

        assert result.success is False
        assert len(result.errors) == 1
        assert "Unexpected error" in result.errors[0]
