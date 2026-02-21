"""
Training script for Module 1: Customer Intelligence Engine.
Trains the Temporal Behavioral Transformer and runs the clustering pipeline.
Logs all experiments to MLflow.

Run: python scripts/train_module1.py --experiment my_experiment --epochs 50
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import structlog
import mlflow

log = structlog.get_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Module 1: Customer Intelligence Engine")
    parser.add_argument("--experiment", default="module1-customer-intelligence", help="MLflow experiment name")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size")
    parser.add_argument("--d-model", type=int, default=128, help="Transformer model dimension")
    parser.add_argument("--n-heads", type=int, default=8, help="Number of attention heads")
    parser.add_argument("--n-layers", type=int, default=4, help="Number of transformer layers")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--data-dir", default="data/processed", help="Processed data directory")
    parser.add_argument("--output-dir", default="data/models", help="Model output directory")
    parser.add_argument("--mlflow-uri", default="http://localhost:5000", help="MLflow tracking URI")
    return parser.parse_args()


def load_sequences(data_dir: str, split: str = "train") -> list[dict]:
    path = Path(data_dir) / f"customer_sequences_{split}.json"
    if not path.exists():
        log.warning("Sequence file not found, running data preparation first", path=str(path))
        import subprocess
        subprocess.run(["python", "scripts/prepare_training_data.py"], check=True)

    with open(path) as f:
        return json.load(f)


def train(args: argparse.Namespace) -> None:
    from modules.customer_intelligence.models.transformer import (
        TemporalBehavioralTransformer,
        TBTConfig,
    )
    import torch

    mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(args.experiment)

    log.info("Loading training sequences", data_dir=args.data_dir)
    train_sequences = load_sequences(args.data_dir, "train")
    val_sequences = load_sequences(args.data_dir, "val")
    log.info("Sequences loaded", train=len(train_sequences), val=len(val_sequences))

    config = TBTConfig(
        d_model=args.d_model,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )

    model = TemporalBehavioralTransformer(config=config)
    log.info("Model created", parameters=model.count_parameters())

    with mlflow.start_run() as run:
        mlflow.log_params({
            "d_model": config.d_model,
            "n_heads": config.n_heads,
            "n_layers": config.n_layers,
            "epochs": config.epochs,
            "batch_size": config.batch_size,
            "lr": config.learning_rate,
            "n_train": len(train_sequences),
            "n_val": len(val_sequences),
            "parameters": model.count_parameters(),
        })

        log.info("Starting training", run_id=run.info.run_id)
        metrics = model.train_model(
            train_sequences=train_sequences,
            val_sequences=val_sequences,
        )

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / "tbt_model.pt"
        torch.save(model.state_dict(), model_path)
        mlflow.log_artifact(str(model_path))

        final_loss = metrics["train_loss"][-1] if metrics["train_loss"] else 0
        mlflow.log_metric("final_train_loss", final_loss)

        log.info("Training complete", run_id=run.info.run_id, final_loss=round(final_loss, 4))
        print(f"\nModel saved to {model_path}")
        print(f"MLflow run ID: {run.info.run_id}")


if __name__ == "__main__":
    args = parse_args()
    train(args)
