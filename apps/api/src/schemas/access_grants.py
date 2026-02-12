from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class AccessGrantUpdateRequest(BaseModel):
    email: EmailStr
    note: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class AccessGrantResponse(BaseModel):
    id: str
    email: str
    is_beta_tester: bool
    is_subscriber: bool

    note: str | None = None
    created_by_admin_email: str | None = None

    has_user: bool
    user_id: str | None = None

    created_at: datetime
    updated_at: datetime
