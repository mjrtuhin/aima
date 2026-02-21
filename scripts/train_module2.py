"""
Training script for Module 2: Campaign Performance Predictor.
Trains the MultiTaskPerformancePredictor and logs all experiments to MLflow.

Run: python scripts/train_module2.py --experiment campaign-predictor --epochs 40
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
import structlog
import mlflow
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

log = structlog.get_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Module 2: Campaign Performance Predictor")
    parser.add_argument("--experiment", default="module2-campaign-predictor", help="MLflow experiment name")
    parser.add_argument("--epochs", type=int, default=40, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Training batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--data-dir", default="data/processed", help="Processed data directory")
    parser.add_argument("--output-dir", default="data/models", help="Model output directory")
    parser.add_argument("--mlflow-uri", default="http://localhost:5000", help="MLflow tracking URI")
    return parser.parse_args()


class CampaignDataset(Dataset):
    """Synthetic campaign dataset for training the performance predictor."""

    def __init__(self, n_samples: int = 5000):
        self.samples = []
        for _ in range(n_samples):
            channel = random.randint(0, 5)
            segment_size = random.randint(100, 50000)
            hour = random.randint(0, 23)
            day_of_week = random.randint(0, 6)
            subject_length = random.randint(20, 80)

            features = torch.tensor([
                channel / 5.0,
                min(segment_size / 50000.0, 1.0),
                hour / 23.0,
                day_of_week / 6.0,
                subject_length / 80.0,
                random.random(),
                random.random(),
                random.random(),
            ], dtype=torch.float32)

            base_open = 0.15 + (0.2 if hour in [9, 10, 11, 14, 15] else 0) + random.gauss(0, 0.05)
            base_click = base_open * 0.15 + random.gauss(0, 0.02)
            base_conv = base_click * 0.05 + random.gauss(0, 0.005)
            base_revenue = segment_size * base_conv * (20 + random.gauss(0, 5))
            base_roi = (base_revenue / max(segment_size * 0.01, 1)) - 1

            targets = torch.tensor([
                max(0.0, min(1.0, base_open)),
                max(0.0, min(1.0, base_click)),
                max(0.0, min(1.0, base_conv)),
                max(0.0, base_revenue),
                base_roi,
            ], dtype=torch.float32)

            self.samples.append((features, targets))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        return self.samples[idx]


def train(args: argparse.Namespace) -> None:
    from modules.campaign_predictor.models.predictor import MultiTaskPerformancePredictor

    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(args.experiment)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("Training device", device=str(device))

    dataset = CampaignDataset(n_samples=5000)
    split = int(0.8 * len(dataset))
    train_ds, val_ds = torch.utils.data.random_split(dataset, [split, len(dataset) - split])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    model = MultiTaskPerformancePredictor()
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.MSELoss()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with mlflow.start_run() as run:
        mlflow.log_params({
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "n_train": len(train_ds),
            "n_val": len(val_ds),
            "device": str(device),
        })

        best_val_loss = float("inf")

        for epoch in range(args.epochs):
            model.train()
            train_loss = 0.0
            for features, targets in train_loader:
                features, targets = features.to(device), targets.to(device)
                optimizer.zero_grad()

                dummy_text = ["sample campaign content"] * features.size(0)
                preds = model(dummy_text, features)

                loss = criterion(preds, targets)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                train_loss += loss.item()

            scheduler.step()

            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for features, targets in val_loader:
                    features, targets = features.to(device), targets.to(device)
                    dummy_text = ["sample campaign content"] * features.size(0)
                    preds = model(dummy_text, features)
                    val_loss += criterion(preds, targets).item()

            avg_train = train_loss / len(train_loader)
            avg_val = val_loss / len(val_loader)

            mlflow.log_metrics({
                "train_loss": avg_train,
                "val_loss": avg_val,
                "lr": scheduler.get_last_lr()[0],
            }, step=epoch)

            if avg_val < best_val_loss:
                best_val_loss = avg_val
                model_path = output_dir / "campaign_predictor_best.pt"
                torch.save(model.state_dict(), model_path)

            if epoch % 10 == 0:
                log.info("Epoch", epoch=epoch, train_loss=round(avg_train, 4), val_loss=round(avg_val, 4))

        mlflow.log_metric("best_val_loss", best_val_loss)
        mlflow.log_artifact(str(output_dir / "campaign_predictor_best.pt"))

        log.info("Training complete", run_id=run.info.run_id, best_val_loss=round(best_val_loss, 4))
        print(f"\nBest validation loss: {best_val_loss:.4f}")
        print(f"MLflow run ID: {run.info.run_id}")


if __name__ == "__main__":
    args = parse_args()
    train(args)
