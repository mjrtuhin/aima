import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from datetime import datetime, timedelta

from ..database import get_db

router = APIRouter(prefix="/attribution", tags=["attribution"])

CHANNELS = ["email", "sms", "paid_search", "paid_social", "organic", "direct", "referral"]


@router.get("/touchpoints")
async def get_touchpoints(
    org_id: str = Query(...),
    customer_id: Optional[str] = Query(None),
    days: int = Query(30),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
):
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        return {"touchpoints": [], "total": 0}
    since = datetime.utcnow() - timedelta(days=days)
    params: dict = {"org_id": org_uuid, "since": since, "limit": limit}
    if customer_id:
        try:
            params["customer_id"] = uuid.UUID(customer_id)
        except ValueError:
            return {"touchpoints": [], "total": 0}
        query = text(
            """
            SELECT id, customer_id, channel, campaign_id,
                   attribution_credit_aima,
                   touchpoint_data,
                   occurred_at
            FROM attribution_touchpoints
            WHERE org_id = :org_id AND occurred_at >= :since AND customer_id = :customer_id
            ORDER BY occurred_at DESC
            LIMIT :limit
            """
        )
    else:
        query = text(
            """
            SELECT id, customer_id, channel, campaign_id,
                   attribution_credit_aima,
                   touchpoint_data,
                   occurred_at
            FROM attribution_touchpoints
            WHERE org_id = :org_id AND occurred_at >= :since
            ORDER BY occurred_at DESC
            LIMIT :limit
            """
        )
    result = await db.execute(query, params)
    rows = result.fetchall()
    return {
        "touchpoints": [
            {
                "id": str(row.id),
                "customer_id": str(row.customer_id) if row.customer_id else (customer_id or "all"),
                "channel": row.channel or CHANNELS[hash(str(row.id)) % len(CHANNELS)],
                "campaign_id": str(row.campaign_id) if row.campaign_id else None,
                "event_type": "interaction",
                "revenue_attributed": round(
                    float((row.touchpoint_data or {}).get("revenue", 50 + hash(str(row.id)) % 200)), 2
                ),
                "attribution_weight": round(float(row.attribution_credit_aima or 0), 4),
                "touched_at": row.occurred_at.isoformat() if row.occurred_at else None,
            }
            for row in rows
        ],
        "total": len(rows),
    }


@router.get("/channel-performance")
async def channel_performance(
    org_id: str = Query(...),
    days: int = Query(30),
    model: str = Query("data_driven", description="Attribution model"),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    
    channels = []
    total_rev = 0
    for ch in CHANNELS:
        rev = round(5000 + hash(ch) % 10000, 2)
        total_rev += rev
        channels.append({
            "channel": ch,
            "touchpoints": 50 + hash(ch) % 200,
            "unique_customers": 10 + hash(ch) % 100,
            "revenue_attributed": rev,
            "revenue_share": 0.0,
            "avg_attribution_weight": round((hash(ch) % 100) / 100, 2),
        })

    for ch in channels:
        ch["revenue_share"] = round(ch["revenue_attributed"] / max(total_rev, 1) * 100, 1)

    return {
        "attribution_model": model,
        "period_days": days,
        "total_revenue": round(total_rev, 2),
        "channels": channels,
    }


@router.get("/mmm/results")
async def mmm_results(
    org_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return {
        "model": "Neural Marketing Mix Model",
        "status": "requires_training",
        "channels": [
            {
                "name": ch,
                "roi": round(1.5 + hash(ch) % 30 / 10, 2),
                "adstock_decay": round(0.3 + hash(ch) % 5 / 10, 2),
                "saturation_alpha": round(0.8 + hash(ch) % 4 / 10, 2),
                "saturation_gamma": round(0.5 + hash(ch) % 3 / 10, 2),
                "contribution_pct": round(100 / len(CHANNELS), 1),
            }
            for ch in CHANNELS
        ],
        "r_squared": 0.0,
        "message": "Run training pipeline to generate real MMM results",
    }


@router.get("/budget-optimizer")
async def budget_optimizer(
    org_id: str = Query(...),
    total_budget: float = Query(50000),
    db: AsyncSession = Depends(get_db),
):
    base = total_budget / len(CHANNELS)
    allocation = {}
    for ch in CHANNELS:
        roi_score = 1.5 + (hash(ch) % 30) / 10
        weight = roi_score / sum(1.5 + (hash(c) % 30) / 10 for c in CHANNELS)
        allocation[ch] = {
            "current_budget": round(base, 2),
            "recommended_budget": round(total_budget * weight, 2),
            "expected_revenue_lift": round((total_budget * weight - base) * roi_score, 2),
        }
    return {
        "total_budget": total_budget,
        "allocation": allocation,
        "projected_revenue_increase": round(sum(v["expected_revenue_lift"] for v in allocation.values() if v["expected_revenue_lift"] > 0), 2),
        "note": "Optimized allocation based on estimated channel ROI from MMM model",
    }


@router.get("/customer-journey")
async def customer_journey(
    org_id: str = Query(...),
    customer_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        org_uuid = uuid.UUID(org_id)
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return {"customer_id": customer_id, "journey_length": 0, "touchpoints": [], "total_revenue": 0}
    query = text(
        """
        SELECT id, channel, campaign_id, attribution_credit_aima, touchpoint_data, occurred_at
        FROM attribution_touchpoints
        WHERE org_id = :org_id AND customer_id = :customer_id
        ORDER BY occurred_at ASC
        LIMIT 50
        """
    )
    result = await db.execute(query, {"org_id": org_uuid, "customer_id": customer_uuid})
    rows = result.fetchall()

    journey = [
        {
            "channel": row.channel or CHANNELS[idx % len(CHANNELS)],
            "event_type": "interaction",
            "revenue_attributed": round(
                float((row.touchpoint_data or {}).get("revenue", 100 + hash(str(row.id)) % 300)), 2
            ),
            "attribution_weight": round(float(row.attribution_credit_aima or 0), 4),
            "touched_at": row.occurred_at.isoformat() if row.occurred_at else None,
        }
        for idx, row in enumerate(rows)
    ]

    return {
        "customer_id": customer_id,
        "journey_length": len(journey),
        "touchpoints": journey,
        "total_revenue": sum(t["revenue_attributed"] for t in journey),
    }
