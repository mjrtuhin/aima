"""
Dataset downloader for AIMA research training data.
Downloads and prepares the 5 key datasets needed for model training.
Run: python scripts/download_datasets.py
"""

import os
import sys
import zipfile
import tarfile
from pathlib import Path
import urllib.request
import structlog

log = structlog.get_logger()

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)


DATASETS = {
    "uci_online_retail": {
        "description": "UCI Online Retail Dataset - transaction data for Module 1 training",
        "url": "https://archive.ics.uci.edu/static/public/352/online+retail.zip",
        "filename": "online_retail.zip",
        "target_dir": DATA_DIR / "uci_online_retail",
        "instruction": "After download, extract and use 'Online Retail.xlsx'",
    },
    "uci_online_retail_ii": {
        "description": "UCI Online Retail II - extended dataset 2009-2011",
        "url": "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
        "filename": "online_retail_ii.zip",
        "target_dir": DATA_DIR / "uci_online_retail_ii",
        "instruction": "After download, extract and use 'online_retail_II.xlsx'",
    },
    "yelp_reviews": {
        "description": "Yelp Open Dataset - reviews for Module 4 (Brand Monitor) ABSA training",
        "url": "https://www.yelp.com/dataset/download",
        "filename": None,
        "target_dir": DATA_DIR / "yelp_reviews",
        "instruction": "Yelp dataset requires manual registration at https://www.yelp.com/dataset/download. Download yelp_dataset.tar and place in data/raw/yelp_reviews/",
        "manual": True,
    },
    "amazon_reviews": {
        "description": "Amazon Product Reviews - sentiment data for Module 4 ABSA training",
        "url": "https://huggingface.co/datasets/amazon_polarity/resolve/main/data/train-00000-of-00004.parquet",
        "filename": "amazon_reviews_train.parquet",
        "target_dir": DATA_DIR / "amazon_reviews",
        "instruction": "Amazon polarity review dataset for sentiment pre-training",
    },
    "criteo_attribution": {
        "description": "Criteo Attribution Dataset - for Module 5 (Attribution Engine) training",
        "url": "http://go.criteo.net/criteo-research-attribution-dataset.zip",
        "filename": "criteo_attribution.zip",
        "target_dir": DATA_DIR / "criteo_attribution",
        "instruction": "Criteo multi-touch attribution dataset with conversion and touchpoint data",
    },
}


def download_file(url: str, dest_path: Path, description: str) -> bool:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists():
        log.info("Already downloaded, skipping", file=dest_path.name)
        return True

    log.info("Downloading", description=description, url=url)
    try:
        def progress_hook(block_count, block_size, total_size):
            if total_size > 0:
                pct = min(100, block_count * block_size * 100 / total_size)
                print(f"\r  Progress: {pct:.1f}%", end="", flush=True)

        urllib.request.urlretrieve(url, dest_path, reporthook=progress_hook)
        print()
        log.info("Download complete", file=dest_path.name)
        return True
    except Exception as e:
        log.error("Download failed", url=url, error=str(e))
        return False


def extract_archive(archive_path: Path, target_dir: Path) -> bool:
    target_dir.mkdir(parents=True, exist_ok=True)
    log.info("Extracting", archive=archive_path.name, target=str(target_dir))
    try:
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path) as z:
                z.extractall(target_dir)
        elif archive_path.suffix in (".tar", ".gz", ".tgz"):
            with tarfile.open(archive_path) as t:
                t.extractall(target_dir)
        log.info("Extraction complete", target=str(target_dir))
        return True
    except Exception as e:
        log.error("Extraction failed", error=str(e))
        return False


def create_sample_dataset() -> None:
    """Create a synthetic sample dataset for testing when real data is unavailable."""
    import pandas as pd
    import numpy as np

    log.info("Creating synthetic sample dataset for testing")
    sample_dir = DATA_DIR / "synthetic_sample"
    sample_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)
    n_customers = 1000
    n_orders = 8000

    customer_ids = [f"CUST_{i:04d}" for i in range(n_customers)]
    customers_df = pd.DataFrame({
        "customer_id": customer_ids,
        "email": [f"customer_{i}@example.com" for i in range(n_customers)],
        "country": np.random.choice(["GB", "US", "DE", "FR", "AU"], n_customers, p=[0.4, 0.3, 0.1, 0.1, 0.1]),
        "signup_date": pd.date_range("2022-01-01", periods=n_customers, freq="8h"),
    })
    customers_df.to_csv(sample_dir / "customers.csv", index=False)

    order_customer_ids = np.random.choice(customer_ids, n_orders, p=None)
    orders_df = pd.DataFrame({
        "order_id": [f"ORD_{i:05d}" for i in range(n_orders)],
        "customer_id": order_customer_ids,
        "total": np.round(np.random.lognormal(4.5, 0.8, n_orders), 2),
        "discount": np.round(np.random.exponential(5, n_orders), 2),
        "items": np.random.randint(1, 8, n_orders),
        "category": np.random.choice(["Electronics", "Clothing", "Home", "Beauty", "Sports"], n_orders),
        "channel": np.random.choice(["web", "mobile", "email", "social"], n_orders, p=[0.5, 0.25, 0.15, 0.1]),
        "ordered_at": pd.date_range("2022-01-15", periods=n_orders, freq="30min"),
    })
    orders_df.to_csv(sample_dir / "orders.csv", index=False)

    event_types = [
        "email_sent", "email_opened", "email_clicked",
        "session_started", "page_viewed", "cart_added", "cart_abandoned",
    ]
    event_probabilities = [0.25, 0.12, 0.05, 0.20, 0.25, 0.07, 0.06]
    n_events = 25000
    events_df = pd.DataFrame({
        "event_id": [f"EVT_{i:06d}" for i in range(n_events)],
        "customer_id": np.random.choice(customer_ids, n_events),
        "event_type": np.random.choice(event_types, n_events, p=event_probabilities),
        "occurred_at": pd.date_range("2022-01-01", periods=n_events, freq="15min"),
        "source": np.random.choice(["klaviyo", "website", "shopify"], n_events),
    })
    events_df.to_csv(sample_dir / "events.csv", index=False)

    log.info(
        "Synthetic dataset created",
        customers=n_customers,
        orders=n_orders,
        events=n_events,
        path=str(sample_dir),
    )
    print(f"\nSynthetic dataset ready at: {sample_dir}")
    print(f"  customers.csv: {n_customers} rows")
    print(f"  orders.csv: {n_orders} rows")
    print(f"  events.csv: {n_events} rows")


def main() -> None:
    print("\nAIMA Dataset Downloader")
    print("=" * 50)

    for key, dataset in DATASETS.items():
        print(f"\n[{key}]")
        print(f"  {dataset['description']}")

        if dataset.get("manual"):
            print(f"  MANUAL DOWNLOAD REQUIRED: {dataset['instruction']}")
            dataset["target_dir"].mkdir(parents=True, exist_ok=True)
            continue

        filename = dataset["filename"]
        target_dir = dataset["target_dir"]
        dest_path = target_dir / filename

        success = download_file(dataset["url"], dest_path, dataset["description"])
        if success and filename and (filename.endswith(".zip") or filename.endswith(".tar")):
            extract_archive(dest_path, target_dir)

    print("\nCreating synthetic sample dataset for immediate testing...")
    create_sample_dataset()

    print("\nDataset preparation complete.")
    print("Next step: Run scripts/prepare_training_data.py to process raw data for model training.")


if __name__ == "__main__":
    main()
