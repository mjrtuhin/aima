"""
Planner Agent - Module 7: Autonomous AI Marketing Agent.
Receives high-level marketing goals from the marketer and breaks them
into structured marketing plans with specific campaigns, segments, channels,
content requirements, timing, and success metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
import structlog

log = structlog.get_logger()


@dataclass
class CampaignPlan:
    campaign_name: str
    objective: str
    target_segment: str
    channel: str
    content_brief: str
    offer_type: Optional[str]
    offer_value: Optional[float]
    budget: float
    scheduled_date: datetime
    success_metrics: dict[str, float]
    reasoning: str


@dataclass
class MarketingPlan:
    goal: str
    total_budget: float
    timeframe_days: int
    campaigns: list[CampaignPlan] = field(default_factory=list)
    expected_revenue: float = 0.0
    expected_roi: float = 0.0
    key_assumptions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PlannerAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.log = log.bind(component="PlannerAgent")

    def create_plan(
        self,
        goal: str,
        budget: float,
        timeframe_days: int,
        segment_summary: dict,
        historical_performance: Optional[dict] = None,
    ) -> MarketingPlan:
        self.log.info("Creating marketing plan", goal=goal, budget=budget, days=timeframe_days)

        if self.llm_client:
            return self._llm_plan(goal, budget, timeframe_days, segment_summary, historical_performance)

        return self._rule_based_plan(goal, budget, timeframe_days, segment_summary)

    def _rule_based_plan(
        self,
        goal: str,
        budget: float,
        timeframe_days: int,
        segment_summary: dict,
    ) -> MarketingPlan:
        plan = MarketingPlan(
            goal=goal,
            total_budget=budget,
            timeframe_days=timeframe_days,
        )

        at_risk_size = segment_summary.get("at_risk_count", 0)
        champion_size = segment_summary.get("champion_count", 0)
        new_customer_size = segment_summary.get("new_count", 0)

        now = datetime.now(timezone.utc)

        if at_risk_size > 0:
            plan.campaigns.append(CampaignPlan(
                campaign_name="At-Risk Win-Back Campaign",
                objective="Re-engage customers at risk of churning",
                target_segment="At Risk",
                channel="email",
                content_brief="Warm re-engagement email highlighting what they've been missing. Personal tone. Acknowledge the gap.",
                offer_type="percentage_discount",
                offer_value=15.0,
                budget=budget * 0.35,
                scheduled_date=now + timedelta(days=1),
                success_metrics={"open_rate": 0.22, "conversion_rate": 0.035, "revenue": budget * 0.35 * 3.5},
                reasoning="At-Risk customers have highest intervention ROI if engaged before full churn.",
            ))

        if new_customer_size > 0:
            plan.campaigns.append(CampaignPlan(
                campaign_name="New Customer Nurture Sequence",
                objective="Convert first-time buyers into loyal customers",
                target_segment="New Customers",
                channel="email",
                content_brief="Welcome sequence - 3 emails over 14 days. Introduce brand story, best sellers, community.",
                offer_type="free_shipping",
                offer_value=None,
                budget=budget * 0.25,
                scheduled_date=now + timedelta(days=3),
                success_metrics={"open_rate": 0.35, "second_purchase_rate": 0.18},
                reasoning="New customers who receive nurture sequence are 3x more likely to make a second purchase.",
            ))

        if champion_size > 0:
            plan.campaigns.append(CampaignPlan(
                campaign_name="Champion Loyalty Reward",
                objective="Retain and deepen relationship with top customers",
                target_segment="Champions",
                channel="email",
                content_brief="Exclusive early access to new products + VIP thank you message. No discount needed.",
                offer_type=None,
                offer_value=None,
                budget=budget * 0.15,
                scheduled_date=now + timedelta(days=7),
                success_metrics={"open_rate": 0.45, "click_rate": 0.12, "repeat_purchase": 0.65},
                reasoning="Champions respond to exclusivity and recognition more than discounts.",
            ))

        plan.expected_revenue = sum(
            c.success_metrics.get("revenue", c.budget * 3.0)
            for c in plan.campaigns
        )
        plan.expected_roi = round(plan.expected_revenue / max(budget, 1), 2)
        plan.key_assumptions = [
            "Email deliverability maintained above 95%",
            "Segment data is current (refreshed within last 24h)",
            "Historical open rates will hold within 20% variance",
        ]

        self.log.info("Plan created", n_campaigns=len(plan.campaigns), expected_roi=plan.expected_roi)
        return plan

    def _llm_plan(
        self,
        goal: str,
        budget: float,
        timeframe_days: int,
        segment_summary: dict,
        historical: Optional[dict],
    ) -> MarketingPlan:
        prompt = f"""You are an expert marketing strategist. Create a detailed marketing plan.

Goal: {goal}
Budget: £{budget:,.0f}
Timeframe: {timeframe_days} days
Customer segments: {segment_summary}
Historical performance: {historical or 'Not available'}

Create a plan with 3-5 specific campaigns. For each:
- Campaign name
- Target segment
- Channel (email/sms/meta_ads/google_ads)
- Content brief (2-3 sentences)
- Offer type and value
- Budget allocation
- Expected open rate, click rate, conversion rate, revenue

Explain your reasoning for each decision."""

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
            )
            raw = response.choices[0].message.content
            self.log.info("LLM plan generated", length=len(raw))
            return self._rule_based_plan(goal, budget, timeframe_days, segment_summary)
        except Exception as e:
            self.log.error("LLM planning failed", error=str(e))
            return self._rule_based_plan(goal, budget, timeframe_days, segment_summary)
