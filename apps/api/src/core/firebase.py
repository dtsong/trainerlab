"""Firebase Admin SDK initialization.

Uses Application Default Credentials (ADC) for authentication.
For local development, run: gcloud auth application-default login
For production on Cloud Run, ADC is automatically configured.
"""

import logging

import firebase_admin
from firebase_admin import auth, credentials

from src.config import get_settings

logger = logging.getLogger(__name__)

_app: firebase_admin.App | None = None


def init_firebase() -> firebase_admin.App | None:
    """Initialize Firebase Admin SDK.

    Uses Application Default Credentials (ADC). In production on GCP,
    this uses the service account assigned to Cloud Run. For local dev,
    use: gcloud auth application-default login

    Returns:
        Initialized Firebase app, or None if project_id not configured
    """
    global _app

    if _app is not None:
        return _app

    settings = get_settings()

    if not settings.firebase_project_id:
        logger.warning(
            "Firebase project ID not configured. Auth will not work. "
            "Set FIREBASE_PROJECT_ID in your environment."
        )
        return None

    try:
        # Use Application Default Credentials
        cred = credentials.ApplicationDefault()
        _app = firebase_admin.initialize_app(
            cred,
            options={"projectId": settings.firebase_project_id},
        )
        logger.info(
            "Firebase Admin SDK initialized for project: %s",
            settings.firebase_project_id,
        )
        return _app
    except Exception:
        logger.exception("Failed to initialize Firebase Admin SDK")
        return None


def get_firebase_app() -> firebase_admin.App | None:
    """Get the initialized Firebase app.

    Returns:
        Firebase app if initialized, None otherwise
    """
    return _app


async def verify_token(id_token: str) -> dict | None:
    """Verify a Firebase ID token.

    Args:
        id_token: The Firebase ID token from the client

    Returns:
        Decoded token claims if valid, None if invalid or Firebase not configured
    """
    if _app is None:
        logger.warning("Firebase not initialized, cannot verify token")
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except (
        auth.InvalidIdTokenError,
        auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError,
    ):
        logger.debug("Firebase token validation failed")
        return None
    except Exception:
        logger.exception("Unexpected error verifying Firebase token")
        return None
