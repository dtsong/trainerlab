"""Waitlist endpoints for Research Pass email capture."""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.exc import IntegrityError

from src.db.database import async_session_factory
from src.models.waitlist import WaitlistEntry

router = APIRouter(prefix="/api/v1/waitlist", tags=["waitlist"])
limiter = Limiter(key_func=get_remote_address)


class WaitlistRequest(BaseModel):
    """Request to join the waitlist."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()


class WaitlistResponse(BaseModel):
    """Response after joining waitlist."""

    success: bool
    message: str


@router.post("", response_model=WaitlistResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def join_waitlist(request: Request, body: WaitlistRequest) -> WaitlistResponse:
    """Add an email to the Research Pass waitlist.

    Returns success even if email already exists (for privacy).
    """
    async with async_session_factory() as session:
        try:
            entry = WaitlistEntry(email=body.email)
            session.add(entry)
            await session.commit()
            return WaitlistResponse(
                success=True,
                message="You're on the list! We'll be in touch soon.",
            )
        except IntegrityError:
            # Email already exists - return success for privacy
            await session.rollback()
            return WaitlistResponse(
                success=True,
                message="You're on the list! We'll be in touch soon.",
            )
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to join waitlist. Please try again.",
            ) from e
