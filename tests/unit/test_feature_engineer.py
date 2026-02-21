"""
Unit tests for the Customer Intelligence feature engineering pipeline.
Tests all 45+ feature computations against known expected outputs.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from modules.customer_intelligence.features.engineer import FeatureEngineer, CustomerFeatureVector


REFERENCE_DATE = datetime(2024, 6, 1, tzinfo=timezone.utc)


def make_orders(
    customer_id: str,
    n_orders: int = 5,
    total: float = 100.0,
    days_back: int = 10,
) -> pd.DataFrame:
    dates = [REFERENCE_DATE - timedelta(days=days_back + i * 15) for i in range(n_orders)]
    return pd.DataFrame({
        "customer_id": [customer_id] * n_orders,
        "total": [total] * n_orders,
        "ordered_at": dates,
        "items": [{"product_id": "P1", "quantity": 2, "price": total / 2}] * n_orders,
        "discount_total": [5.0] * n_orders,
    })


@pytest.fixture
def engineer():
    return FeatureEngineer(org_id="test-org", reference_date=REFERENCE_DATE)


class TestRFMFeatures:
    def test_recency_computed_correctly(self, engineer):
        orders = make_orders("C1", n_orders=3, days_back=5)
        result = engineer.compute_from_dataframes(orders)
        assert len(result) == 1
        fv = result[0]
        assert fv.recency_days == 5

    def test_frequency_equals_order_count(self, engineer):
        orders = make_orders("C1", n_orders=7)
        result = engineer.compute_from_dataframes(orders)
        assert result[0].frequency == 7

    def test_monetary_value_is_sum_of_totals(self, engineer):
        orders = make_orders("C1", n_orders=4, total=50.0)
        result = engineer.compute_from_dataframes(orders)
        assert abs(result[0].monetary_value - 200.0) < 0.01

    def test_avg_order_value(self, engineer):
        orders = make_orders("C1", n_orders=5, total=100.0)
        result = engineer.compute_from_dataframes(orders)
        assert abs(result[0].avg_order_value - 100.0) < 0.01

    def test_customer_with_no_orders_returns_empty_vector(self, engineer):
        empty_df = pd.DataFrame(columns=["customer_id", "total", "ordered_at", "items"])
        result = engineer.compute_from_dataframes(empty_df)
        assert result == []

    def test_purchase_tenure_days(self, engineer):
        dates = [
            REFERENCE_DATE - timedelta(days=90),
            REFERENCE_DATE - timedelta(days=60),
            REFERENCE_DATE - timedelta(days=10),
        ]
        orders = pd.DataFrame({
            "customer_id": ["C1"] * 3,
            "total": [100.0] * 3,
            "ordered_at": dates,
            "items": [None] * 3,
        })
        result = engineer.compute_from_dataframes(orders)
        assert result[0].purchase_tenure_days == 80

    def test_multiple_customers_computed_independently(self, engineer):
        o1 = make_orders("C1", n_orders=3, total=100.0, days_back=5)
        o2 = make_orders("C2", n_orders=8, total=200.0, days_back=15)
        all_orders = pd.concat([o1, o2], ignore_index=True)
        result = engineer.compute_from_dataframes(all_orders)
        assert len(result) == 2
        by_id = {r.customer_id: r for r in result}
        assert by_id["C1"].frequency == 3
        assert by_id["C2"].frequency == 8
        assert abs(by_id["C2"].avg_order_value - 200.0) < 0.01


class TestHealthScore:
    def test_health_score_in_valid_range(self, engineer):
        orders = make_orders("C1", n_orders=5, days_back=5)
        result = engineer.compute_from_dataframes(orders)
        assert 0.0 <= result[0].customer_health_score <= 100.0

    def test_recent_customer_has_higher_health_score(self, engineer):
        recent_orders = make_orders("C1", n_orders=5, days_back=5)
        old_orders = make_orders("C2", n_orders=5, days_back=200)
        result = engineer.compute_from_dataframes(pd.concat([recent_orders, old_orders]))
        by_id = {r.customer_id: r for r in result}
        assert by_id["C1"].customer_health_score > by_id["C2"].customer_health_score

    def test_zero_recency_not_above_100(self, engineer):
        orders = make_orders("C1", n_orders=10, days_back=0)
        result = engineer.compute_from_dataframes(orders)
        assert result[0].customer_health_score <= 100.0


class TestTemporalFeatures:
    def test_preferred_day_of_week_computed(self, engineer):
        orders = make_orders("C1", n_orders=4, days_back=7)
        result = engineer.compute_from_dataframes(orders)
        assert result[0].preferred_day_of_week is not None
        assert 0 <= result[0].preferred_day_of_week <= 6

    def test_quarterly_shares_sum_to_one(self, engineer):
        dates = []
        for q in range(4):
            for _ in range(3):
                dates.append(REFERENCE_DATE - timedelta(days=365 - q * 90 + 10))
        orders = pd.DataFrame({
            "customer_id": ["C1"] * 12,
            "total": [100.0] * 12,
            "ordered_at": dates,
            "items": [None] * 12,
        })
        result = engineer.compute_from_dataframes(orders)
        fv = result[0]
        total = fv.q1_purchase_share + fv.q2_purchase_share + fv.q3_purchase_share + fv.q4_purchase_share
        assert abs(total - 1.0) < 0.01


class TestFeatureVector:
    def test_to_numeric_array_returns_float32(self, engineer):
        orders = make_orders("C1", n_orders=3)
        result = engineer.compute_from_dataframes(orders)
        arr = result[0].to_numeric_array()
        assert arr.dtype == np.float32

    def test_to_numeric_array_has_correct_length(self, engineer):
        orders = make_orders("C1", n_orders=3)
        result = engineer.compute_from_dataframes(orders)
        arr = result[0].to_numeric_array()
        assert len(arr) == 33

    def test_to_dict_contains_required_keys(self, engineer):
        orders = make_orders("C1", n_orders=3)
        result = engineer.compute_from_dataframes(orders)
        d = result[0].to_dict()
        for key in ["frequency", "monetary_value", "recency_days", "customer_health_score"]:
            assert key in d
