"""Operational endpoints for automation.

These endpoints are intentionally low-scope and protected by a shared secret
token (not admin JWT), to support scheduled checks/alerts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.dependencies.ops_alerts import require_readiness_alert_token
from src.models.meta_snapshot import MetaSnapshot
from src.models.tournament import Tournament
from src.schemas.readiness import TPCIReadinessResponse
from src.services.readiness import evaluate_tpci_post_major_readiness

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])


@router.get(
    "/readiness/tpci",
    response_model=TPCIReadinessResponse,
    dependencies=[Depends(require_readiness_alert_token)],
)
async def tpci_readiness_ops(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TPCIReadinessResponse:
    """Readiness check for scheduled alerts.

    Uses the same evaluation logic as the admin readiness endpoint.
    """
    now_utc = datetime.now(UTC)
    today = now_utc.date()
    official_tiers = ["major", "worlds", "international", "regional", "special"]

    latest_major_end = await db.scalar(
        select(func.max(Tournament.date)).where(Tournament.tier.in_(official_tiers))
    )

    snapshot = await db.scalar(
        select(MetaSnapshot)
        .where(MetaSnapshot.tournament_type == "official")
        .where(MetaSnapshot.region.is_(None))
        .where(MetaSnapshot.format == "standard")
        .where(MetaSnapshot.best_of == 3)
        .order_by(MetaSnapshot.snapshot_date.desc())
        .limit(1)
    )

    snapshot_date = snapshot.snapshot_date if snapshot else None
    sample_size = snapshot.sample_size if snapshot else None

    evaluation = evaluate_tpci_post_major_readiness(
        latest_major_end_date=latest_major_end,
        snapshot_date=snapshot_date,
        sample_size=sample_size,
        now_utc=now_utc,
    )

    return TPCIReadinessResponse(
        status=evaluation["status"],
        checked_at=today,
        latest_major_end_date=latest_major_end,
        deadline_date=evaluation.get("deadline_date"),
        snapshot_date=snapshot_date,
        sample_size=sample_size,
        meets_partial_threshold=evaluation["meets_partial"],
        meets_fresh_threshold=evaluation["meets_fresh"],
        deadline_missed=evaluation["deadline_missed"],
        message=evaluation["message"],
    )
