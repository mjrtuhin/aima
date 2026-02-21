from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
import uuid
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("")
async def list_campaigns(
    org_id: str = Query(...),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Campaign).where(Campaign.org_id == org_id)
    if status:
        stmt = stmt.where(Campaign.status == status)
    stmt = stmt.order_by(Campaign.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    count_stmt = select(func.count()).select_from(Campaign).where(Campaign.org_id == org_id)
    total = (await db.execute(count_stmt)).scalar()

    return {
        "campaigns": [
            {
                "id": str(c.id),
                "name": c.name,
                "channel": c.channel.value if c.channel else None,
                "status": c.status.value if c.status else None,
                "segment_id": str(c.target_segment_id) if c.target_segment_id else None,
                "scheduled_at": c.scheduled_at.isoformat() if c.scheduled_at else None,
                "launched_at": c.launched_at.isoformat() if c.launched_at else None,
                "predicted_open_rate": float(c.predicted_open_rate) if c.predicted_open_rate else None,
                "predicted_click_rate": float(c.predicted_click_rate) if c.predicted_click_rate else None,
                "predicted_conversion_rate": float(c.predicted_conversion_rate) if c.predicted_conversion_rate else None,
                "predicted_revenue": float(c.predicted_revenue) if c.predicted_revenue else None,
                "actual_open_rate": float(c.actual_open_rate) if c.actual_open_rate else None,
                "actual_click_rate": float(c.actual_click_rate) if c.actual_click_rate else None,
                "actual_conversion_rate": float(c.actual_conversion_rate) if c.actual_conversion_rate else None,
                "actual_revenue": float(c.actual_revenue) if c.actual_revenue else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in campaigns
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/analytics/summary")
async def campaign_analytics(
    org_id: str = Query(...),
    days: int = Query(30),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    stmt = select(Campaign).where(
        and_(Campaign.org_id == org_id, Campaign.created_at >= since)
    )
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    total = len(campaigns)
    sent = [c for c in campaigns if c.status and c.status.value == "completed"]
    avg_open = sum(float(c.actual_open_rate) if c.actual_open_rate else 0 for c in sent) / max(len(sent), 1)
    avg_click = sum(float(c.actual_click_rate) if c.actual_click_rate else 0 for c in sent) / max(len(sent), 1)
    total_revenue = sum(float(c.actual_revenue) if c.actual_revenue else 0 for c in sent)

    return {
        "period_days": days,
        "total_campaigns": total,
        "sent_campaigns": len(sent),
        "avg_open_rate": round(avg_open, 4),
        "avg_click_rate": round(avg_click, 4),
        "total_revenue": round(total_revenue, 2),
        "by_channel": {},
    }


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    org_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Campaign).where(
        and_(Campaign.id == uuid.UUID(campaign_id), Campaign.org_id == org_id)
    )
    result = await db.execute(stmt)
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    performance = {}
    if campaign.actual_open_rate and campaign.predicted_open_rate:
        performance["open_rate_delta"] = float(campaign.actual_open_rate) - float(campaign.predicted_open_rate)
    if campaign.actual_revenue and campaign.predicted_revenue:
        actual_rev = float(campaign.actual_revenue)
        predicted_rev = float(campaign.predicted_revenue)
        performance["revenue_delta"] = actual_rev - predicted_rev
        if predicted_rev > 0:
            performance["revenue_accuracy"] = 1 - abs(performance["revenue_delta"]) / predicted_rev

    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "channel": campaign.channel.value if campaign.channel else None,
        "status": campaign.status.value if campaign.status else None,
        "segment_id": str(campaign.target_segment_id) if campaign.target_segment_id else None,
        "subject_line": campaign.subject_line,
        "content": campaign.content,
        "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
        "predictions": {
            "open_rate": float(campaign.predicted_open_rate) if campaign.predicted_open_rate else None,
            "click_rate": float(campaign.predicted_click_rate) if campaign.predicted_click_rate else None,
            "conversion_rate": float(campaign.predicted_conversion_rate) if campaign.predicted_conversion_rate else None,
            "revenue": float(campaign.predicted_revenue) if campaign.predicted_revenue else None,
        },
        "actuals": {
            "open_rate": float(campaign.actual_open_rate) if campaign.actual_open_rate else None,
            "click_rate": float(campaign.actual_click_rate) if campaign.actual_click_rate else None,
            "conversion_rate": float(campaign.actual_conversion_rate) if campaign.actual_conversion_rate else None,
            "revenue": float(campaign.actual_revenue) if campaign.actual_revenue else None,
        },
        "performance": performance,
        "created_at": campaign.created_at.isoformat(),
    }


@router.post("")
async def create_campaign(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    org_id = payload.get("org_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="org_id is required")

    campaign = Campaign(
        org_id=org_id,
        name=payload.get("name", "Untitled Campaign"),
        channel=payload.get("channel", "email"),
        status="draft",
        subject_line=payload.get("subject_line"),
        content=payload.get("content", {}),
        target_segment_id=uuid.UUID(payload["target_segment_id"]) if payload.get("target_segment_id") else None,
        scheduled_at=datetime.fromisoformat(payload["scheduled_at"]) if payload.get("scheduled_at") else None,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return {"id": str(campaign.id), "status": "created"}
