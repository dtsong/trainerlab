from __future__ import annotations

import inspect
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.admin_audit_event import AdminAuditEvent
from src.models.user import User


def _safe_client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


async def record_admin_audit_event(
    db: AsyncSession,
    *,
    action: str,
    actor: User,
    target: User | None,
    target_email: str,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AdminAuditEvent(
        action=action,
        actor_user_id=getattr(actor, "id", None),
        actor_email=actor.email,
        target_user_id=(getattr(target, "id", None) if target else None),
        target_email=target_email,
        ip_address=_safe_client_ip(request) if request else None,
        user_agent=(request.headers.get("user-agent") if request else None),
        path=(str(request.url.path) if request else None),
        correlation_id=(request.headers.get("x-correlation-id") if request else None),
        event_metadata=metadata,
    )

    # AsyncSession.add() is sync, but many tests mock the session with AsyncMock.
    # Handle both without leaking un-awaited coroutine warnings.
    result = db.add(event)
    if inspect.isawaitable(result):
        await result
