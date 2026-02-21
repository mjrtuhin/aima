from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from platform.api.config import settings
from platform.api.database import get_engine, Base
from platform.api.routers import (
    health,
    connectors,
    customers,
    segments,
    campaigns,
    content,
    brand_monitor,
    attribution,
    clv_churn,
    agent,
    alerts,
    import_data,
)

log = structlog.get_logger()

DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from sqlalchemy import text

    log.info("AIMA API starting", env=settings.AIMA_ENV)
    _engine = get_engine()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "INSERT INTO organizations (id, name, slug) "
                "VALUES (:id, :name, :slug) ON CONFLICT (id) DO NOTHING"
            ),
            {"id": DEMO_ORG_ID, "name": "Demo Organization", "slug": "demo"},
        )
    log.info("Database tables verified and demo org seeded")
    yield
    log.info("AIMA API shutting down")
    await get_engine().dispose()


app = FastAPI(
    title="AIMA - AI Marketing Analytics",
    description="Open-source AI marketing intelligence platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(health.router, tags=["Health"])
app.include_router(connectors.router, prefix=settings.API_PREFIX, tags=["Connectors"])
app.include_router(customers.router, prefix=settings.API_PREFIX, tags=["Customers"])
app.include_router(segments.router, prefix=settings.API_PREFIX, tags=["Segments"])
app.include_router(campaigns.router, prefix=settings.API_PREFIX, tags=["Campaigns"])
app.include_router(content.router, prefix=settings.API_PREFIX, tags=["Content Studio"])
app.include_router(brand_monitor.router, prefix=settings.API_PREFIX, tags=["Brand Monitor"])
app.include_router(attribution.router, prefix=settings.API_PREFIX, tags=["Attribution"])
app.include_router(clv_churn.router, prefix=settings.API_PREFIX, tags=["CLV & Churn"])
app.include_router(agent.router, prefix=settings.API_PREFIX, tags=["AI Agent"])
app.include_router(alerts.router, prefix=settings.API_PREFIX, tags=["Alerts"])
app.include_router(import_data.router, prefix=settings.API_PREFIX, tags=["Import"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "platform.api.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.API_WORKERS,
    )
