"""Tests for the reprocess-archetypes pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config import Settings
from src.pipelines.reprocess_archetypes import (
    ReprocessArchetypesResult,
    reprocess_archetypes,
)
from src.routers.pipeline import router


def _make_placement(
    *,
    archetype: str = "Unknown",
    raw_archetype: str | None = None,
    raw_archetype_sprites: list[str] | None = None,
    decklist: list[dict] | None = None,
    detection_method: str | None = None,
) -> MagicMock:
    """Create a mock TournamentPlacement."""
    p = MagicMock()
    p.id = uuid4()
    p.archetype = archetype
    p.raw_archetype = raw_archetype
    p.raw_archetype_sprites = raw_archetype_sprites
    p.decklist = decklist
    p.archetype_detection_method = detection_method
    return p


def _mock_session(placements: list, total: int = 0):
    """Build a mock async session that returns placements."""
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    # First execute call returns placements
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = placements
    rows_mock = MagicMock()
    rows_mock.scalars.return_value = scalars_mock

    # Second execute call returns count
    count_mock = MagicMock()
    count_mock.scalar.return_value = total

    session.execute = AsyncMock(side_effect=[rows_mock, count_mock])
    session.commit = AsyncMock()

    return session


class TestReprocessArchetypesResult:
    """Tests for the ReprocessArchetypesResult dataclass."""

    def test_success_when_no_errors(self):
        result = ReprocessArchetypesResult(processed=10, updated=5)
        assert result.success

    def test_not_success_when_has_errors(self):
        result = ReprocessArchetypesResult(errors=["Query failed"])
        assert not result.success

    def test_default_values(self):
        result = ReprocessArchetypesResult()
        assert result.processed == 0
        assert result.updated == 0
        assert result.skipped == 0
        assert result.errors == []
        assert result.next_cursor is None
        assert result.total_remaining == 0
        assert result.success


class TestReprocessUpdatesArchetype:
    """Placement with sprites gets archetype updated."""

    @pytest.mark.asyncio
    async def test_reprocess_updates_archetype(self):
        placement = _make_placement(
            archetype="Unknown",
            raw_archetype="charizard-ex",
            raw_archetype_sprites=["https://r2.limitlesstcg.net/pokemon/charizard.png"],
        )

        session = _mock_session([placement], total=1)
        normalizer_mock = MagicMock()
        normalizer_mock.load_db_sprites = AsyncMock(return_value=0)
        normalizer_mock.resolve.return_value = (
            "Charizard ex",
            "charizard-ex",
            "sprite_lookup",
        )

        with (
            patch(
                "src.pipelines.reprocess_archetypes.async_session_factory",
                return_value=session,
            ),
            patch(
                "src.pipelines.reprocess_archetypes.ArchetypeNormalizer",
                return_value=normalizer_mock,
            ),
        ):
            result = await reprocess_archetypes(region="JP", batch_size=10)

        assert result.processed == 1
        assert result.updated == 1
        assert result.skipped == 0
        assert result.success

        # Verify placement was mutated
        assert placement.archetype == "Charizard ex"
        assert placement.archetype_detection_method == "sprite_lookup"
        session.commit.assert_awaited_once()


class TestReprocessSkipsNoSprites:
    """Placement without sprite URLs is skipped."""

    @pytest.mark.asyncio
    async def test_reprocess_skips_no_sprites(self):
        placement = _make_placement(
            archetype="Unknown",
            raw_archetype_sprites=None,
        )

        session = _mock_session([placement], total=1)
        normalizer_mock = MagicMock()
        normalizer_mock.load_db_sprites = AsyncMock(return_value=0)

        with (
            patch(
                "src.pipelines.reprocess_archetypes.async_session_factory",
                return_value=session,
            ),
            patch(
                "src.pipelines.reprocess_archetypes.ArchetypeNormalizer",
                return_value=normalizer_mock,
            ),
        ):
            result = await reprocess_archetypes(region="JP", batch_size=10)

        assert result.processed == 1
        assert result.updated == 0
        assert result.skipped == 1
        normalizer_mock.resolve.assert_not_called()


class TestReprocessDryRun:
    """Dry run logs changes but doesn't commit."""

    @pytest.mark.asyncio
    async def test_reprocess_dry_run(self):
        placement = _make_placement(
            archetype="Unknown",
            raw_archetype="charizard-ex",
            raw_archetype_sprites=["https://r2.limitlesstcg.net/pokemon/charizard.png"],
        )
        original_archetype = placement.archetype

        session = _mock_session([placement], total=1)
        normalizer_mock = MagicMock()
        normalizer_mock.load_db_sprites = AsyncMock(return_value=0)
        normalizer_mock.resolve.return_value = (
            "Charizard ex",
            "charizard-ex",
            "sprite_lookup",
        )

        with (
            patch(
                "src.pipelines.reprocess_archetypes.async_session_factory",
                return_value=session,
            ),
            patch(
                "src.pipelines.reprocess_archetypes.ArchetypeNormalizer",
                return_value=normalizer_mock,
            ),
        ):
            result = await reprocess_archetypes(
                region="JP", batch_size=10, dry_run=True
            )

        assert result.processed == 1
        assert result.updated == 1
        assert result.success

        # Placement should NOT be mutated in dry_run
        assert placement.archetype == original_archetype
        session.commit.assert_not_awaited()


class TestReprocessPagination:
    """Returns next_cursor when more results remain."""

    @pytest.mark.asyncio
    async def test_reprocess_pagination(self):
        placement = _make_placement(
            archetype="Unknown",
            raw_archetype_sprites=None,
        )

        # total=5 means 5 rows match, but we only fetch 1
        session = _mock_session([placement], total=5)
        normalizer_mock = MagicMock()
        normalizer_mock.load_db_sprites = AsyncMock(return_value=0)

        with (
            patch(
                "src.pipelines.reprocess_archetypes.async_session_factory",
                return_value=session,
            ),
            patch(
                "src.pipelines.reprocess_archetypes.ArchetypeNormalizer",
                return_value=normalizer_mock,
            ),
        ):
            result = await reprocess_archetypes(region="JP", batch_size=1)

        assert result.next_cursor is not None
        assert result.total_remaining == 4

    @pytest.mark.asyncio
    async def test_no_cursor_when_all_processed(self):
        placement = _make_placement(
            archetype="Unknown",
            raw_archetype_sprites=None,
        )

        # total=1 means exactly 1 row; batch fetches 1 => 0 remaining
        session = _mock_session([placement], total=1)
        normalizer_mock = MagicMock()
        normalizer_mock.load_db_sprites = AsyncMock(return_value=0)

        with (
            patch(
                "src.pipelines.reprocess_archetypes.async_session_factory",
                return_value=session,
            ),
            patch(
                "src.pipelines.reprocess_archetypes.ArchetypeNormalizer",
                return_value=normalizer_mock,
            ),
        ):
            result = await reprocess_archetypes(region="JP", batch_size=10)

        assert result.next_cursor is None
        assert result.total_remaining == 0


class TestReprocessForce:
    """force=True includes placements with detection_method set."""

    @pytest.mark.asyncio
    async def test_reprocess_force_reprocesses_already_labeled(
        self,
    ):
        placement = _make_placement(
            archetype="Old Name",
            raw_archetype="charizard-ex",
            raw_archetype_sprites=["https://r2.limitlesstcg.net/pokemon/charizard.png"],
            detection_method="text_label",
        )

        session = _mock_session([placement], total=1)
        normalizer_mock = MagicMock()
        normalizer_mock.load_db_sprites = AsyncMock(return_value=0)
        normalizer_mock.resolve.return_value = (
            "Charizard ex",
            "charizard-ex",
            "sprite_lookup",
        )

        with (
            patch(
                "src.pipelines.reprocess_archetypes.async_session_factory",
                return_value=session,
            ),
            patch(
                "src.pipelines.reprocess_archetypes.ArchetypeNormalizer",
                return_value=normalizer_mock,
            ),
        ):
            result = await reprocess_archetypes(region="JP", batch_size=10, force=True)

        assert result.processed == 1
        assert result.updated == 1
        assert placement.archetype == "Charizard ex"
        assert placement.archetype_detection_method == "sprite_lookup"


class TestReprocessSkipsUnchanged:
    """Skips placements where archetype hasn't changed."""

    @pytest.mark.asyncio
    async def test_skips_when_no_change(self):
        placement = _make_placement(
            archetype="Charizard ex",
            raw_archetype="charizard-ex",
            raw_archetype_sprites=["https://r2.limitlesstcg.net/pokemon/charizard.png"],
            detection_method="sprite_lookup",
        )

        session = _mock_session([placement], total=1)
        normalizer_mock = MagicMock()
        normalizer_mock.load_db_sprites = AsyncMock(return_value=0)
        normalizer_mock.resolve.return_value = (
            "Charizard ex",
            "charizard-ex",
            "sprite_lookup",
        )

        with (
            patch(
                "src.pipelines.reprocess_archetypes.async_session_factory",
                return_value=session,
            ),
            patch(
                "src.pipelines.reprocess_archetypes.ArchetypeNormalizer",
                return_value=normalizer_mock,
            ),
        ):
            result = await reprocess_archetypes(region="JP", batch_size=10, force=True)

        assert result.processed == 1
        assert result.updated == 0
        assert result.skipped == 1


class TestReprocessEndpoint:
    """Test the FastAPI endpoint via TestClient."""

    @pytest.fixture
    def bypass_settings(self) -> Settings:
        return Settings(scheduler_auth_bypass=True)

    @pytest.fixture
    def app(self, bypass_settings: Settings) -> FastAPI:
        app = FastAPI()
        app.include_router(router)

        async def override_settings():
            return bypass_settings

        from src.config import get_settings

        app.dependency_overrides[get_settings] = override_settings
        return app

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        return TestClient(app)

    def test_reprocess_endpoint_success(self, client: TestClient) -> None:
        from src.pipelines.reprocess_archetypes import (
            ReprocessArchetypesResult as InternalResult,
        )

        mock_result = InternalResult(
            processed=50,
            updated=30,
            skipped=20,
            next_cursor="abc-123",
            total_remaining=100,
        )

        with patch(
            "src.routers.pipeline.reprocess_archetypes",
            new_callable=AsyncMock,
        ) as mock_fn:
            mock_fn.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/reprocess-archetypes",
                json={
                    "region": "JP",
                    "batch_size": 50,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["processed"] == 50
            assert data["updated"] == 30
            assert data["skipped"] == 20
            assert data["next_cursor"] == "abc-123"
            assert data["total_remaining"] == 100
            assert data["success"] is True

    def test_reprocess_endpoint_defaults(self, client: TestClient) -> None:
        from src.pipelines.reprocess_archetypes import (
            ReprocessArchetypesResult as InternalResult,
        )

        mock_result = InternalResult()

        with patch(
            "src.routers.pipeline.reprocess_archetypes",
            new_callable=AsyncMock,
        ) as mock_fn:
            mock_fn.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/reprocess-archetypes",
                json={},
            )

            assert response.status_code == 200
            mock_fn.assert_called_once_with(
                region="JP",
                batch_size=200,
                cursor=None,
                force=False,
                dry_run=False,
            )

    def test_reprocess_endpoint_validates_batch_size(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/pipeline/reprocess-archetypes",
            json={"batch_size": 5000},
        )
        assert response.status_code == 422

    def test_reprocess_endpoint_with_errors(self, client: TestClient) -> None:
        from src.pipelines.reprocess_archetypes import (
            ReprocessArchetypesResult as InternalResult,
        )

        mock_result = InternalResult(errors=["Query failed: connection reset"])

        with patch(
            "src.routers.pipeline.reprocess_archetypes",
            new_callable=AsyncMock,
        ) as mock_fn:
            mock_fn.return_value = mock_result

            response = client.post(
                "/api/v1/pipeline/reprocess-archetypes",
                json={},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert len(data["errors"]) == 1
