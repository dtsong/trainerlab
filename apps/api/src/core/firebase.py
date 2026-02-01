"""Firebase Admin SDK initialization.

Uses Application Default Credentials (ADC) for authentication.
For local development, run: gcloud auth application-default login
For production on Cloud Run, ADC is automatically configured.
"""

import asyncio
import logging

import firebase_admin
from firebase_admin import auth, credentials
from google.auth import exceptions as google_auth_exceptions

from src.config import get_settings

logger = logging.getLogger(__name__)


class FirebaseInitError(Exception):
    """Raised when Firebase initialization fails in production."""

    pass


class TokenVerificationError(Exception):
    """Raised when token verification fails due to infrastructure issues.

    This is distinct from invalid/expired/revoked tokens - it indicates
    a problem with Firebase service connectivity or unexpected SDK errors.
    Callers should return 503 Service Unavailable, not 401 Unauthorized.
    """

    pass


_app: firebase_admin.App | None = None


def init_firebase() -> firebase_admin.App | None:
    """Initialize Firebase Admin SDK.

    Uses Application Default Credentials (ADC). In production on GCP,
    this uses the service account assigned to Cloud Run. For local dev,
    use: gcloud auth application-default login

    Returns:
        Initialized Firebase app, or None if project_id not configured

    Raises:
        FirebaseInitError: In production, if project_id is configured but
            initialization fails (credentials error, etc.)
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
    except google_auth_exceptions.DefaultCredentialsError as e:
        msg = (
            f"Firebase ADC not configured: {e}. "
            "Run 'gcloud auth application-default login' for local dev."
        )
        logger.error(msg)
        if settings.is_production:
            raise FirebaseInitError(msg) from e
        return None
    except ValueError as e:
        msg = f"Firebase initialization error: {e}"
        logger.error(msg)
        if settings.is_production:
            raise FirebaseInitError(msg) from e
        return None
    except Exception as e:
        msg = f"Unexpected error initializing Firebase: {type(e).__name__}: {e}"
        logger.exception(msg)
        if settings.is_production:
            raise FirebaseInitError(msg) from e
        return None


def get_firebase_app() -> firebase_admin.App | None:
    """Get the initialized Firebase app.

    Returns:
        Firebase app if initialized, None otherwise
    """
    return _app


async def verify_token(id_token: str) -> dict | None:
    """Verify a Firebase ID token.

    Runs the synchronous Firebase SDK verification in a thread pool
    to avoid blocking the event loop. Also checks if the token has been
    revoked (e.g., after password change or explicit revocation).

    Args:
        id_token: The Firebase ID token from the client

    Returns:
        Decoded token claims if valid, None if invalid/expired/revoked

    Raises:
        TokenVerificationError: If verification fails due to infrastructure
            issues (Firebase not initialized, network timeout, service
            unavailable, etc.). Callers should return 503, not 401.
    """
    if _app is None:
        logger.error("Firebase not initialized - cannot verify tokens")
        raise TokenVerificationError(
            "Authentication service not configured. Contact support."
        )

    try:
        decoded_token = await asyncio.to_thread(
            auth.verify_id_token, id_token, check_revoked=True
        )
        return decoded_token
    except auth.InvalidIdTokenError as e:
        logger.info("Firebase token invalid: %s", e)
        return None
    except auth.ExpiredIdTokenError as e:
        logger.info("Firebase token expired: %s", e)
        return None
    except auth.RevokedIdTokenError as e:
        logger.warning("Firebase token revoked: %s", e)
        return None
    except auth.CertificateFetchError as e:
        # Infrastructure issue: can't fetch Google's public keys
        logger.error("Failed to fetch Firebase certificates: %s", e)
        raise TokenVerificationError(
            "Unable to verify token: certificate fetch failed"
        ) from e
    except Exception as e:
        # Unexpected error - treat as infrastructure failure, not invalid token
        logger.exception("Unexpected error verifying token: %s", type(e).__name__)
        raise TokenVerificationError(
            f"Unable to verify token: {type(e).__name__}"
        ) from e
