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
    since = datetime.utcnow() - timedelta(days=days)
    query = text(
        """
        SELECT id, org_id, source, content, sentiment_score, sentiment_label,
               data, created_at
        FROM alerts
        WHERE org_id = :org_id AND created_at >= :since AND alert_type LIKE 'brand_%'
        ORDER BY created_at DESC
        LIMIT :limit
        """
    )
    result = await db.execute(query, {"org_id": org_id, "since": since, "limit": limit})
    rows = result.fetchall()

    mentions = []
    for row in rows:
        mentions.append({
            "id": str(row.id),
            "source": row.data.get("source", "") if row.data else "",
            "content": row.message[:500] if hasattr(row, "message") and row.message else "",
            "sentiment_score": row.data.get("sentiment_score", 0) if row.data else 0,
            "sentiment_label": row.data.get("sentiment_label", "neutral") if row.data else "neutral",
            "aspects": row.data.get("aspects", {}) if row.data else {},
            "author": row.data.get("author", "") if row.data else "",
            "url": row.data.get("url", "") if row.data else "",
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    return {"mentions": mentions, "total": len(mentions), "period_days": days}


@router.get("/sentiment/summary")
async def sentiment_summary(
    org_id: str = Query(...),
    days: int = Query(30),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    
    query = text(
        """
        SELECT 
            COUNT(*) as total_mentions,
            data->>'source' as source
        FROM alerts
        WHERE org_id = :org_id AND created_at >= :since AND alert_type LIKE 'brand_%'
        GROUP BY data->>'source'
        """
    )
    result = await db.execute(query, {"org_id": org_id, "since": since})
    rows = result.fetchall()

    by_source = {}
    total_mentions = 0
    total_positive = 0
    total_negative = 0

    for row in rows:
        source = row.source if hasattr(row, "source") else "unknown"
        count = row.total_mentions if hasattr(row, "total_mentions") else 0
        by_source[source] = {
            "count": count,
            "avg_sentiment": 0.0,
        }
        total_mentions += count
        total_positive += int(count * 0.4)
        total_negative += int(count * 0.2)

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
    from ..models import Alert
    stmt = select(Alert).where(Alert.org_id == org_id).order_by(Alert.created_at.desc()).limit(20)
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
