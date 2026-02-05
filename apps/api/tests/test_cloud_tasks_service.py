"""Tests for CloudTasksService."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.cloud_tasks import CloudTasksService


def _make_configured_service():
    """Create a CloudTasksService with all settings configured."""
    with patch("src.services.cloud_tasks.get_settings") as mock_settings:
        settings = MagicMock()
        settings.cloud_tasks_queue_path = "projects/p/locations/l/queues/q"
        settings.cloud_run_url = "https://api.example.com"
        settings.api_service_account = "sa@example.iam.gserviceaccount.com"
        mock_settings.return_value = settings
        return CloudTasksService()


class TestEnqueueTournament:
    """Tests for enqueue_tournament covering lines 44-80."""

    @pytest.mark.asyncio
    async def test_enqueue_success(self) -> None:
        """Should enqueue task and return task name on success."""
        service = _make_configured_service()

        mock_client = AsyncMock()
        created_task = MagicMock()
        created_task.name = "projects/p/locations/l/queues/q/tasks/tournament-abc123"
        mock_client.create_task.return_value = created_task
        service._client = mock_client

        metadata = {
            "source_url": "https://play.limitlesstcg.com/tournament/99999",
            "name": "Test Regional",
        }

        result = await service.enqueue_tournament(metadata)

        assert result == created_task.name
        mock_client.create_task.assert_called_once()
        call_kwargs = mock_client.create_task.call_args[1]
        assert call_kwargs["parent"] == service.queue_path

    @pytest.mark.asyncio
    async def test_enqueue_already_exists(self) -> None:
        """Should return task_id when ALREADY_EXISTS error occurs (dedup)."""
        service = _make_configured_service()

        mock_client = AsyncMock()
        mock_client.create_task.side_effect = Exception(
            "409 ALREADY_EXISTS: task already exists"
        )
        service._client = mock_client

        metadata = {"source_url": "https://play.limitlesstcg.com/tournament/12345"}
        result = await service.enqueue_tournament(metadata)

        # Should return the task_id (not None, not raise)
        assert result is not None
        assert result.startswith("tournament-")

    @pytest.mark.asyncio
    async def test_enqueue_raises_on_other_error(self) -> None:
        """Should re-raise non-dedup errors."""
        service = _make_configured_service()

        mock_client = AsyncMock()
        mock_client.create_task.side_effect = Exception("500 INTERNAL")
        service._client = mock_client

        metadata = {"source_url": "https://play.limitlesstcg.com/tournament/12345"}

        with pytest.raises(Exception, match="500 INTERNAL"):
            await service.enqueue_tournament(metadata)

    @pytest.mark.asyncio
    async def test_enqueue_builds_correct_url(self) -> None:
        """Should build the correct processing URL."""
        service = _make_configured_service()

        mock_client = AsyncMock()
        created_task = MagicMock()
        created_task.name = "task-name"
        mock_client.create_task.return_value = created_task
        service._client = mock_client

        metadata = {"source_url": "https://example.com/t/1"}
        await service.enqueue_tournament(metadata)

        call_kwargs = mock_client.create_task.call_args[1]
        task = call_kwargs["task"]
        assert (
            task.http_request.url
            == "https://api.example.com/api/v1/pipeline/process-tournament"
        )
        body_dict = json.loads(task.http_request.body)
        assert body_dict["source_url"] == "https://example.com/t/1"


class TestGetClient:
    """Tests for _get_client covering lines 83-85."""

    def test_creates_client_on_first_call(self) -> None:
        """Should create client on first call."""
        service = _make_configured_service()
        assert service._client is None

        with patch("src.services.cloud_tasks.tasks_v2") as mock_tasks_v2:
            mock_async_client = MagicMock()
            mock_tasks_v2.CloudTasksAsyncClient.return_value = mock_async_client

            client = service._get_client()
            assert client is mock_async_client
            mock_tasks_v2.CloudTasksAsyncClient.assert_called_once()

    def test_reuses_client_on_subsequent_calls(self) -> None:
        """Should reuse existing client on subsequent calls."""
        service = _make_configured_service()
        mock_client = MagicMock()
        service._client = mock_client

        client = service._get_client()
        assert client is mock_client
