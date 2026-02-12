"""Waitlist endpoints for launch updates + access requests."""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from src.db.database import async_session_factory
from src.models.waitlist import WaitlistEntry

router = APIRouter(prefix="/api/v1/waitlist", tags=["waitlist"])
limiter = Limiter(key_func=get_remote_address)


class WaitlistRequest(BaseModel):
    """Request to join the waitlist."""

    email: EmailStr
    note: str | None = None
    intent: str | None = None
    source: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        return cleaned[:1000]

    @field_validator("intent", "source")
    @classmethod
    def validate_small_fields(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        return cleaned[:64]


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
            stmt = insert(WaitlistEntry).values(
                email=body.email,
                note=body.note,
                intent=body.intent,
                source=body.source,
                request_count=1,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[WaitlistEntry.email],
                set_={
                    "request_count": WaitlistEntry.request_count + 1,
                    "note": func.coalesce(WaitlistEntry.note, stmt.excluded.note),
                    "intent": func.coalesce(WaitlistEntry.intent, stmt.excluded.intent),
                    "source": func.coalesce(WaitlistEntry.source, stmt.excluded.source),
                    "updated_at": func.now(),
                },
            )
            await session.execute(stmt)
            await session.commit()
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
