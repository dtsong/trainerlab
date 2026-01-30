"""Set-related Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SetResponse(BaseModel):
    """Full schema for card set data."""

    model_config = ConfigDict(from_attributes=True)

    # Identifiers
    id: str
    name: str
    series: str

    # Release info
    release_date: date | None = None
    release_date_jp: date | None = None
    card_count: int | None = None

    # Images
    logo_url: str | None = None
    symbol_url: str | None = None

    # Legalities
    legalities: dict[str, str] | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
