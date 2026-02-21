from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db

router = APIRouter(prefix="/content", tags=["content_studio"])

TONES = ["professional", "friendly", "urgent", "casual", "inspirational"]
CHANNELS = ["email", "sms", "push", "social", "ads"]


@router.post("/generate/email")
async def generate_email(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    segment_type = payload.get("segment_type", "general")
    tone = payload.get("tone", "professional")
    goal = payload.get("goal", "engagement")
    product = payload.get("product_name", "our products")
    brand_name = payload.get("brand_name", "Brand")

    templates = {
        "Champions": {
            "subject": f"Thank you for being our top customer",
            "preview": "A special reward just for you",
            "body": f"You've been incredible this year. As a thank-you, here's an exclusive early access offer on {product}.",
            "cta": "Claim Your Exclusive Offer",
        },
        "At-Risk": {
            "subject": f"We miss you",
            "preview": "Come back and see what's new",
            "body": f"It's been a while. We've added new things to {product} and have a special offer waiting for you.",
            "cta": "See What's New",
        },
        "New Customers": {
            "subject": f"Welcome to {brand_name}",
            "preview": "Everything you need to know",
            "body": f"Welcome! Here are three ways to get the most out of {product} right away.",
            "cta": "Get Started",
        },
    }

    template = templates.get(segment_type, {
        "subject": f"An update from {brand_name}",
        "preview": "See what's new",
        "body": f"We have exciting news about {product}.",
        "cta": "Learn More",
    })

    subject_variants = [
        template["subject"],
        template["subject"].replace("Thank you", "You're amazing"),
        f"[{goal.title()}] " + template["subject"],
    ]

    return {
        "subject_lines": subject_variants,
        "preview_text": template["preview"],
        "body": template["body"],
        "cta_text": template["cta"],
        "tone": tone,
        "segment_type": segment_type,
        "html": _generate_html(template, brand_name),
        "word_count": len(template["body"].split()),
    }


def _generate_html(template: dict, brand_name: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{template['subject']}</title></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: #1a56db; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 24px;">{brand_name}</h1>
  </div>
  <div style="background: white; padding: 30px; border: 1px solid #e5e7eb;">
    <p style="color: #374151; line-height: 1.6;">{template['body']}</p>
    <a href="#" style="display: inline-block; background: #1a56db; color: white; padding: 12px 24px;
       border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 16px;">
      {template['cta_text']}
    </a>
  </div>
  <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
    Copyright {brand_name}. Unsubscribe | Privacy Policy
  </div>
</body>
</html>"""


@router.post("/generate/sms")
async def generate_sms(payload: dict):
    segment_type = payload.get("segment_type", "general")
    goal = payload.get("goal", "engagement")
    product = payload.get("product_name", "our product")
    max_chars = 160

    messages = {
        "Champions": f"VIP offer: Early access to new {product} features. Reply STOP to unsubscribe.",
        "At-Risk": f"We miss you! 20% off your next order. Use code COMEBACK. Reply STOP to opt out.",
        "New Customers": f"Welcome! Your account is ready. Start exploring {product} today. Reply STOP to opt out.",
    }
    text = messages.get(segment_type, f"Check out the latest from {product}. Reply STOP to opt out.")

    return {
        "message": text[:max_chars],
        "character_count": len(text),
        "within_single_sms": len(text) <= 160,
        "segment_type": segment_type,
    }


@router.get("/templates")
async def list_templates(
    category: Optional[str] = Query(None),
    channel: Optional[str] = Query("email"),
):
    templates = [
        {"id": "welcome_series", "name": "Welcome Series", "channel": "email", "category": "onboarding", "segments": ["New Customers"]},
        {"id": "winback_30", "name": "30-Day Win-Back", "channel": "email", "category": "retention", "segments": ["At-Risk"]},
        {"id": "champion_loyalty", "name": "Champion Loyalty Reward", "channel": "email", "category": "loyalty", "segments": ["Champions"]},
        {"id": "flash_sale", "name": "Flash Sale Announcement", "channel": "sms", "category": "promotional", "segments": ["all"]},
        {"id": "cart_abandon", "name": "Cart Abandonment Recovery", "channel": "email", "category": "conversion", "segments": ["all"]},
    ]
    if category:
        templates = [t for t in templates if t["category"] == category]
    if channel:
        templates = [t for t in templates if t["channel"] == channel]
    return {"templates": templates, "total": len(templates)}


@router.get("/performance")
async def content_performance(
    org_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    return {
        "org_id": org_id,
        "top_subject_lines": [
            {"subject": "You're our VIP - exclusive offer inside", "open_rate": 0.42},
            {"subject": "Last chance: 24 hours left", "open_rate": 0.38},
            {"subject": "We miss you - here's 20% off", "open_rate": 0.35},
        ],
        "best_send_times": {
            "email": {"day": "Tuesday", "hour": 10},
            "sms": {"day": "Thursday", "hour": 14},
        },
        "tone_performance": {
            "urgent": {"avg_open_rate": 0.38, "avg_ctr": 0.08},
            "friendly": {"avg_open_rate": 0.32, "avg_ctr": 0.06},
            "professional": {"avg_open_rate": 0.28, "avg_ctr": 0.05},
        },
    }
