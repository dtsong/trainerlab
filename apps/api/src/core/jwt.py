"""JWT verification for NextAuth.js HS256 tokens.

Verifies tokens signed by NextAuth.js using the shared NEXTAUTH_SECRET.
"""

import logging
from dataclasses import dataclass

from jose import JWTError, jwt

from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DecodedToken:
    """Decoded NextAuth.js JWT with typed claims."""

    sub: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None


class TokenVerificationError(Exception):
    """Raised when token verification fails due to infrastructure issues.

    This is distinct from invalid/expired tokens - it indicates
    a configuration problem (missing secret). Callers should
    return 503 Service Unavailable, not 401 Unauthorized.
    """


def verify_token(token: str) -> DecodedToken | None:
    """Verify an HS256-signed NextAuth.js JWT.

    Args:
        token: The raw JWT string from the Authorization header.

    Returns:
        DecodedToken with typed claims if valid, None if invalid/expired.

    Raises:
        TokenVerificationError: If NEXTAUTH_SECRET is not configured.
    """
    settings = get_settings()

    if not settings.nextauth_secret:
        logger.error("NEXTAUTH_SECRET not configured - cannot verify tokens")
        raise TokenVerificationError(
            "Authentication service not configured. Set NEXTAUTH_SECRET."
        )

    try:
        payload = jwt.decode(
            token,
            settings.nextauth_secret,
            algorithms=["HS256"],
        )
    except JWTError as e:
        logger.info("JWT verification failed: %s", e)
        return None

    sub = payload.get("sub")
    if not sub:
        logger.warning("Token missing sub claim")
        return None

    return DecodedToken(
        sub=sub,
        email=payload.get("email"),
        name=payload.get("name"),
        picture=payload.get("picture"),
    )
