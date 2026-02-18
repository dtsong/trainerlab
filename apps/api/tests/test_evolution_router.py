"""Tests for the Evolution API router."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from src.dependencies.beta import require_beta
from src.main import app
from src.models.archetype_evolution_snapshot import ArchetypeEvolutionSnapshot
from src.models.archetype_prediction import ArchetypePrediction
from src.models.evolution_article import EvolutionArticle
from src.models.evolution_article_snapshot import EvolutionArticleSnapshot

_UNSET = object()


def _make_execute_result(
    *, scalar_one_or_none=_UNSET, scalars_all=_UNSET, scalar=_UNSET
):
    """Create a mock result from session.execute()."""
    mock_result = MagicMock()
    if scalar_one_or_none is not _UNSET:
        mock_result.scalar_one_or_none.return_value = scalar_one_or_none
    if scalars_all is not _UNSET:
        mock_result.scalars.return_value.all.return_value = scalars_all
    if scalar is not _UNSET:
        mock_result.scalar.return_value = scalar
    return mock_result


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked DB."""
    from src.db.database import get_db

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[require_beta] = lambda: None
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestGetArchetypeEvolution:
    """Tests for GET /api/v1/archetypes/{id}/evolution."""

    def test_returns_timeline(self, client, mock_db) -> None:
        """Should return evolution timeline with snapshots."""
        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.id = uuid4()
        snapshot.archetype = "Charizard ex"
        snapshot.tournament_id = uuid4()
        snapshot.meta_share = 0.12
        snapshot.top_cut_conversion = 0.35
        snapshot.best_placement = 2
        snapshot.deck_count = 8
        snapshot.consensus_list = None
        snapshot.meta_context = "Test context"
        snapshot.adaptations = []
        snapshot.created_at = datetime.now(UTC)

        mock_db.execute.return_value = _make_execute_result(scalars_all=[snapshot])

        response = client.get("/api/v1/archetypes/Charizard%20ex/evolution")
        assert response.status_code == 200
        data = response.json()
        assert data["archetype"] == "Charizard ex"
        assert len(data["snapshots"]) == 1
        assert data["snapshots"][0]["meta_share"] == 0.12

    def test_returns_404_when_no_data(self, client, mock_db) -> None:
        """Should return 404 when no snapshots found."""
        mock_db.execute.return_value = _make_execute_result(scalars_all=[])

        response = client.get("/api/v1/archetypes/Unknown/evolution")
        assert response.status_code == 404


class TestGetArchetypePrediction:
    """Tests for GET /api/v1/archetypes/{id}/prediction."""

    def test_returns_prediction(self, client, mock_db) -> None:
        """Should return the latest prediction."""
        prediction = MagicMock(spec=ArchetypePrediction)
        prediction.id = uuid4()
        prediction.archetype_id = "Charizard ex"
        prediction.target_tournament_id = uuid4()
        prediction.predicted_meta_share = {
            "low": 0.08,
            "mid": 0.12,
            "high": 0.16,
        }
        prediction.predicted_day2_rate = None
        prediction.predicted_tier = "A"
        prediction.likely_adaptations = None
        prediction.confidence = 0.75
        prediction.methodology = "Based on trajectory."
        prediction.actual_meta_share = None
        prediction.accuracy_score = None
        prediction.created_at = datetime.now(UTC)

        mock_db.execute.return_value = _make_execute_result(
            scalar_one_or_none=prediction
        )

        response = client.get("/api/v1/archetypes/Charizard%20ex/prediction")
        assert response.status_code == 200
        data = response.json()
        assert data["predicted_tier"] == "A"
        assert data["confidence"] == 0.75

    def test_returns_404_when_no_prediction(self, client, mock_db) -> None:
        """Should return 404 when no prediction found."""
        mock_db.execute.return_value = _make_execute_result(scalar_one_or_none=None)

        response = client.get("/api/v1/archetypes/Unknown/prediction")
        assert response.status_code == 404


class TestListEvolutionArticles:
    """Tests for GET /api/v1/evolution."""

    def test_returns_article_list(self, client, mock_db) -> None:
        """Should return list of published articles."""
        article = MagicMock(spec=EvolutionArticle)
        article.id = uuid4()
        article.archetype_id = "Charizard ex"
        article.slug = "charizard-ex-evolution-20260203"
        article.title = "Charizard ex Evolution"
        article.excerpt = "How Charizard adapted."
        article.status = "published"
        article.is_premium = False
        article.published_at = datetime.now(UTC)

        mock_db.execute.return_value = _make_execute_result(scalars_all=[article])

        response = client.get("/api/v1/evolution")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["slug"] == "charizard-ex-evolution-20260203"

    def test_returns_empty_list(self, client, mock_db) -> None:
        """Should return empty list when no articles."""
        mock_db.execute.return_value = _make_execute_result(scalars_all=[])

        response = client.get("/api/v1/evolution")
        assert response.status_code == 200
        assert response.json() == []


class TestGetPredictionAccuracy:
    """Tests for GET /api/v1/evolution/accuracy."""

    def test_returns_accuracy_data(self, client, mock_db) -> None:
        """Should return accuracy tracking summary."""
        prediction = MagicMock(spec=ArchetypePrediction)
        prediction.id = uuid4()
        prediction.archetype_id = "Charizard ex"
        prediction.target_tournament_id = uuid4()
        prediction.predicted_meta_share = {"mid": 0.12}
        prediction.predicted_day2_rate = None
        prediction.predicted_tier = "A"
        prediction.likely_adaptations = None
        prediction.confidence = 0.8
        prediction.methodology = "Trajectory analysis."
        prediction.actual_meta_share = 0.11
        prediction.accuracy_score = 0.92
        prediction.created_at = datetime.now(UTC)

        mock_db.execute.side_effect = [
            _make_execute_result(scalar=5),  # total
            _make_execute_result(scalar=3),  # scored
            _make_execute_result(scalar=0.85),  # avg accuracy
            _make_execute_result(scalars_all=[prediction]),  # predictions
        ]

        response = client.get("/api/v1/evolution/accuracy")
        assert response.status_code == 200
        data = response.json()
        assert data["total_predictions"] == 5
        assert data["scored_predictions"] == 3
        assert data["average_accuracy"] == 0.85
        assert len(data["predictions"]) == 1


class TestGetEvolutionArticle:
    """Tests for GET /api/v1/evolution/{slug}."""

    def test_returns_article_with_snapshots(self, client, mock_db) -> None:
        """Should return full article with linked snapshots."""
        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.id = uuid4()
        snapshot.archetype = "Charizard ex"
        snapshot.tournament_id = uuid4()
        snapshot.meta_share = 0.12
        snapshot.top_cut_conversion = 0.35
        snapshot.best_placement = 2
        snapshot.deck_count = 8
        snapshot.consensus_list = None
        snapshot.meta_context = None
        snapshot.created_at = datetime.now(UTC)

        link = MagicMock(spec=EvolutionArticleSnapshot)
        link.position = 0
        link.snapshot = snapshot

        article = MagicMock(spec=EvolutionArticle)
        article.id = uuid4()
        article.archetype_id = "Charizard ex"
        article.slug = "charizard-ex-evolution-20260203"
        article.title = "Charizard ex Evolution"
        article.excerpt = "How it adapted."
        article.introduction = "Intro text."
        article.conclusion = "Conclusion text."
        article.status = "published"
        article.is_premium = False
        article.published_at = datetime.now(UTC)
        article.view_count = 10
        article.share_count = 2
        article.article_snapshots = [link]

        mock_db.execute.return_value = _make_execute_result(scalar_one_or_none=article)

        response = client.get("/api/v1/evolution/charizard-ex-evolution-20260203")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Charizard ex Evolution"
        assert len(data["snapshots"]) == 1
        assert data["view_count"] == 11  # incremented

    def test_returns_404_for_missing_slug(self, client, mock_db) -> None:
        """Should return 404 for unknown slug."""
        mock_db.execute.return_value = _make_execute_result(scalar_one_or_none=None)

        response = client.get("/api/v1/evolution/nonexistent-slug")
        assert response.status_code == 404

    def test_handles_view_count_increment_failure(self, client, mock_db) -> None:
        """Should return article when view count fails."""
        snapshot = MagicMock(spec=ArchetypeEvolutionSnapshot)
        snapshot.id = uuid4()
        snapshot.archetype = "Charizard ex"
        snapshot.tournament_id = uuid4()
        snapshot.meta_share = 0.12
        snapshot.top_cut_conversion = 0.35
        snapshot.best_placement = 2
        snapshot.deck_count = 8
        snapshot.consensus_list = None
        snapshot.meta_context = None
        snapshot.created_at = datetime.now(UTC)

        link = MagicMock(spec=EvolutionArticleSnapshot)
        link.position = 0
        link.snapshot = snapshot

        article = MagicMock(spec=EvolutionArticle)
        article.id = uuid4()
        article.archetype_id = "Charizard ex"
        article.slug = "test-slug"
        article.title = "Test Article"
        article.excerpt = "Excerpt"
        article.introduction = "Intro"
        article.conclusion = "Conclusion"
        article.status = "published"
        article.is_premium = False
        article.published_at = datetime.now(UTC)
        article.view_count = 5
        article.share_count = 0
        article.article_snapshots = [link]

        # First call: fetch article (succeeds)
        # Second call: increment view count (fails with SQLAlchemy error)
        first_result = _make_execute_result(scalar_one_or_none=article)
        mock_db.execute.side_effect = [
            first_result,
            SQLAlchemyError("Connection lost"),
        ]

        response = client.get("/api/v1/evolution/test-slug")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Article"

    def test_handles_missing_snapshot_in_link(self, client, mock_db) -> None:
        """Should skip links with missing snapshots (line 363)."""
        link = MagicMock(spec=EvolutionArticleSnapshot)
        link.position = 0
        link.snapshot = None  # Missing snapshot

        article = MagicMock(spec=EvolutionArticle)
        article.id = uuid4()
        article.archetype_id = "Charizard ex"
        article.slug = "missing-snap"
        article.title = "Test"
        article.excerpt = "Excerpt"
        article.introduction = "Intro"
        article.conclusion = "Conclusion"
        article.status = "published"
        article.is_premium = False
        article.published_at = datetime.now(UTC)
        article.view_count = 0
        article.share_count = 0
        article.article_snapshots = [link]

        mock_db.execute.return_value = _make_execute_result(scalar_one_or_none=article)

        response = client.get("/api/v1/evolution/missing-snap")
        assert response.status_code == 200
        data = response.json()
        assert data["snapshots"] == []


class TestEvolutionRouterDatabaseErrors:
    """Tests for SQLAlchemy error handling in evolution."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db):
        from src.db.database import get_db

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[require_beta] = lambda: None
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_evolution_timeline_db_error(self, client, mock_db) -> None:
        """Should return 503 on DB error for evolution timeline (lines 99-105)."""
        mock_db.execute.side_effect = SQLAlchemyError("Connection error")

        response = client.get("/api/v1/archetypes/test/evolution")
        assert response.status_code == 503
        assert "Unable to retrieve" in response.json()["detail"]

    def test_prediction_db_error(self, client, mock_db) -> None:
        """Should return 503 on DB error for prediction (lines 141-147)."""
        mock_db.execute.side_effect = SQLAlchemyError("Timeout")

        response = client.get("/api/v1/archetypes/test/prediction")
        assert response.status_code == 503
        assert "Unable to retrieve" in response.json()["detail"]

    def test_list_articles_db_error(self, client, mock_db) -> None:
        """Should return 503 on DB error for article listing (lines 201-206)."""
        mock_db.execute.side_effect = SQLAlchemyError("Pool exhausted")

        response = client.get("/api/v1/evolution")
        assert response.status_code == 503
        assert "Unable to retrieve" in response.json()["detail"]

    def test_accuracy_db_error(self, client, mock_db) -> None:
        """Should return 503 on DB error for accuracy (lines 267-272)."""
        mock_db.execute.side_effect = SQLAlchemyError("Broken pipe")

        response = client.get("/api/v1/evolution/accuracy")
        assert response.status_code == 503
        assert "Unable to retrieve" in response.json()["detail"]

    def test_article_detail_db_error(self, client, mock_db) -> None:
        """Should return 503 on DB error for article detail (lines 323-329)."""
        mock_db.execute.side_effect = SQLAlchemyError("Read-only")

        response = client.get("/api/v1/evolution/some-slug")
        assert response.status_code == 503
        assert "Unable to retrieve" in response.json()["detail"]
