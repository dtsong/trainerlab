"""Health check endpoints."""

import asyncio
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import async_session_factory, get_db
from src.schemas.health import PipelineHealthResponse
from src.services.health_service import PipelineHealthService

router = APIRouter(prefix="/api/v1/health", tags=["health"])

# Timeout for health checks (in seconds)
HEALTH_CHECK_TIMEOUT = 5.0


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns status and version. No authentication required.
    Does not check external dependencies for fast response.
    """
    return {"status": "ok", "version": "0.0.1"}


@router.get("/db")
async def db_health_check(response: Response) -> dict[str, Any]:
    """Database health check endpoint.

    Checks connectivity to PostgreSQL.
    Returns detailed status for the database.
    """
    db_result = await check_database_health()

    overall_status = "ok" if db_result["status"] == "ok" else "degraded"

    if db_result["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "database": db_result,
    }


@router.get("/pipeline", response_model=PipelineHealthResponse)
async def pipeline_health_check(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db)],
    detail: str | None = None,
) -> PipelineHealthResponse:
    """Pipeline health check endpoint.

    Returns scrape freshness, meta snapshot staleness,
    and archetype detection quality metrics.
    No authentication required (read-only diagnostic).

    Query params:
        detail: Set to "verbose" for extended diagnostics
            (Unknown placements, text_label fallbacks, trends).
    """
    service = PipelineHealthService(session)
    health = await service.get_pipeline_health(
        verbose=(detail == "verbose"),
    )

    if health.status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health


async def check_database_health() -> dict[str, Any]:
    """Check PostgreSQL database connectivity.

    Returns:
        Dict with status and latency or error message.
    """
    try:
        start = time.perf_counter()
        async with asyncio.timeout(HEALTH_CHECK_TIMEOUT):
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency_ms, 2)}
    except TimeoutError:
        return {"status": "error", "error": "Connection timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
