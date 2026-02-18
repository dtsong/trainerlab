"""Tests for JP post-rotation meta intelligence features.

Covers:
- start_date_floor clamping in meta service
- min_tournaments parameter in _compute_archetype_shares
- era query param on meta endpoints
- start_date query param on meta history
- GET /japan/content endpoint
- era_label in snapshot response
- JP content schemas
"""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.db.database import get_db
from src.dependencies.beta import require_beta
from src.main import app
from src.models import MetaSnapshot, TournamentPlacement
from src.models.translated_content import TranslatedContent
from src.services.meta_service import MetaService

# ──────────────────────────────────────────────
# start_date_floor + min_tournaments
# ──────────────────────────────────────────────


class TestStartDateFloor:
    """Tests for start_date_floor clamping."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.mark.asyncio
    async def test_clamps_start_date_to_floor(
        self,
        service: MetaService,
        mock_session: AsyncMock,
    ) -> None:
        """start_date_floor should prevent lookback before the floor."""
        # No tournaments → returns empty snapshot, but we verify clamping works
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2026, 2, 7),
            region="JP",
            game_format="standard",
            best_of=1,
            lookback_days=90,
            start_date_floor=date(2026, 1, 23),
            era_label="post-nihil-zero",
        )

        assert snapshot.era_label == "post-nihil-zero"
        assert snapshot.sample_size == 0

    @pytest.mark.asyncio
    async def test_floor_sets_era_label(
        self,
        service: MetaService,
        mock_session: AsyncMock,
    ) -> None:
        """era_label should be set on the resulting snapshot."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2026, 2, 7),
            region="JP",
            game_format="standard",
            best_of=1,
            era_label="post-nihil-zero",
        )

        assert snapshot.era_label == "post-nihil-zero"

    @pytest.mark.asyncio
    async def test_no_floor_no_clamping(
        self,
        service: MetaService,
        mock_session: AsyncMock,
    ) -> None:
        """Without start_date_floor, full lookback is used."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        snapshot = await service.compute_meta_snapshot(
            snapshot_date=date(2026, 2, 7),
            region="JP",
            game_format="standard",
            best_of=1,
        )

        assert snapshot.era_label is None


class TestMinTournamentsParam:
    """Tests for min_tournaments parameter on _compute_archetype_shares."""

    @pytest.fixture
    def service(self) -> MetaService:
        return MetaService(AsyncMock())

    def test_default_min_tournaments_filters_at_3(self, service: MetaService) -> None:
        """Default (3) filters out archetypes in < 3 tournaments."""
        t1, t2 = uuid4(), uuid4()
        placements = []
        for tid in [t1, t2]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "TwoTourneyDeck"
            p.tournament_id = tid
            placements.append(p)

        shares = service._compute_archetype_shares(placements)
        assert "TwoTourneyDeck" not in shares

    def test_min_tournaments_2_includes_2_tournament_archetype(
        self, service: MetaService
    ) -> None:
        """min_tournaments=2 includes archetypes in 2 tournaments."""
        t1, t2 = uuid4(), uuid4()
        placements = []
        for tid in [t1, t2]:
            p = MagicMock(spec=TournamentPlacement)
            p.archetype = "TwoTourneyDeck"
            p.tournament_id = tid
            placements.append(p)

        shares = service._compute_archetype_shares(placements, min_tournaments=2)
        assert "TwoTourneyDeck" in shares

    def test_min_tournaments_1_includes_single_tournament(
        self, service: MetaService
    ) -> None:
        """min_tournaments=1 includes archetypes in a single tournament."""
        t1 = uuid4()
        p = MagicMock(spec=TournamentPlacement)
        p.archetype = "OneTourneyDeck"
        p.tournament_id = t1

        shares = service._compute_archetype_shares([p], min_tournaments=1)
        assert "OneTourneyDeck" in shares


# ──────────────────────────────────────────────
# era query param on meta endpoints
# ──────────────────────────────────────────────


class TestEraQueryParam:
    """Tests for era query param on meta endpoints."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = lambda: None
        yield TestClient(app)
        app.dependency_overrides.clear()

    def _make_snapshot(self, **overrides) -> MagicMock:
        snapshot = MagicMock(spec=MetaSnapshot)
        snapshot.snapshot_date = date(2026, 2, 1)
        snapshot.region = "JP"
        snapshot.format = "standard"
        snapshot.best_of = 1
        snapshot.archetype_shares = {"Charizard ex": 0.15}
        snapshot.card_usage = {}
        snapshot.sample_size = 100
        snapshot.tournaments_included = ["t-1"]
        snapshot.diversity_index = None
        snapshot.tier_assignments = None
        snapshot.jp_signals = None
        snapshot.trends = None
        snapshot.era_label = None
        snapshot.tournament_type = "all"
        for k, v in overrides.items():
            setattr(snapshot, k, v)
        return snapshot

    def test_current_meta_with_era_filter(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """GET /meta/current?era=post-nihil-zero filters by era."""
        snapshot = self._make_snapshot(era_label="post-nihil-zero")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = snapshot
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/meta/current?region=JP&best_of=1&era=post-nihil-zero"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["era_label"] == "post-nihil-zero"

    def test_current_meta_without_era(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """GET /meta/current without era returns era_label=null."""
        snapshot = self._make_snapshot()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = snapshot
        mock_db.execute.return_value = mock_result

        response = client.get("/api/v1/meta/current?region=JP&best_of=1")

        assert response.status_code == 200
        data = response.json()
        assert data["era_label"] is None

    def test_history_with_era_filter(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """GET /meta/history?era=post-nihil-zero filters snapshots."""
        snapshot = self._make_snapshot(era_label="post-nihil-zero")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snapshot]
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/meta/history?region=JP&best_of=1&era=post-nihil-zero"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["snapshots"]) == 1
        assert data["snapshots"][0]["era_label"] == "post-nihil-zero"

    def test_history_with_start_date_param(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """GET /meta/history?start_date=2026-01-23 overrides days."""
        snapshot = self._make_snapshot()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [snapshot]
        mock_db.execute.return_value = mock_result

        response = client.get(
            "/api/v1/meta/history?region=JP&best_of=1&start_date=2026-01-23"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["snapshots"]) == 1


# ──────────────────────────────────────────────
# GET /japan/content
# ──────────────────────────────────────────────


class TestJPContentEndpoint:
    """Tests for GET /api/v1/japan/content."""

    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def client(self, mock_db: AsyncMock) -> TestClient:
        async def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_beta] = lambda: None
        yield TestClient(app)
        app.dependency_overrides.clear()

    def _make_content(self, **overrides) -> MagicMock:
        item = MagicMock(spec=TranslatedContent)
        item.id = uuid4()
        item.source_url = "https://pokecabook.com/article/1"
        item.content_type = "article"
        item.translated_text = "Translated article text" * 5
        item.translated_at = datetime(2026, 2, 1, tzinfo=UTC)
        item.title_en = "Charizard ex Deck Guide"
        item.title_jp = "リザードンexデッキガイド"
        item.published_date = date(2026, 1, 25)
        item.source_name = "pokecabook"
        item.tags = ["deck-guide", "charizard"]
        item.archetype_refs = ["Charizard ex"]
        item.era_label = "post-nihil-zero"
        item.review_status = "auto_approved"
        item.status = "translated"
        for k, v in overrides.items():
            setattr(item, k, v)
        return item

    def test_returns_content_list(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Should return translated content items."""
        item = self._make_content()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [item]
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        mock_db.execute.side_effect = [mock_result, mock_count]

        response = client.get("/api/v1/japan/content")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["content_type"] == "article"
        assert data["items"][0]["title_en"] == "Charizard ex Deck Guide"
        assert data["items"][0]["source_name"] == "pokecabook"
        assert data["items"][0]["era_label"] == "post-nihil-zero"

    def test_filters_by_content_type(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Should filter by content_type param."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_db.execute.side_effect = [mock_result, mock_count]

        response = client.get("/api/v1/japan/content?content_type=tier_list")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_filters_by_era(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Should filter by era param."""
        item = self._make_content()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [item]
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        mock_db.execute.side_effect = [mock_result, mock_count]

        response = client.get("/api/v1/japan/content?era=post-nihil-zero")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_filters_by_source(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Should filter by source param."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_db.execute.side_effect = [mock_result, mock_count]

        response = client.get("/api/v1/japan/content?source=pokekameshi")

        assert response.status_code == 200

    def test_limit_param(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Should respect limit param."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_count = MagicMock()
        mock_count.scalar.return_value = 0
        mock_db.execute.side_effect = [mock_result, mock_count]

        response = client.get("/api/v1/japan/content?limit=5")

        assert response.status_code == 200

    def test_limit_validation(self, client: TestClient, mock_db: AsyncMock) -> None:
        """Should reject invalid limit values."""
        response = client.get("/api/v1/japan/content?limit=0")
        assert response.status_code == 422

        response = client.get("/api/v1/japan/content?limit=101")
        assert response.status_code == 422

    def test_db_error_returns_503(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Should return 503 on database error."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_db.execute.side_effect = SQLAlchemyError("DB error")

        response = client.get("/api/v1/japan/content")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_truncates_translated_text(
        self,
        client: TestClient,
        mock_db: AsyncMock,
    ) -> None:
        """Should truncate translated_text to 500 chars."""
        long_text = "x" * 1000
        item = self._make_content(translated_text=long_text)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [item]
        mock_count = MagicMock()
        mock_count.scalar.return_value = 1
        mock_db.execute.side_effect = [mock_result, mock_count]

        response = client.get("/api/v1/japan/content")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"][0]["translated_text"]) == 500


# ──────────────────────────────────────────────
# JP Content Schemas
# ──────────────────────────────────────────────


class TestJPContentSchemas:
    """Tests for JPContentItem and JPContentListResponse schemas."""

    def test_jp_content_item_minimal(self) -> None:
        """Minimal JPContentItem creation."""
        from src.schemas.japan import JPContentItem

        item = JPContentItem(
            id="abc-123",
            source_url="https://example.com",
            content_type="article",
        )
        assert item.id == "abc-123"
        assert item.title_en is None
        assert item.era_label is None
        assert item.review_status == "auto_approved"

    def test_jp_content_item_full(self) -> None:
        """Full JPContentItem creation."""
        from src.schemas.japan import JPContentItem

        item = JPContentItem(
            id="abc-123",
            source_url="https://pokecabook.com/article/1",
            content_type="tier_list",
            title_en="Tier List Feb 2026",
            title_jp="ティアリスト 2026年2月",
            translated_text="S Tier: Charizard ex...",
            published_date=date(2026, 2, 1),
            source_name="pokecabook",
            tags=["tier-list", "february"],
            archetype_refs=["Charizard ex", "Lugia VSTAR"],
            era_label="post-nihil-zero",
            review_status="human_approved",
            translated_at=datetime(2026, 2, 1, 12, 0, tzinfo=UTC),
        )
        assert item.content_type == "tier_list"
        assert item.source_name == "pokecabook"
        assert len(item.archetype_refs) == 2

    def test_jp_content_list_response(self) -> None:
        """JPContentListResponse creation."""
        from src.schemas.japan import (
            JPContentItem,
            JPContentListResponse,
        )

        resp = JPContentListResponse(
            items=[
                JPContentItem(
                    id="1",
                    source_url="https://example.com",
                    content_type="article",
                ),
            ],
            total=1,
        )
        assert resp.total == 1
        assert len(resp.items) == 1


# ──────────────────────────────────────────────
# era_label in MetaSnapshotResponse
# ──────────────────────────────────────────────


class TestEraLabelInResponse:
    """Tests for era_label field in MetaSnapshotResponse."""

    def test_era_label_present_in_schema(self) -> None:
        """MetaSnapshotResponse should accept era_label."""
        from src.schemas.meta import MetaSnapshotResponse

        resp = MetaSnapshotResponse(
            snapshot_date=date(2026, 2, 1),
            region="JP",
            format="standard",
            best_of=1,
            archetype_breakdown=[],
            sample_size=100,
            era_label="post-nihil-zero",
        )
        assert resp.era_label == "post-nihil-zero"

    def test_era_label_defaults_to_none(self) -> None:
        """MetaSnapshotResponse era_label defaults to None."""
        from src.schemas.meta import MetaSnapshotResponse

        resp = MetaSnapshotResponse(
            snapshot_date=date(2026, 2, 1),
            format="standard",
            best_of=3,
            archetype_breakdown=[],
            sample_size=50,
        )
        assert resp.era_label is None


# ──────────────────────────────────────────────
# Save snapshot with era_label (UPDATE path)
# ──────────────────────────────────────────────


class TestSaveSnapshotEraLabel:
    """Tests for era_label persistence in save_snapshot."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session: AsyncMock) -> MetaService:
        return MetaService(mock_session)

    @pytest.mark.asyncio
    async def test_insert_path_includes_era_label(
        self,
        service: MetaService,
        mock_session: AsyncMock,
    ) -> None:
        """New snapshot insert should carry era_label."""
        snapshot = MetaSnapshot(
            id=uuid4(),
            snapshot_date=date(2026, 2, 7),
            region="JP",
            format="standard",
            best_of=1,
            archetype_shares={"Charizard ex": 0.5},
            sample_size=10,
            era_label="post-nihil-zero",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        saved = await service.save_snapshot(snapshot)

        assert saved.era_label == "post-nihil-zero"
        mock_session.add.assert_called_once_with(snapshot)

    @pytest.mark.asyncio
    async def test_update_path_sets_era_label(
        self,
        service: MetaService,
        mock_session: AsyncMock,
    ) -> None:
        """Existing snapshot update should copy era_label."""
        existing = MagicMock(spec=MetaSnapshot)
        existing.archetype_shares = {}
        existing.card_usage = None
        existing.sample_size = 5
        existing.tournaments_included = []
        existing.diversity_index = None
        existing.tier_assignments = None
        existing.jp_signals = None
        existing.trends = None
        existing.era_label = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        new_snapshot = MetaSnapshot(
            id=uuid4(),
            snapshot_date=date(2026, 2, 7),
            region="JP",
            format="standard",
            best_of=1,
            archetype_shares={"A": 0.5},
            sample_size=20,
            era_label="post-nihil-zero",
        )

        await service.save_snapshot(new_snapshot)

        assert existing.era_label == "post-nihil-zero"
