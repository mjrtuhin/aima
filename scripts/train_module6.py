"""
Training script for Module 6: CLV and Churn Predictor.
Trains the DeepChurnModel with survival analysis.
Logs all experiments to MLflow.

Run: python scripts/train_module6.py --experiment clv-churn --epochs 60
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
import structlog
import mlflow
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

log = structlog.get_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Module 6: CLV and Churn Predictor")
    parser.add_argument("--experiment", default="module6-clv-churn", help="MLflow experiment name")
    parser.add_argument("--epochs", type=int, default=60, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size")
    parser.add_argument("--lr", type=float, default=5e-4, help="Learning rate")
    parser.add_argument("--time-bins", type=int, default=12, help="Number of survival time bins")
    parser.add_argument("--output-dir", default="data/models", help="Model output directory")
    parser.add_argument("--mlflow-uri", default="http://localhost:5000", help="MLflow tracking URI")
    return parser.parse_args()


class ChurnDataset(Dataset):
    """Synthetic customer churn dataset for survival analysis training."""

    def __init__(self, n_samples: int = 8000, n_time_bins: int = 12):
        self.samples = []
        self.n_time_bins = n_time_bins

        for _ in range(n_samples):
            recency_days = random.randint(0, 365)
            frequency = random.randint(1, 50)
            monetary = random.uniform(10, 5000)
            engagement_score = random.random()
            tenure_months = random.randint(1, 48)

            churn_risk = (
                0.3 * (recency_days / 365) +
                0.3 * (1 - min(frequency / 50, 1.0)) +
                0.2 * (1 - engagement_score) +
                0.2 * (1 - min(tenure_months / 48, 1.0))
            )

            features = torch.tensor([
                recency_days / 365.0,
                min(frequency / 50.0, 1.0),
                min(monetary / 5000.0, 1.0),
                engagement_score,
                tenure_months / 48.0,
                random.random(),
                random.random(),
                random.random(),
                random.random(),
                random.random(),
                random.random(),
                random.random(),
                random.random(),
                random.random(),
                random.random(),
                random.random(),
            ], dtype=torch.float32)

            survival = torch.zeros(n_time_bins, dtype=torch.float32)
            for t in range(n_time_bins):
                survival[t] = max(0.0, 1.0 - churn_risk * (t + 1) / n_time_bins + random.gauss(0, 0.05))

            event_time = random.randint(0, n_time_bins - 1) if random.random() < churn_risk else n_time_bins - 1

            self.samples.append((features, survival, torch.tensor(event_time, dtype=torch.long)))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        return self.samples[idx]


def train(args: argparse.Namespace) -> None:
    from modules.clv_churn.models.churn_predictor import DeepChurnModel

    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(args.experiment)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("Training device", device=str(device))

    dataset = ChurnDataset(n_samples=8000, n_time_bins=args.time_bins)
    split = int(0.8 * len(dataset))
    train_ds, val_ds = torch.utils.data.random_split(dataset, [split, len(dataset) - split])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    model = DeepChurnModel(n_time_bins=args.time_bins)
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=args.lr * 10,
        steps_per_epoch=len(train_loader),
        epochs=args.epochs,
    )
    survival_criterion = nn.BCEWithLogitsLoss()
    event_criterion = nn.CrossEntropyLoss()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with mlflow.start_run() as run:
        mlflow.log_params({
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "time_bins": args.time_bins,
            "n_train": len(train_ds),
            "n_val": len(val_ds),
            "device": str(device),
        })

        best_val_loss = float("inf")

        for epoch in range(args.epochs):
            model.train()
            train_loss = 0.0

            for features, survival_targets, event_times in train_loader:
                features = features.to(device)
                survival_targets = survival_targets.to(device)
                event_times = event_times.to(device)

                optimizer.zero_grad()

                output = model(features)

                if hasattr(output, "survival_logits"):
                    surv_loss = survival_criterion(output.survival_logits, survival_targets)
                    evt_loss = event_criterion(output.event_logits, event_times)
                    loss = 0.7 * surv_loss + 0.3 * evt_loss
                else:
                    loss = survival_criterion(output, survival_targets)

                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                train_loss += loss.item()

            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for features, survival_targets, event_times in val_loader:
                    features = features.to(device)
                    survival_targets = survival_targets.to(device)
                    event_times = event_times.to(device)

                    output = model(features)

                    if hasattr(output, "survival_logits"):
                        surv_loss = survival_criterion(output.survival_logits, survival_targets)
                        evt_loss = event_criterion(output.event_logits, event_times)
                        val_loss += (0.7 * surv_loss + 0.3 * evt_loss).item()
                    else:
                        val_loss += survival_criterion(output, survival_targets).item()

            avg_train = train_loss / len(train_loader)
            avg_val = val_loss / len(val_loader)

            mlflow.log_metrics({"train_loss": avg_train, "val_loss": avg_val}, step=epoch)

            if avg_val < best_val_loss:
                best_val_loss = avg_val
                model_path = output_dir / "churn_predictor_best.pt"
                torch.save(model.state_dict(), model_path)

            if epoch % 10 == 0:
                log.info("Epoch", epoch=epoch, train_loss=round(avg_train, 4), val_loss=round(avg_val, 4))

        mlflow.log_metric("best_val_loss", best_val_loss)
        mlflow.log_artifact(str(output_dir / "churn_predictor_best.pt"))

        log.info("Training complete", run_id=run.info.run_id, best_val_loss=round(best_val_loss, 4))
        print(f"\nBest validation loss: {best_val_loss:.4f}")
        print(f"MLflow run ID: {run.info.run_id}")


if __name__ == "__main__":
    args = parse_args()
    train(args)
