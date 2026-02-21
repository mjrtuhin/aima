"""
Temporal Behavioral Transformer - Module 1's core novel AI model.

Treats customer behavior as a TIME SEQUENCE, not a snapshot.
A Transformer architecture learns from sequences of customer events to build
dense behavioral fingerprint vectors - capturing full behavioral history in a way
that simple RFM or feature engineering cannot.

Architecture:
  - Event embedding layer (event_type + numerical context → d_model vector)
  - Positional encoding (to preserve event order)
  - N Transformer encoder layers with multi-head self-attention
  - CLS token pooling → final behavioral fingerprint
  - MLflow experiment tracking throughout
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class TBTConfig:
    d_model: int = 128
    n_heads: int = 8
    n_layers: int = 4
    d_ff: int = 512
    dropout: float = 0.1
    max_seq_len: int = 512
    n_event_types: int = 64
    n_numerical_features: int = 8
    output_dim: int = 64
    learning_rate: float = 1e-4
    batch_size: int = 64
    epochs: int = 50
    warmup_steps: int = 1000


class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class EventEmbedding(nn.Module):
    def __init__(self, config: TBTConfig):
        super().__init__()
        self.event_embed = nn.Embedding(config.n_event_types, config.d_model // 2)
        self.numerical_proj = nn.Linear(config.n_numerical_features, config.d_model // 2)
        self.output_proj = nn.Linear(config.d_model, config.d_model)
        self.norm = nn.LayerNorm(config.d_model)

    def forward(self, event_types: torch.Tensor, numerical_features: torch.Tensor) -> torch.Tensor:
        event_emb = self.event_embed(event_types)
        num_emb = self.numerical_proj(numerical_features)
        combined = torch.cat([event_emb, num_emb], dim=-1)
        return self.norm(self.output_proj(combined))


class TemporalBehavioralTransformer(nn.Module):
    def __init__(self, config: Optional[TBTConfig] = None):
        super().__init__()
        self.config = config or TBTConfig()

        self.cls_token = nn.Parameter(torch.randn(1, 1, self.config.d_model))
        self.event_embedding = EventEmbedding(self.config)
        self.pos_encoding = PositionalEncoding(
            self.config.d_model, self.config.max_seq_len + 1, self.config.dropout
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.config.d_model,
            nhead=self.config.n_heads,
            dim_feedforward=self.config.d_ff,
            dropout=self.config.dropout,
            batch_first=True,
            norm_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer, num_layers=self.config.n_layers
        )

        self.output_head = nn.Sequential(
            nn.Linear(self.config.d_model, self.config.d_model),
            nn.GELU(),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.d_model, self.config.output_dim),
        )

        self._init_weights()

    def _init_weights(self) -> None:
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(
        self,
        event_types: torch.Tensor,
        numerical_features: torch.Tensor,
        padding_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        B = event_types.shape[0]

        event_emb = self.event_embedding(event_types, numerical_features)

        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, event_emb], dim=1)

        x = self.pos_encoding(x)

        if padding_mask is not None:
            cls_mask = torch.zeros(B, 1, dtype=torch.bool, device=padding_mask.device)
            padding_mask = torch.cat([cls_mask, padding_mask], dim=1)

        x = self.transformer_encoder(x, src_key_padding_mask=padding_mask)

        cls_output = x[:, 0, :]
        fingerprint = self.output_head(cls_output)

        return fingerprint

    def get_fingerprint(
        self,
        event_types: np.ndarray,
        numerical_features: np.ndarray,
    ) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            et = torch.from_numpy(event_types).long().unsqueeze(0)
            nf = torch.from_numpy(numerical_features).float().unsqueeze(0)
            fingerprint = self.forward(et, nf)
            return fingerprint.squeeze(0).numpy()

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def train_model(
        self,
        train_sequences: list[dict],
        val_sequences: Optional[list[dict]] = None,
        mlflow_experiment: Optional[str] = None,
    ) -> dict:
        import mlflow
        from torch.optim import Adam
        from torch.optim.lr_scheduler import CosineAnnealingLR

        log.info(
            "Starting TBT training",
            n_customers=len(train_sequences),
            params=self.count_parameters(),
        )

        if mlflow_experiment:
            mlflow.set_experiment(mlflow_experiment)
            mlflow.pytorch.autolog()

        optimizer = Adam(self.parameters(), lr=self.config.learning_rate, weight_decay=1e-5)
        scheduler = CosineAnnealingLR(optimizer, T_max=self.config.epochs)

        self.train()
        metrics = {"train_loss": [], "val_loss": []}

        for epoch in range(self.config.epochs):
            epoch_loss = 0.0
            n_batches = 0

            for i in range(0, len(train_sequences), self.config.batch_size):
                batch = train_sequences[i : i + self.config.batch_size]
                et, nf, mask = self._prepare_batch(batch)
                optimizer.zero_grad()
                fingerprints = self.forward(et, nf, mask)
                loss = self._contrastive_loss(fingerprints, batch)
                loss.backward()
                nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)
                optimizer.step()
                epoch_loss += loss.item()
                n_batches += 1

            avg_loss = epoch_loss / max(n_batches, 1)
            metrics["train_loss"].append(avg_loss)
            scheduler.step()

            if epoch % 10 == 0:
                log.info("Training epoch", epoch=epoch, loss=round(avg_loss, 4))
                if mlflow_experiment:
                    mlflow.log_metric("train_loss", avg_loss, step=epoch)

        return metrics

    def _prepare_batch(
        self, batch: list[dict]
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        max_len = min(max(len(s["event_types"]) for s in batch), self.config.max_seq_len)
        n = self.config.n_numerical_features

        et_tensor = torch.zeros(len(batch), max_len, dtype=torch.long)
        nf_tensor = torch.zeros(len(batch), max_len, n, dtype=torch.float)
        mask_tensor = torch.ones(len(batch), max_len, dtype=torch.bool)

        for i, seq in enumerate(batch):
            seq_len = min(len(seq["event_types"]), max_len)
            et_tensor[i, :seq_len] = torch.tensor(seq["event_types"][:seq_len])
            if seq.get("numerical_features") is not None:
                nf = np.array(seq["numerical_features"][:seq_len])
                nf_tensor[i, :seq_len, : min(nf.shape[1], n)] = torch.from_numpy(nf[:, :n])
            mask_tensor[i, :seq_len] = False

        return et_tensor, nf_tensor, mask_tensor

    def _contrastive_loss(
        self, fingerprints: torch.Tensor, batch: list[dict], temperature: float = 0.07
    ) -> torch.Tensor:
        fingerprints = F.normalize(fingerprints, p=2, dim=1)
        similarity = torch.matmul(fingerprints, fingerprints.T) / temperature
        labels = torch.arange(len(batch), device=fingerprints.device)
        loss = F.cross_entropy(similarity, labels)
        return loss
