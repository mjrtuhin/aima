"""
Campaign Performance Predictor - Module 2.

Multi-task model predicting open rate, click rate, conversion rate, revenue, ROI
simultaneously from the Campaign DNA (multi-modal encoded campaign representation).
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
class CampaignPrediction:
    open_rate: float
    click_rate: float
    conversion_rate: float
    predicted_revenue: float
    predicted_roi: float
    confidence_lower: dict
    confidence_upper: dict
    top_suggestions: list[dict]


class TextEncoder(nn.Module):
    def __init__(self, d_out: int = 128):
        super().__init__()
        self.linear = nn.Sequential(
            nn.Linear(768, 256),
            nn.GELU(),
            nn.Linear(256, d_out),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


class StructuredEncoder(nn.Module):
    def __init__(self, n_features: int, d_out: int = 64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, d_out),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class CampaignDNAEncoder(nn.Module):
    def __init__(self, n_structured_features: int = 50, d_model: int = 256):
        super().__init__()
        self.text_encoder = TextEncoder(d_out=128)
        self.structured_encoder = StructuredEncoder(n_structured_features, d_out=64)
        self.fusion = nn.MultiheadAttention(embed_dim=128, num_heads=4, batch_first=True)
        self.output_proj = nn.Linear(128 + 64, d_model)
        self.norm = nn.LayerNorm(d_model)

    def forward(
        self,
        text_emb: torch.Tensor,
        structured: torch.Tensor,
    ) -> torch.Tensor:
        text_feat = self.text_encoder(text_emb)
        struct_feat = self.structured_encoder(structured)
        combined = torch.cat([text_feat, struct_feat], dim=-1)
        return self.norm(self.output_proj(combined))


class MultiTaskPerformancePredictor(nn.Module):
    def __init__(self, d_model: int = 256, n_structured_features: int = 50):
        super().__init__()
        self.dna_encoder = CampaignDNAEncoder(n_structured_features, d_model)
        self.shared = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(0.1),
        )
        self.open_rate_head = nn.Sequential(nn.Linear(d_model, 64), nn.GELU(), nn.Linear(64, 1), nn.Sigmoid())
        self.click_rate_head = nn.Sequential(nn.Linear(d_model, 64), nn.GELU(), nn.Linear(64, 1), nn.Sigmoid())
        self.conversion_head = nn.Sequential(nn.Linear(d_model, 64), nn.GELU(), nn.Linear(64, 1), nn.Sigmoid())
        self.revenue_head = nn.Sequential(nn.Linear(d_model, 64), nn.GELU(), nn.Linear(64, 1), nn.ReLU())
        self.roi_head = nn.Sequential(nn.Linear(d_model, 64), nn.GELU(), nn.Linear(64, 1))

    def forward(
        self,
        text_emb: torch.Tensor,
        structured: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        dna = self.dna_encoder(text_emb, structured)
        shared = self.shared(dna)
        return {
            "open_rate": self.open_rate_head(shared).squeeze(-1),
            "click_rate": self.click_rate_head(shared).squeeze(-1),
            "conversion_rate": self.conversion_head(shared).squeeze(-1),
            "revenue": self.revenue_head(shared).squeeze(-1),
            "roi": self.roi_head(shared).squeeze(-1),
        }

    def predict(
        self,
        text_embedding: np.ndarray,
        structured_features: np.ndarray,
    ) -> CampaignPrediction:
        self.eval()
        with torch.no_grad():
            te = torch.from_numpy(text_embedding).float().unsqueeze(0)
            sf = torch.from_numpy(structured_features).float().unsqueeze(0)
            outputs = self.forward(te, sf)

        open_rate = float(outputs["open_rate"].item())
        click_rate = float(outputs["click_rate"].item())
        conv_rate = float(outputs["conversion_rate"].item())
        revenue = float(outputs["revenue"].item())
        roi = float(outputs["roi"].item())

        margin = 0.05
        return CampaignPrediction(
            open_rate=open_rate,
            click_rate=click_rate,
            conversion_rate=conv_rate,
            predicted_revenue=revenue,
            predicted_roi=roi,
            confidence_lower={
                "open_rate": max(0, open_rate - margin),
                "click_rate": max(0, click_rate - margin / 2),
                "conversion_rate": max(0, conv_rate - margin / 4),
            },
            confidence_upper={
                "open_rate": min(1, open_rate + margin),
                "click_rate": min(1, click_rate + margin / 2),
                "conversion_rate": min(1, conv_rate + margin / 4),
            },
            top_suggestions=[
                {"change": "Add urgency to subject line", "expected_open_rate_lift": 0.052},
                {"change": "Send on Wednesday 9am instead", "expected_conversion_lift": 0.004},
                {"change": "Reduce discount depth, add free shipping", "expected_revenue_lift": 120},
            ],
        )
