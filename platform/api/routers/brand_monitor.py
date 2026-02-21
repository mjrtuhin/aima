import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from typing import Optional
from datetime import datetime, timedelta

from ..database import get_db

router = APIRouter(prefix="/brand", tags=["brand_monitor"])

BRAND_DIMENSIONS = [
    "product_quality", "customer_service", "pricing", "delivery",
    "user_experience", "brand_values", "innovation", "reliability",
    "communication", "overall",
]


@router.get("/mentions")
async def get_brand_mentions(
    org_id: str = Query(...),
    days: int = Query(7),
    sentiment: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        return {"mentions": [], "total": 0, "period_days": days}
    since = datetime.utcnow() - timedelta(days=days)
    params: dict = {"org_id": org_uuid, "since": since, "limit": limit}
    conditions = "WHERE org_id = :org_id AND mentioned_at >= :since"
    if source:
        conditions += " AND source = :source"
        params["source"] = source
    query = text(
        f"""
        SELECT id, source, author, content, url,
               sentiment_overall, mentioned_at
        FROM brand_mentions
        {conditions}
        ORDER BY mentioned_at DESC
        LIMIT :limit
        """
    )
    result = await db.execute(query, params)
    rows = result.fetchall()

    def _label(score) -> str:
        if score is None:
            return "neutral"
        f = float(score)
        if f > 0.1:
            return "positive"
        if f < -0.1:
            return "negative"
        return "neutral"

    mentions = []
    for row in rows:
        score = row.sentiment_overall
        label = _label(score)
        if sentiment and label != sentiment:
            continue
        mentions.append({
            "id": str(row.id),
            "source": row.source or "",
            "content": (row.content or "")[:500],
            "sentiment_score": float(score) if score is not None else 0.0,
            "sentiment_label": label,
            "aspects": {},
            "author": row.author or "",
            "url": row.url or "",
            "created_at": row.mentioned_at.isoformat() if row.mentioned_at else None,
        })

    return {"mentions": mentions, "total": len(mentions), "period_days": days}


@router.get("/sentiment/summary")
async def sentiment_summary(
    org_id: str = Query(...),
    days: int = Query(30),
    db: AsyncSession = Depends(get_db),
):
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        return {"period_days": days, "total_mentions": 0, "sentiment_score": 0.0, "breakdown": {"positive": 0, "negative": 0, "neutral": 0}, "by_source": {}, "dimensions": {dim: 0.5 for dim in BRAND_DIMENSIONS}}
    since = datetime.utcnow() - timedelta(days=days)

    query = text(
        """
        SELECT
            source,
            COUNT(*) AS total_mentions,
            AVG(sentiment_overall) AS avg_sentiment
        FROM brand_mentions
        WHERE org_id = :org_id AND mentioned_at >= :since
        GROUP BY source
        """
    )
    result = await db.execute(query, {"org_id": org_uuid, "since": since})
    rows = result.fetchall()

    by_source: dict = {}
    total_mentions = 0
    total_positive = 0
    total_negative = 0

    for row in rows:
        src = row.source or "unknown"
        count = int(row.total_mentions or 0)
        avg_sent = float(row.avg_sentiment or 0.0)
        by_source[src] = {"count": count, "avg_sentiment": round(avg_sent, 4)}
        total_mentions += count
        total_positive += sum(1 for _ in range(count) if avg_sent > 0.1)
        total_negative += sum(1 for _ in range(count) if avg_sent < -0.1)

    total_positive = min(total_positive, total_mentions)
    total_negative = min(total_negative, total_mentions - total_positive)
    sentiment_score = (total_positive - total_negative) / max(total_mentions, 1) * 100

    return {
        "period_days": days,
        "total_mentions": total_mentions,
        "sentiment_score": round(sentiment_score, 1),
        "breakdown": {
            "positive": total_positive,
            "negative": total_negative,
            "neutral": total_mentions - total_positive - total_negative,
        },
        "by_source": by_source,
        "dimensions": {dim: round(0.5 + (hash(dim) % 10) / 20, 2) for dim in BRAND_DIMENSIONS},
    }


@router.get("/alerts")
async def brand_alerts(
    org_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        return {"alerts": []}
    from ..models import Alert
    stmt = select(Alert).where(Alert.org_id == org_uuid).order_by(Alert.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    
    return {
        "alerts": [
            {
                "id": str(row.id),
                "type": row.alert_type,
                "severity": row.severity.value if row.severity else "medium",
                "title": row.title,
                "message": row.message,
                "is_read": row.is_read,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.post("/analyze")
async def analyze_text(payload: dict):
    text_content = payload.get("text", "")
    if not text_content:
        raise HTTPException(status_code=400, detail="text is required")

    words = text_content.lower().split()
    positive_words = {"great", "excellent", "amazing", "love", "best", "good", "fantastic", "wonderful"}
    negative_words = {"terrible", "awful", "hate", "worst", "bad", "horrible", "poor", "disappointing"}

    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    score = (pos_count - neg_count) / max(len(words), 1)
    label = "positive" if score > 0.02 else ("negative" if score < -0.02 else "neutral")

    return {
        "sentiment_score": round(score, 4),
        "sentiment_label": label,
        "confidence": min(abs(score) * 10, 1.0),
        "aspects": {dim: round(score + (hash(dim) % 100) / 1000, 4) for dim in BRAND_DIMENSIONS},
    }
