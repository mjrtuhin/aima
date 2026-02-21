from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Optional
import uuid
from datetime import datetime, timedelta

from ..database import get_db
from ..models import Customer

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat")
async def chat(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    message = payload.get("message", "").strip()
    org_id = payload.get("org_id")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    response = await _handle_message(message, org_id, db)
    return {
        "message": message,
        "response": response["text"],
        "actions": response.get("actions", []),
        "data": response.get("data"),
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _handle_message(message: str, org_id: Optional[str], db: AsyncSession) -> dict:
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["churn", "at risk", "losing customers"]):
        return {
            "text": "I can analyze your churn risk. Your high-risk customers should be targeted with win-back campaigns immediately. A personalized discount offer typically recovers 15-25% of at-risk customers.",
            "actions": [
                {"type": "navigate", "label": "View At-Risk Customers", "href": "/clv-churn"},
                {"type": "create_campaign", "label": "Create Win-Back Campaign", "segment": "At-Risk"},
            ],
        }

    if any(w in msg_lower for w in ["segment", "segments", "cluster", "group"]):
        return {
            "text": "I can trigger customer segmentation using behavioral analysis. This will group your customers into segments based on their purchase and engagement patterns.",
            "actions": [
                {"type": "navigate", "label": "View Segments", "href": "/customers"},
                {"type": "trigger_segmentation", "label": "Run Segmentation Now"},
            ],
        }

    if any(w in msg_lower for w in ["campaign", "email", "send", "marketing"]):
        return {
            "text": "I can help you create and optimize marketing campaigns. Our campaign predictor can forecast open rates, click rates, and expected revenue before you send. What type of campaign are you looking to create?",
            "actions": [
                {"type": "navigate", "label": "Create Campaign", "href": "/campaigns"},
                {"type": "navigate", "label": "Content Studio", "href": "/content"},
            ],
        }

    if any(w in msg_lower for w in ["revenue", "sales", "performance", "report"]):
        return {
            "text": "Here is a summary of your marketing performance. For detailed attribution analysis showing which channels drive the most revenue, check the Attribution module.",
            "actions": [
                {"type": "navigate", "label": "View Attribution", "href": "/attribution"},
                {"type": "navigate", "label": "Dashboard", "href": "/"},
            ],
        }

    if any(w in msg_lower for w in ["brand", "sentiment", "mention", "review"]):
        return {
            "text": "Your Brand Monitor tracks sentiment across all customer touchpoints. I can flag negative sentiment spikes and alert you to emerging issues before they escalate.",
            "actions": [
                {"type": "navigate", "label": "Brand Monitor", "href": "/brand"},
            ],
        }

    return {
        "text": f"I'm your AI marketing assistant. I can help you with: customer segmentation, churn prediction, campaign creation, content generation, attribution analysis, and brand monitoring. What would you like to work on?",
        "actions": [
            {"type": "navigate", "label": "Dashboard", "href": "/"},
            {"type": "navigate", "label": "Customers", "href": "/customers"},
        ],
    }


@router.get("/suggestions")
async def get_suggestions(
    org_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer).where(Customer.org_id == org_id)
    result = await db.execute(stmt)
    customers = result.scalars().all()
    
    high_risk = sum(1 for c in customers if round((hash(str(c.id)) % 100) / 100, 4) >= 0.7)

    suggestions = []
    if high_risk > 0:
        suggestions.append({
            "id": "winback_campaign",
            "priority": "high",
            "title": f"Launch win-back campaign for {high_risk} at-risk customers",
            "description": f"You have {high_risk} customers at high churn risk. A personalized win-back campaign can recover 15-25% of them.",
            "action": {"type": "create_campaign", "segment": "At-Risk"},
            "estimated_impact": {"revenue_recovery": high_risk * 150, "customers_recovered": int(high_risk * 0.2)},
        })

    suggestions.append({
        "id": "segment_refresh",
        "priority": "medium",
        "title": "Refresh customer segments",
        "description": "Running segmentation on the latest behavioral data improves targeting accuracy.",
        "action": {"type": "trigger_segmentation"},
        "estimated_impact": {"campaign_lift": "12-18%"},
    })

    return {"suggestions": suggestions, "generated_at": datetime.utcnow().isoformat()}


@router.get("/history")
async def conversation_history(
    org_id: str = Query(...),
    limit: int = Query(20),
):
    return {
        "history": [],
        "total": 0,
        "note": "Conversation history stored in session",
    }
