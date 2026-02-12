from datetime import datetime

from pydantic import BaseModel


class AdminAuditEventResponse(BaseModel):
    id: str
    created_at: datetime
    action: str

    actor_user_id: str | None = None
    actor_email: str

    target_user_id: str | None = None
    target_email: str

    ip_address: str | None = None
    user_agent: str | None = None
    path: str | None = None
    correlation_id: str | None = None
    metadata: dict | None = None
