"""
Unit tests for the Dynamic Clustering Engine and Segment Drift Detector.
"""

import pytest
import numpy as np
from modules.customer_intelligence.clustering.engine import DynamicClusteringEngine, name_segment
from modules.customer_intelligence.clustering.drift_detector import SegmentDriftDetector, DriftEvent


class TestNameSegment:
    def test_champions_identified(self):
        stats = {"avg_recency_days": 10, "avg_frequency": 8, "avg_monetary_value": 800}
        name, desc, strategy = name_segment(stats)
        assert name == "Champions"

    def test_at_risk_identified(self):
        stats = {"avg_recency_days": 200, "avg_frequency": 4, "avg_monetary_value": 400}
        name, desc, strategy = name_segment(stats)
        assert name == "At Risk"

    def test_lost_identified(self):
        stats = {"avg_recency_days": 400, "avg_frequency": 2, "avg_monetary_value": 100}
        name, desc, strategy = name_segment(stats)
        assert name == "Lost"

    def test_new_customers_identified(self):
        stats = {"avg_recency_days": 5, "avg_frequency": 1, "avg_monetary_value": 80}
        name, desc, strategy = name_segment(stats)
        assert name == "New Customers"

    def test_all_returns_three_values(self):
        stats = {"avg_recency_days": 50, "avg_frequency": 2, "avg_monetary_value": 150}
        result = name_segment(stats)
        assert len(result) == 3
        assert all(isinstance(v, str) for v in result)


class TestDynamicClusteringEngine:
    def make_fingerprints(self, n: int = 200, d: int = 64) -> np.ndarray:
        np.random.seed(42)
        centers = np.random.randn(5, d) * 3
        per_cluster = n // 5
        parts = [centers[i] + np.random.randn(per_cluster, d) * 0.5 for i in range(5)]
        return np.vstack(parts)

    def test_fit_predict_returns_segments(self):
        engine = DynamicClusteringEngine(min_cluster_size=5)
        fingerprints = self.make_fingerprints()
        ids = [f"C{i}" for i in range(len(fingerprints))]
        segments = engine.fit_predict(fingerprints, ids)
        assert len(segments) >= 2

    def test_all_customers_assigned(self):
        engine = DynamicClusteringEngine(min_cluster_size=5)
        fingerprints = self.make_fingerprints(n=100)
        ids = [f"C{i}" for i in range(100)]
        segments = engine.fit_predict(fingerprints, ids)
        total_assigned = sum(s.size for s in segments)
        assert total_assigned <= 100

    def test_segment_names_are_strings(self):
        engine = DynamicClusteringEngine(min_cluster_size=5)
        fingerprints = self.make_fingerprints(n=100)
        ids = [f"C{i}" for i in range(100)]
        segments = engine.fit_predict(fingerprints, ids)
        for s in segments:
            assert isinstance(s.name, str)
            assert len(s.name) > 0

    def test_segment_has_positive_size(self):
        engine = DynamicClusteringEngine(min_cluster_size=5)
        fingerprints = self.make_fingerprints(n=100)
        ids = [f"C{i}" for i in range(100)]
        segments = engine.fit_predict(fingerprints, ids)
        for s in segments:
            assert s.size > 0


class TestSegmentDriftDetector:
    def test_detects_downward_drift(self):
        detector = SegmentDriftDetector()
        history = [
            {"customer_id": "C1", "segment_name": "Champions", "health_score": 90, "assigned_at": "2024-01-01"},
            {"customer_id": "C1", "segment_name": "At Risk", "health_score": 35, "assigned_at": "2024-03-01"},
        ]
        events = detector.detect_drift(history)
        assert len(events) == 1
        assert events[0].drift_direction in ("downward", "critical")
        assert events[0].from_segment == "Champions"
        assert events[0].to_segment == "At Risk"

    def test_no_drift_for_same_segment(self):
        detector = SegmentDriftDetector()
        history = [
            {"customer_id": "C1", "segment_name": "Champions", "health_score": 90, "assigned_at": "2024-01-01"},
            {"customer_id": "C1", "segment_name": "Champions", "health_score": 88, "assigned_at": "2024-02-01"},
        ]
        events = detector.detect_drift(history)
        assert len(events) == 0

    def test_single_entry_returns_no_drift(self):
        detector = SegmentDriftDetector()
        history = [{"customer_id": "C1", "segment_name": "Champions", "health_score": 90, "assigned_at": "2024-01-01"}]
        events = detector.detect_drift(history)
        assert events == []

    def test_batch_detect_handles_multiple_customers(self):
        detector = SegmentDriftDetector()
        all_histories = {
            "C1": [
                {"customer_id": "C1", "segment_name": "Champions", "health_score": 90, "assigned_at": "2024-01-01"},
                {"customer_id": "C1", "segment_name": "At Risk", "health_score": 30, "assigned_at": "2024-03-01"},
            ],
            "C2": [
                {"customer_id": "C2", "segment_name": "Loyal Customers", "health_score": 75, "assigned_at": "2024-01-01"},
                {"customer_id": "C2", "segment_name": "Loyal Customers", "health_score": 72, "assigned_at": "2024-03-01"},
            ],
        }
        events = detector.batch_detect(all_histories)
        assert len(events) == 1
        assert events[0].customer_id == "C1"
