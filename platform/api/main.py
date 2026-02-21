import uuid
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


_EXTRA_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    customer_id UUID,
    external_id VARCHAR(255),
    order_number VARCHAR(100),
    status VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'USD',
    subtotal NUMERIC(12, 2),
    total NUMERIC(12, 2),
    items JSONB DEFAULT '[]',
    channel VARCHAR(100),
    properties JSONB DEFAULT '{}',
    ordered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS brand_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    source VARCHAR(100) NOT NULL DEFAULT 'unknown',
    source_id VARCHAR(500),
    author VARCHAR(255),
    content TEXT,
    url VARCHAR(2000),
    sentiment_overall NUMERIC(5, 4),
    sentiment_product_quality NUMERIC(5, 4),
    sentiment_customer_service NUMERIC(5, 4),
    sentiment_pricing NUMERIC(5, 4),
    sentiment_brand_trust NUMERIC(5, 4),
    sentiment_innovation NUMERIC(5, 4),
    is_competitor BOOLEAN DEFAULT false,
    mentioned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS attribution_touchpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    customer_id UUID,
    order_id UUID,
    channel VARCHAR(100),
    campaign_id UUID,
    touchpoint_data JSONB DEFAULT '{}',
    attribution_credit_last_click NUMERIC(5, 4),
    attribution_credit_first_click NUMERIC(5, 4),
    attribution_credit_linear NUMERIC(5, 4),
    attribution_credit_aima NUMERIC(5, 4),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_events (
    id UUID DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL,
    customer_id UUID,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    source VARCHAR(100),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from sqlalchemy import text

    log.info("AIMA API starting", env=settings.AIMA_ENV)
    _engine = get_engine()
    try:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            log.info("ORM tables created/verified")
    except Exception as e:
        log.warning("ORM create_all failed (non-fatal)", error=str(e))

    try:
        async with _engine.begin() as conn:
            for stmt in _EXTRA_TABLES_SQL.split(";"):
                stmt = stmt.strip()
                if stmt:
                    await conn.execute(text(stmt))
            log.info("Extra tables created/verified")
    except Exception as e:
        log.warning("Extra tables creation failed (non-fatal)", error=str(e))

    try:
        async with _engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO organizations (id, name, slug) "
                    "VALUES (:id, :name, :slug) ON CONFLICT DO NOTHING"
                ),
                {"id": uuid.UUID(DEMO_ORG_ID), "name": "Demo Organization", "slug": "demo"},
            )
        log.info("Demo org seeded")
    except Exception as e:
        log.warning("Demo org seeding failed (non-fatal)", error=str(e))

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

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        log.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
        if settings.is_development:
            detail = f"{type(exc).__name__}: {exc}"
        else:
            detail = "Internal server error. Please try again later."
        return JSONResponse(
            status_code=500,
            content={"detail": detail},
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "platform.api.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.API_WORKERS,
    )
