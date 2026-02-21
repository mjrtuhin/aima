"""
Feature Engineering Pipeline for Module 1 - Customer Intelligence Engine.
Computes all 45+ behavioral, transactional, engagement, temporal, and composite
features per customer from raw event and order data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
import numpy as np
import pandas as pd
import structlog

log = structlog.get_logger()


@dataclass
class CustomerFeatureVector:
    customer_id: str
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    recency_days: Optional[int] = None
    frequency: int = 0
    monetary_value: float = 0.0
    avg_order_value: float = 0.0
    max_order_value: float = 0.0
    min_order_value: float = 0.0
    order_value_std: float = 0.0
    total_items_purchased: int = 0
    avg_items_per_order: float = 0.0
    unique_products_count: int = 0
    unique_categories_count: int = 0
    purchase_tenure_days: Optional[int] = None
    avg_days_between_purchases: Optional[float] = None
    purchase_acceleration: float = 0.0

    top_category: Optional[str] = None
    category_diversity_score: float = 0.0
    brand_loyalty_score: float = 0.0
    price_sensitivity_score: float = 0.0
    new_product_adoption_rate: float = 0.0

    email_open_rate: float = 0.0
    email_click_rate: float = 0.0
    email_conversion_rate: float = 0.0
    avg_time_to_open_hours: Optional[float] = None
    cart_abandonment_rate: float = 0.0
    website_visit_frequency: float = 0.0
    avg_session_duration_seconds: int = 0
    bounce_rate: float = 0.0

    preferred_day_of_week: Optional[int] = None
    preferred_hour_of_day: Optional[int] = None
    q1_purchase_share: float = 0.0
    q2_purchase_share: float = 0.0
    q3_purchase_share: float = 0.0
    q4_purchase_share: float = 0.0
    recency_trend_90d: float = 0.0

    customer_health_score: float = 0.0
    churn_probability_30d: float = 0.0
    predicted_ltv: float = 0.0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    def to_numeric_array(self) -> np.ndarray:
        numeric_fields = [
            "recency_days", "frequency", "monetary_value", "avg_order_value",
            "max_order_value", "min_order_value", "order_value_std",
            "total_items_purchased", "avg_items_per_order",
            "unique_products_count", "unique_categories_count",
            "purchase_tenure_days", "avg_days_between_purchases",
            "purchase_acceleration", "category_diversity_score",
            "brand_loyalty_score", "price_sensitivity_score",
            "new_product_adoption_rate", "email_open_rate", "email_click_rate",
            "email_conversion_rate", "cart_abandonment_rate",
            "website_visit_frequency", "avg_session_duration_seconds",
            "bounce_rate", "preferred_day_of_week", "preferred_hour_of_day",
            "q1_purchase_share", "q2_purchase_share", "q3_purchase_share",
            "q4_purchase_share", "recency_trend_90d", "customer_health_score",
        ]
        values = []
        for f in numeric_fields:
            v = getattr(self, f, None)
            values.append(float(v) if v is not None else 0.0)
        return np.array(values, dtype=np.float32)


class FeatureEngineer:
    def __init__(self, org_id: str, reference_date: Optional[datetime] = None):
        self.org_id = org_id
        self.reference_date = reference_date or datetime.now(timezone.utc)
        self.log = log.bind(org_id=org_id)

    def compute_from_dataframes(
        self,
        orders_df: pd.DataFrame,
        events_df: Optional[pd.DataFrame] = None,
        customer_id: Optional[str] = None,
    ) -> list[CustomerFeatureVector]:
        if customer_id:
            orders_df = orders_df[orders_df["customer_id"] == customer_id]
            if events_df is not None:
                events_df = events_df[events_df["customer_id"] == customer_id]

        customer_ids = orders_df["customer_id"].unique()
        features = []

        for cid in customer_ids:
            cust_orders = orders_df[orders_df["customer_id"] == cid]
            cust_events = events_df[events_df["customer_id"] == cid] if events_df is not None else None
            fv = self._compute_single(str(cid), cust_orders, cust_events)
            features.append(fv)

        self.log.info("Features computed", customers=len(features))
        return features

    def _compute_single(
        self,
        customer_id: str,
        orders: pd.DataFrame,
        events: Optional[pd.DataFrame],
    ) -> CustomerFeatureVector:
        fv = CustomerFeatureVector(customer_id=customer_id)

        if orders.empty:
            return fv

        orders = orders.copy()
        orders["ordered_at"] = pd.to_datetime(orders["ordered_at"], utc=True)
        orders = orders.sort_values("ordered_at")

        self._compute_rfm(fv, orders)
        self._compute_order_stats(fv, orders)
        self._compute_product_features(fv, orders)
        self._compute_temporal_features(fv, orders)
        if events is not None and not events.empty:
            self._compute_engagement_features(fv, events)
        self._compute_health_score(fv)

        return fv

    def _compute_rfm(self, fv: CustomerFeatureVector, orders: pd.DataFrame) -> None:
        last_order_date = orders["ordered_at"].max()
        fv.recency_days = (self.reference_date - last_order_date).days
        fv.frequency = len(orders)
        fv.monetary_value = float(orders["total"].sum())

        first_order_date = orders["ordered_at"].min()
        fv.purchase_tenure_days = (last_order_date - first_order_date).days

        if len(orders) > 1:
            order_dates = orders["ordered_at"].sort_values()
            gaps = order_dates.diff().dropna().dt.days
            fv.avg_days_between_purchases = float(gaps.mean())

            if len(gaps) >= 4:
                first_half_avg = float(gaps.iloc[: len(gaps) // 2].mean())
                second_half_avg = float(gaps.iloc[len(gaps) // 2 :].mean())
                if first_half_avg > 0:
                    fv.purchase_acceleration = (first_half_avg - second_half_avg) / first_half_avg

    def _compute_order_stats(self, fv: CustomerFeatureVector, orders: pd.DataFrame) -> None:
        totals = orders["total"].astype(float)
        fv.avg_order_value = float(totals.mean())
        fv.max_order_value = float(totals.max())
        fv.min_order_value = float(totals.min())
        fv.order_value_std = float(totals.std()) if len(totals) > 1 else 0.0

        if "items" in orders.columns:
            item_counts = orders["items"].apply(
                lambda x: sum(i.get("quantity", 1) for i in (x or []))
            )
            fv.total_items_purchased = int(item_counts.sum())
            fv.avg_items_per_order = float(item_counts.mean())

            all_products = []
            all_categories = []
            discounted_count = 0

            for _, row in orders.iterrows():
                for item in (row.get("items") or []):
                    pid = item.get("product_id")
                    if pid:
                        all_products.append(str(pid))
                    cat = item.get("category") or item.get("product_type")
                    if cat:
                        all_categories.append(cat)
                    if item.get("discount", 0) > 0:
                        discounted_count += 1

            fv.unique_products_count = len(set(all_products))
            fv.unique_categories_count = len(set(all_categories))

            total_item_count = max(fv.total_items_purchased, 1)
            fv.price_sensitivity_score = round(discounted_count / total_item_count, 4)

            if all_categories:
                from collections import Counter
                cat_counts = Counter(all_categories)
                fv.top_category = cat_counts.most_common(1)[0][0]
                n_cats = len(cat_counts)
                total_cats = len(all_categories)
                fv.category_diversity_score = round(n_cats / max(total_cats, 1), 4)

    def _compute_temporal_features(self, fv: CustomerFeatureVector, orders: pd.DataFrame) -> None:
        fv.preferred_day_of_week = int(orders["ordered_at"].dt.dayofweek.mode()[0])
        fv.preferred_hour_of_day = int(orders["ordered_at"].dt.hour.mode()[0])

        quarters = orders["ordered_at"].dt.quarter
        total = len(orders)
        fv.q1_purchase_share = float((quarters == 1).sum() / total)
        fv.q2_purchase_share = float((quarters == 2).sum() / total)
        fv.q3_purchase_share = float((quarters == 3).sum() / total)
        fv.q4_purchase_share = float((quarters == 4).sum() / total)

        cutoff_90d = self.reference_date - timedelta(days=90)
        recent_orders = orders[orders["ordered_at"] >= cutoff_90d]
        if len(recent_orders) > 0:
            fv.recency_trend_90d = len(recent_orders) / max(fv.frequency, 1)

    def _compute_engagement_features(self, fv: CustomerFeatureVector, events: pd.DataFrame) -> None:
        email_sends = events[events["event_type"] == "email_sent"]
        email_opens = events[events["event_type"] == "email_opened"]
        email_clicks = events[events["event_type"] == "email_clicked"]
        email_conversions = events[events["event_type"] == "email_converted"]
        cart_adds = events[events["event_type"] == "cart_added"]
        cart_abandons = events[events["event_type"] == "cart_abandoned"]
        page_views = events[events["event_type"] == "page_viewed"]
        sessions = events[events["event_type"] == "session_started"]

        n_sends = len(email_sends)
        if n_sends > 0:
            fv.email_open_rate = round(len(email_opens) / n_sends, 4)
            fv.email_click_rate = round(len(email_clicks) / n_sends, 4)
            fv.email_conversion_rate = round(len(email_conversions) / n_sends, 4)

        n_cart_adds = len(cart_adds)
        if n_cart_adds > 0:
            fv.cart_abandonment_rate = round(len(cart_abandons) / n_cart_adds, 4)

        if not sessions.empty:
            fv.website_visit_frequency = float(len(sessions))

    def _compute_health_score(self, fv: CustomerFeatureVector) -> None:
        score = 0.0
        weights = {
            "recency": 30.0,
            "engagement": 25.0,
            "spend_trend": 25.0,
            "frequency": 20.0,
        }

        if fv.recency_days is not None:
            if fv.recency_days <= 30:
                recency_score = 100.0
            elif fv.recency_days <= 60:
                recency_score = 75.0
            elif fv.recency_days <= 90:
                recency_score = 50.0
            elif fv.recency_days <= 180:
                recency_score = 25.0
            else:
                recency_score = 0.0
            score += (recency_score / 100) * weights["recency"]

        open_rate_score = min(fv.email_open_rate * 4, 1.0) * 100
        score += (open_rate_score / 100) * weights["engagement"]

        if fv.recency_trend_90d > 0:
            score += weights["spend_trend"]

        freq_score = min(fv.frequency / 10, 1.0) * 100
        score += (freq_score / 100) * weights["frequency"]

        fv.customer_health_score = round(score, 2)
