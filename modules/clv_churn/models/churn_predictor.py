"""
Deep Churn Prediction Model - Module 6.
Uses a survival analysis approach (DeepHit-inspired) to predict not just
WHETHER a customer will churn, but WHEN - the full probability distribution over time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import torch
import torch.nn as nn
import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class ChurnPrediction:
    customer_id: str
    churn_probability_30d: float
    churn_probability_60d: float
    churn_probability_90d: float
    survival_curve: list[float]
    predicted_days_to_churn: Optional[float]
    risk_level: str
    recommended_intervention: str

    @property
    def is_high_risk(self) -> bool:
        return self.churn_probability_30d >= 0.6

    @property
    def is_medium_risk(self) -> bool:
        return 0.3 <= self.churn_probability_30d < 0.6


class DeepChurnModel(nn.Module):
    def __init__(self, n_features: int = 33, n_time_bins: int = 12, d_hidden: int = 128):
        super().__init__()
        self.n_time_bins = n_time_bins

        self.shared_net = nn.Sequential(
            nn.Linear(n_features, d_hidden),
            nn.LayerNorm(d_hidden),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(d_hidden, d_hidden),
            nn.GELU(),
            nn.Dropout(0.2),
        )

        self.cause_specific_net = nn.Sequential(
            nn.Linear(d_hidden, 64),
            nn.GELU(),
            nn.Linear(64, n_time_bins),
            nn.Softmax(dim=-1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        shared = self.shared_net(x)
        hazard = self.cause_specific_net(shared)
        return hazard

    def predict_churn(
        self,
        feature_vector: np.ndarray,
        customer_id: str,
        days_per_bin: int = 30,
    ) -> ChurnPrediction:
        self.eval()
        with torch.no_grad():
            x = torch.from_numpy(feature_vector).float().unsqueeze(0)
            hazard = self.forward(x).squeeze(0).numpy()

        survival = np.cumprod(1 - hazard)
        survival_list = survival.tolist()

        churn_30d = 1 - survival[0]
        churn_60d = 1 - survival[min(1, len(survival) - 1)]
        churn_90d = 1 - survival[min(2, len(survival) - 1)]

        median_bin = np.searchsorted(1 - survival, 0.5)
        predicted_days = float(median_bin * days_per_bin) if median_bin < len(survival) else None

        if churn_30d >= 0.6:
            risk = "high"
            intervention = "immediate_personal_outreach"
        elif churn_30d >= 0.3:
            risk = "medium"
            intervention = "personalized_win_back_offer"
        else:
            risk = "low"
            intervention = "standard_nurture_sequence"

        return ChurnPrediction(
            customer_id=customer_id,
            churn_probability_30d=round(float(churn_30d), 4),
            churn_probability_60d=round(float(churn_60d), 4),
            churn_probability_90d=round(float(churn_90d), 4),
            survival_curve=survival_list,
            predicted_days_to_churn=predicted_days,
            risk_level=risk,
            recommended_intervention=intervention,
        )
