"""Cloud Tasks service for enqueuing tournament processing tasks."""

import hashlib
import json
import logging

from google.cloud import tasks_v2

from src.config import get_settings

logger = logging.getLogger(__name__)


class CloudTasksService:
    """Service for enqueuing tournament processing tasks via Cloud Tasks."""

    def __init__(self) -> None:
        settings = get_settings()
        self.queue_path = settings.cloud_tasks_queue_path
        self.cloud_run_url = settings.cloud_run_url
        self.api_service_account = settings.api_service_account
        self._client: tasks_v2.CloudTasksAsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        """Check if Cloud Tasks is configured (vs local dev)."""
        return bool(self.queue_path and self.cloud_run_url)

    async def enqueue_tournament(self, tournament_metadata: dict) -> str | None:
        """Enqueue a single tournament for processing via Cloud Tasks.

        Task name is derived from source_url hash for built-in deduplication.

        Args:
            tournament_metadata: Tournament data dict with at least 'source_url'.

        Returns:
            Task name if enqueued, None if Cloud Tasks not configured.
        """
        if not self.is_configured:
            logger.debug("Cloud Tasks not configured, skipping enqueue")
            return None

        source_url = tournament_metadata["source_url"]
        task_id = self._task_id_from_url(source_url)

        # Build the HTTP request targeting the process endpoint
        url = f"{self.cloud_run_url}/api/v1/pipeline/process-tournament"
        body = json.dumps(tournament_metadata).encode()

        task = tasks_v2.Task(
            name=f"{self.queue_path}/tasks/{task_id}",
            http_request=tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=url,
                headers={"Content-Type": "application/json"},
                body=body,
                oidc_token=tasks_v2.OidcToken(
                    service_account_email=self.api_service_account,
                    audience=self.cloud_run_url,
                ),
            ),
        )

        client = self._get_client()

        try:
            created = await client.create_task(
                parent=self.queue_path,
                task=task,
            )
            logger.info("Enqueued task %s for %s", task_id, source_url)
            return created.name
        except Exception as e:
            # AlreadyExists means dedup worked — task was already enqueued
            if "ALREADY_EXISTS" in str(e):
                logger.info("Task already exists (dedup): %s", task_id)
                return task_id
            logger.error("Failed to enqueue task for %s: %s", source_url, e)
            raise

    def _get_client(self) -> tasks_v2.CloudTasksAsyncClient:
        if self._client is None:
            self._client = tasks_v2.CloudTasksAsyncClient()
        return self._client

    @staticmethod
    def _task_id_from_url(source_url: str) -> str:
        """Generate a deterministic task ID from a source URL.

        Uses SHA-256 prefix for deduplication. Cloud Tasks rejects
        duplicate task names within the dedup window.
        """
        url_hash = hashlib.sha256(source_url.encode()).hexdigest()[:16]
        return f"tournament-{url_hash}"
