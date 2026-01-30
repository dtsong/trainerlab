"""Health check endpoints."""

import asyncio
import time
from typing import Any

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from src.config import get_settings
from src.db.database import async_session_factory

router = APIRouter(prefix="/api/v1/health", tags=["health"])

settings = get_settings()

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
    """Database and Redis health check endpoint.

    Checks connectivity to PostgreSQL and Redis.
    Returns detailed status for each service.
    """
    # Run health checks concurrently
    db_task = asyncio.create_task(check_database_health())
    redis_task = asyncio.create_task(check_redis_health())

    db_result, redis_result = await asyncio.gather(db_task, redis_task)

    # Determine overall status
    all_ok = db_result["status"] == "ok" and redis_result["status"] == "ok"
    overall_status = "ok" if all_ok else "degraded"

    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "database": db_result,
        "redis": redis_result,
    }


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


async def check_redis_health() -> dict[str, Any]:
    """Check Redis connectivity.

    Returns:
        Dict with status and latency or error message.
    """
    try:
        import redis.asyncio as redis

        start = time.perf_counter()
        async with asyncio.timeout(HEALTH_CHECK_TIMEOUT):
            client = redis.from_url(settings.redis_url)
            await client.ping()
            await client.aclose()
        latency_ms = (time.perf_counter() - start) * 1000
        return {"status": "ok", "latency_ms": round(latency_ms, 2)}
    except TimeoutError:
        return {"status": "error", "error": "Connection timeout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
