"""Tests for StorageService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.cloud.exceptions import NotFound

from src.services.storage_service import StorageService


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.exports_bucket = "test-exports-bucket"
    settings.og_images_bucket = "test-og-images-bucket"
    return settings


@pytest.fixture
def mock_blob():
    """Create a mock blob."""
    blob = MagicMock()
    blob.public_url = "https://storage.googleapis.com/test-bucket/exports/test.json"
    blob.upload_from_string = MagicMock()
    blob.generate_signed_url = MagicMock(return_value="https://signed-url.example.com")
    blob.delete = MagicMock()
    blob.name = "exports/test.json"
    blob.size = 1024
    blob.time_created = datetime.now(UTC)
    blob.content_type = "application/json"
    return blob


@pytest.fixture
def mock_bucket(mock_blob):
    """Create a mock bucket."""
    bucket = MagicMock()
    bucket.blob.return_value = mock_blob
    return bucket


@pytest.fixture
def mock_client(mock_bucket):
    """Create a mock storage client."""
    client = MagicMock()
    client.bucket.return_value = mock_bucket
    client.list_blobs.return_value = []
    return client


class TestStorageServiceInit:
    """Tests for StorageService initialization."""

    def test_uses_default_bucket_from_settings(self, mock_settings):
        """Test using default bucket from settings."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()

        assert service.bucket_name == "test-exports-bucket"

    def test_uses_custom_bucket(self, mock_settings):
        """Test using custom bucket name."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService(bucket_name="custom-bucket")

        assert service.bucket_name == "custom-bucket"


class TestUploadExport:
    """Tests for upload_export method."""

    @pytest.mark.asyncio
    async def test_uploads_file_to_gcs(
        self, mock_settings, mock_client, mock_bucket, mock_blob
    ):
        """Test uploading file to GCS."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.upload_export(
                data=b'{"test": "data"}',
                filename="test.json",
                content_type="application/json",
            )

        mock_bucket.blob.assert_called_once_with("exports/test.json")
        assert result == mock_blob.public_url

    @pytest.mark.asyncio
    async def test_upload_with_csv_content_type(
        self, mock_settings, mock_client, mock_bucket, mock_blob
    ):
        """Test uploading CSV file."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            await service.upload_export(
                data=b"col1,col2\nval1,val2",
                filename="test.csv",
                content_type="text/csv",
            )

        mock_bucket.blob.assert_called_once_with("exports/test.csv")


class TestGenerateSignedUrl:
    """Tests for generate_signed_url method."""

    @pytest.mark.asyncio
    async def test_generates_signed_url(
        self, mock_settings, mock_client, mock_bucket, mock_blob
    ):
        """Test generating signed URL."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.generate_signed_url("test.json")

        mock_bucket.blob.assert_called_once_with("exports/test.json")
        assert result == "https://signed-url.example.com"

    @pytest.mark.asyncio
    async def test_uses_custom_expiration(
        self, mock_settings, mock_client, mock_bucket, mock_blob
    ):
        """Test using custom expiration time."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            await service.generate_signed_url("test.json", expiration_hours=48)

        call_kwargs = mock_blob.generate_signed_url.call_args[1]
        assert call_kwargs["expiration"] == timedelta(hours=48)


class TestDeleteExport:
    """Tests for delete_export method."""

    @pytest.mark.asyncio
    async def test_deletes_existing_file(
        self, mock_settings, mock_client, mock_bucket, mock_blob
    ):
        """Test deleting existing file."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.delete_export("test.json")

        assert result is True
        mock_bucket.blob.assert_called_once_with("exports/test.json")

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(
        self, mock_settings, mock_client, mock_bucket, mock_blob
    ):
        """Test returning False when file not found."""
        mock_blob.delete.side_effect = NotFound("Not found")

        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.delete_export("nonexistent.json")

        assert result is False


class TestListExports:
    """Tests for list_exports method."""

    @pytest.mark.asyncio
    async def test_lists_all_exports(
        self, mock_settings, mock_client, mock_bucket, mock_blob
    ):
        """Test listing all exports."""
        mock_client.list_blobs.return_value = [mock_blob]

        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.list_exports()

        assert len(result) == 1
        assert result[0]["name"] == "exports/test.json"
        assert result[0]["size"] == 1024

    @pytest.mark.asyncio
    async def test_lists_exports_with_prefix(
        self, mock_settings, mock_client, mock_bucket
    ):
        """Test listing exports with prefix filter."""
        mock_client.list_blobs.return_value = []

        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            await service.list_exports(prefix="2024-01")

        mock_client.list_blobs.assert_called_once()
        call_args = mock_client.list_blobs.call_args
        assert "exports/2024-01" in call_args[1]["prefix"]

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_files(
        self, mock_settings, mock_client, mock_bucket
    ):
        """Test returning empty list when no files exist."""
        mock_client.list_blobs.return_value = []

        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.list_exports()

        assert result == []


class TestCleanupExpiredExports:
    """Tests for cleanup_expired_exports method."""

    @pytest.mark.asyncio
    async def test_deletes_expired_files(
        self, mock_settings, mock_client, mock_bucket
    ):
        """Test deleting expired files."""
        old_blob = MagicMock()
        old_blob.time_created = datetime.now(UTC) - timedelta(hours=48)
        old_blob.delete = MagicMock()
        old_blob.name = "exports/old.json"

        new_blob = MagicMock()
        new_blob.time_created = datetime.now(UTC) - timedelta(hours=1)
        new_blob.delete = MagicMock()
        new_blob.name = "exports/new.json"

        mock_client.list_blobs.return_value = [old_blob, new_blob]

        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.cleanup_expired_exports(max_age_hours=24)

        assert result == 1
        old_blob.delete.assert_called_once()
        new_blob.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_delete_errors(
        self, mock_settings, mock_client, mock_bucket
    ):
        """Test handling delete errors gracefully."""
        old_blob = MagicMock()
        old_blob.time_created = datetime.now(UTC) - timedelta(hours=48)
        old_blob.delete.side_effect = Exception("Delete failed")
        old_blob.name = "exports/old.json"

        mock_client.list_blobs.return_value = [old_blob]

        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.cleanup_expired_exports(max_age_hours=24)

        assert result == 0

    @pytest.mark.asyncio
    async def test_uses_custom_max_age(
        self, mock_settings, mock_client, mock_bucket
    ):
        """Test using custom max age."""
        blob = MagicMock()
        blob.time_created = datetime.now(UTC) - timedelta(hours=50)
        blob.delete = MagicMock()
        blob.name = "exports/test.json"

        mock_client.list_blobs.return_value = [blob]

        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client
            service._bucket = mock_bucket

            result = await service.cleanup_expired_exports(max_age_hours=48)

        assert result == 1


class TestLazyInitialization:
    """Tests for lazy initialization of client and bucket."""

    def test_client_lazy_initialized(self, mock_settings):
        """Test that client is lazily initialized."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()

        assert service._client is None

        with patch("src.services.storage_service.storage.Client") as mock_client_class:
            mock_client_class.return_value = MagicMock()
            _ = service.client

        mock_client_class.assert_called_once()

    def test_bucket_lazy_initialized(self, mock_settings, mock_client):
        """Test that bucket is lazily initialized."""
        with patch("src.services.storage_service.get_settings") as mock_get:
            mock_get.return_value = mock_settings
            service = StorageService()
            service._client = mock_client

        assert service._bucket is None

        _ = service.bucket

        mock_client.bucket.assert_called_once_with("test-exports-bucket")
