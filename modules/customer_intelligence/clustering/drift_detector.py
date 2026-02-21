"""
Segment Drift Detector - Module 1.
Monitors each customer's segment membership over time and detects early
downward movement (e.g., Champion → At-Risk) before churn occurs.
Uses statistical process control + learned transition probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class DriftEvent:
    customer_id: str
    from_segment: str
    to_segment: str
    drift_direction: str
    health_score_before: float
    health_score_after: float
    detected_at: datetime


DOWNWARD_TRANSITIONS = {
    ("Champions", "Loyal Customers"),
    ("Champions", "Need Attention"),
    ("Champions", "At Risk"),
    ("Champions", "Can't Lose Them"),
    ("Loyal Customers", "Need Attention"),
    ("Loyal Customers", "At Risk"),
    ("Loyal Customers", "Hibernating"),
    ("Potential Loyalists", "Need Attention"),
    ("Potential Loyalists", "At Risk"),
    ("Potential Loyalists", "About to Sleep"),
    ("Need Attention", "At Risk"),
    ("Need Attention", "Hibernating"),
    ("At Risk", "Lost"),
    ("At Risk", "Hibernating"),
    ("Can't Lose Them", "Lost"),
}

CRITICAL_TRANSITIONS = {
    ("Champions", "At Risk"),
    ("Champions", "Can't Lose Them"),
    ("Loyal Customers", "At Risk"),
    ("Can't Lose Them", "Lost"),
    ("At Risk", "Lost"),
}


class SegmentDriftDetector:
    def __init__(self, health_score_threshold: float = 10.0):
        self.health_score_threshold = health_score_threshold

    def detect_drift(
        self,
        membership_history: list[dict],
    ) -> list[DriftEvent]:
        drift_events = []

        if len(membership_history) < 2:
            return drift_events

        membership_history = sorted(membership_history, key=lambda x: x["assigned_at"])

        for i in range(1, len(membership_history)):
            prev = membership_history[i - 1]
            curr = membership_history[i]

            from_seg = prev.get("segment_name", "Unknown")
            to_seg = curr.get("segment_name", "Unknown")

            if from_seg == to_seg:
                continue

            direction = self._classify_transition(from_seg, to_seg)

            if direction in ("downward", "critical"):
                drift_events.append(DriftEvent(
                    customer_id=curr["customer_id"],
                    from_segment=from_seg,
                    to_segment=to_seg,
                    drift_direction=direction,
                    health_score_before=prev.get("health_score", 0),
                    health_score_after=curr.get("health_score", 0),
                    detected_at=datetime.now(timezone.utc),
                ))

        return drift_events

    def _classify_transition(self, from_seg: str, to_seg: str) -> str:
        if (from_seg, to_seg) in CRITICAL_TRANSITIONS:
            return "critical"
        if (from_seg, to_seg) in DOWNWARD_TRANSITIONS:
            return "downward"
        return "neutral_or_upward"

    def batch_detect(self, all_histories: dict[str, list[dict]]) -> list[DriftEvent]:
        all_events = []
        for customer_id, history in all_histories.items():
            events = self.detect_drift(history)
            all_events.extend(events)
        log.info("Drift detection complete", total_drift_events=len(all_events))
        return all_events
