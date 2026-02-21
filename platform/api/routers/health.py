from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis

from platform.api.database import get_db
from platform.api.config import settings

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    return {"status": "ok", "version": "0.1.0", "env": settings.AIMA_ENV}


@router.get("/health/detailed", summary="Detailed health check with dependency status")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    checks = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
