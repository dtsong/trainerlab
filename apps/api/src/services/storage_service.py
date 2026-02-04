"""Cloud Storage service for file uploads."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from google.cloud import storage
from google.cloud.exceptions import NotFound

from src.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for Google Cloud Storage operations."""

    def __init__(self, bucket_name: str | None = None) -> None:
        """Initialize storage service.

        Args:
            bucket_name: GCS bucket name (defaults to settings)
        """
        settings = get_settings()
        self.bucket_name = bucket_name or settings.exports_bucket
        self._client: storage.Client | None = None
        self._bucket: storage.Bucket | None = None

    @property
    def client(self) -> storage.Client:
        """Lazy-initialize storage client."""
        if self._client is None:
            self._client = storage.Client()
        return self._client

    @property
    def bucket(self) -> storage.Bucket:
        """Lazy-initialize bucket."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    async def upload_export(
        self,
        data: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """Upload export file to GCS.

        Args:
            data: File content as bytes
            filename: Target filename
            content_type: MIME content type

        Returns:
            Public URL for the uploaded file
        """
        blob_path = f"exports/{filename}"
        blob = self.bucket.blob(blob_path)

        # Run upload in thread to not block async loop
        await asyncio.to_thread(
            blob.upload_from_string,
            data,
            content_type=content_type,
        )

        logger.info("Uploaded export to gs://%s/%s", self.bucket_name, blob_path)
        return blob.public_url

    async def generate_signed_url(
        self,
        filename: str,
        expiration_hours: int = 24,
    ) -> str:
        """Generate a signed URL for download.

        Args:
            filename: File path in bucket
            expiration_hours: Hours until URL expires

        Returns:
            Signed URL for download
        """
        blob_path = f"exports/{filename}"
        blob = self.bucket.blob(blob_path)

        expiration = timedelta(hours=expiration_hours)

        url = await asyncio.to_thread(
            blob.generate_signed_url,
            expiration=expiration,
            method="GET",
        )

        return url

    async def delete_export(self, filename: str) -> bool:
        """Delete an export file.

        Args:
            filename: File path in bucket

        Returns:
            True if deleted, False if not found
        """
        blob_path = f"exports/{filename}"
        blob = self.bucket.blob(blob_path)

        try:
            await asyncio.to_thread(blob.delete)
            logger.info("Deleted export gs://%s/%s", self.bucket_name, blob_path)
            return True
        except NotFound:
            logger.warning("Export not found: gs://%s/%s", self.bucket_name, blob_path)
            return False

    async def list_exports(self, prefix: str = "") -> list[dict]:
        """List export files.

        Args:
            prefix: Filter by prefix

        Returns:
            List of file metadata
        """
        blob_prefix = f"exports/{prefix}" if prefix else "exports/"

        blobs = await asyncio.to_thread(
            lambda: list(self.client.list_blobs(self.bucket_name, prefix=blob_prefix))
        )

        return [
            {
                "name": blob.name,
                "size": blob.size,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "content_type": blob.content_type,
            }
            for blob in blobs
        ]

    async def cleanup_expired_exports(self, max_age_hours: int = 24) -> int:
        """Delete exports older than max age.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of files deleted
        """
        cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
        blobs = await asyncio.to_thread(
            lambda: list(self.client.list_blobs(self.bucket_name, prefix="exports/"))
        )

        deleted = 0
        for blob in blobs:
            if blob.time_created and blob.time_created < cutoff:
                try:
                    await asyncio.to_thread(blob.delete)
                    deleted += 1
                except Exception:
                    logger.exception("Failed to delete expired export: %s", blob.name)

        logger.info("Cleaned up %d expired exports", deleted)
        return deleted
