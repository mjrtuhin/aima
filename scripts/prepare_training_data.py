"""
Training data preparation for AIMA Module 1.
Converts raw datasets into the sequence format required by the
Temporal Behavioral Transformer.
Run: python scripts/prepare_training_data.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
import structlog

log = structlog.get_logger()

DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EVENT_TYPE_VOCAB = {
    "purchase": 1,
    "email_sent": 2,
    "email_opened": 3,
    "email_clicked": 4,
    "email_bounced": 5,
    "session_started": 6,
    "page_viewed": 7,
    "cart_added": 8,
    "cart_abandoned": 9,
    "checkout_started": 10,
    "search": 11,
    "product_viewed": 12,
    "review_left": 13,
    "refund_requested": 14,
    "support_ticket": 15,
    "<pad>": 0,
    "<unk>": 63,
}


def load_uci_retail(data_path: Optional[Path] = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    sample_path = DATA_DIR / "synthetic_sample"
    if sample_path.exists():
        log.info("Loading synthetic sample dataset")
        customers = pd.read_csv(sample_path / "customers.csv")
        orders = pd.read_csv(sample_path / "orders.csv", parse_dates=["ordered_at"])
        return customers, orders

    log.warning("No dataset found, creating minimal synthetic data")
    customers = pd.DataFrame({
        "customer_id": [f"C{i}" for i in range(100)],
        "email": [f"user{i}@example.com" for i in range(100)],
    })
    orders = pd.DataFrame({
        "customer_id": [f"C{i % 100}" for i in range(500)],
        "total": np.random.exponential(80, 500),
        "ordered_at": pd.date_range("2023-01-01", periods=500, freq="6h"),
        "items": np.random.randint(1, 5, 500),
    })
    return customers, orders


def build_customer_sequences(
    orders: pd.DataFrame,
    events: Optional[pd.DataFrame] = None,
    max_seq_len: int = 256,
) -> list[dict]:
    log.info("Building customer event sequences", n_orders=len(orders))
    sequences = []

    for customer_id, group in orders.groupby("customer_id"):
        event_list = []

        for _, row in group.sort_values("ordered_at").iterrows():
            event_list.append({
                "event_type_id": EVENT_TYPE_VOCAB.get("purchase", 63),
                "numerical": [
                    float(row.get("total", 0)) / 1000.0,
                    float(row.get("items", 1)) / 10.0,
                    float(row.get("discount", 0)) / 100.0,
                    0.0, 0.0, 0.0, 0.0, 0.0,
                ],
                "timestamp": str(row.get("ordered_at", "")),
            })

        if events is not None and customer_id in events["customer_id"].values:
            cust_events = events[events["customer_id"] == customer_id].sort_values("occurred_at")
            for _, ev in cust_events.iterrows():
                event_list.append({
                    "event_type_id": EVENT_TYPE_VOCAB.get(ev.get("event_type", ""), 63),
                    "numerical": [0.0] * 8,
                    "timestamp": str(ev.get("occurred_at", "")),
                })

        event_list = sorted(event_list, key=lambda x: x["timestamp"])
        event_list = event_list[-max_seq_len:]

        if len(event_list) < 2:
            continue

        sequences.append({
            "customer_id": str(customer_id),
            "event_types": [e["event_type_id"] for e in event_list],
            "numerical_features": [e["numerical"] for e in event_list],
            "seq_len": len(event_list),
        })

    log.info("Sequences built", total=len(sequences))
    return sequences


def save_sequences(sequences: list[dict], split: float = 0.8) -> None:
    import random
    random.shuffle(sequences)
    n_train = int(len(sequences) * split)
    train = sequences[:n_train]
    val = sequences[n_train:]

    for name, data in [("train", train), ("val", val)]:
        path = OUTPUT_DIR / f"customer_sequences_{name}.json"
        with open(path, "w") as f:
            json.dump(data, f)
        log.info("Saved sequence split", split=name, n=len(data), path=str(path))


def compute_dataset_stats(sequences: list[dict]) -> dict:
    seq_lens = [s["seq_len"] for s in sequences]
    return {
        "n_sequences": len(sequences),
        "avg_seq_len": round(float(np.mean(seq_lens)), 2),
        "max_seq_len": int(np.max(seq_lens)),
        "min_seq_len": int(np.min(seq_lens)),
        "median_seq_len": float(np.median(seq_lens)),
    }


def main() -> None:
    print("\nAIMA Training Data Preparation")
    print("=" * 50)

    customers, orders = load_uci_retail()
    log.info("Dataset loaded", customers=len(customers), orders=len(orders))

    events = None
    events_path = DATA_DIR / "synthetic_sample" / "events.csv"
    if events_path.exists():
        events = pd.read_csv(events_path, parse_dates=["occurred_at"])
        log.info("Events loaded", n_events=len(events))

    sequences = build_customer_sequences(orders, events)
    stats = compute_dataset_stats(sequences)
    print("\nDataset stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    save_sequences(sequences)

    stats_path = OUTPUT_DIR / "dataset_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\nTraining data ready in {OUTPUT_DIR}/")
    print("Next step: Run scripts/train_module1.py to train the Temporal Behavioral Transformer.")


if __name__ == "__main__":
    main()
