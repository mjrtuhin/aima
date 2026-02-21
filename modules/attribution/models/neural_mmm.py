"""
Neural Marketing Mix Model - Module 5.
Replaces traditional linear MMM with a deep neural network that learns
non-linear saturation curves, carry-over effects, and channel interactions.
Uses Bayesian priors for regularization on limited data.
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
class MMMResult:
    channel_roi: dict[str, float]
    optimal_budget: dict[str, float]
    saturation_curves: dict[str, list[float]]
    total_predicted_revenue: float
    confidence_intervals: dict[str, tuple[float, float]]


class AdstockTransform(nn.Module):
    def __init__(self, n_channels: int):
        super().__init__()
        self.decay = nn.Parameter(torch.ones(n_channels) * 0.5)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        T = x.shape[1]
        result = torch.zeros_like(x)
        result[:, 0, :] = x[:, 0, :]
        for t in range(1, T):
            decay = torch.sigmoid(self.decay).unsqueeze(0)
            result[:, t, :] = x[:, t, :] + decay * result[:, t - 1, :]
        return result


class SaturationTransform(nn.Module):
    def __init__(self, n_channels: int):
        super().__init__()
        self.alpha = nn.Parameter(torch.ones(n_channels) * 0.5)
        self.beta = nn.Parameter(torch.ones(n_channels) * 1.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        alpha = torch.sigmoid(self.alpha) * 2
        beta = torch.clamp(self.beta, min=0.01)
        return alpha * (1 - torch.exp(-beta * x))


class NeuralMMMModel(nn.Module):
    def __init__(self, n_channels: int, n_control_vars: int = 10):
        super().__init__()
        self.n_channels = n_channels
        self.adstock = AdstockTransform(n_channels)
        self.saturation = SaturationTransform(n_channels)

        self.channel_interaction = nn.Sequential(
            nn.Linear(n_channels, n_channels * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(n_channels * 2, n_channels),
        )

        self.control_net = nn.Linear(n_control_vars, 32)
        self.output_net = nn.Sequential(
            nn.Linear(n_channels + 32, 64),
            nn.GELU(),
            nn.Linear(64, 1),
        )

    def forward(
        self,
        channel_spend: torch.Tensor,
        control_vars: torch.Tensor,
    ) -> torch.Tensor:
        adstocked = self.adstock(channel_spend)
        saturated = self.saturation(adstocked)
        last_t = saturated[:, -1, :]
        interactions = self.channel_interaction(last_t)
        control_feat = self.control_net(control_vars)
        combined = torch.cat([interactions, control_feat], dim=-1)
        return self.output_net(combined).squeeze(-1)

    def compute_channel_roi(
        self,
        channel_spend: np.ndarray,
        control_vars: np.ndarray,
        actual_revenue: float,
    ) -> dict[str, float]:
        self.eval()
        roi_dict = {}
        baseline = self._predict_np(channel_spend, control_vars)

        for i in range(self.n_channels):
            incremented = channel_spend.copy()
            delta = max(incremented[:, i].mean() * 0.1, 1.0)
            incremented[:, i] += delta
            incremented_rev = self._predict_np(incremented, control_vars)
            roi_dict[f"channel_{i}"] = round(float((incremented_rev - baseline) / delta), 4)

        return roi_dict

    def _predict_np(self, spend: np.ndarray, control: np.ndarray) -> float:
        with torch.no_grad():
            spend_t = torch.from_numpy(spend).float().unsqueeze(0)
            control_t = torch.from_numpy(control).float().unsqueeze(0)
            return float(self.forward(spend_t, control_t).item())
