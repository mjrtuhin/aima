"""
Dynamic Clustering Engine - Module 1.

Takes behavioral fingerprints from the Temporal Behavioral Transformer and
discovers natural customer segments. Uses UMAP for dimensionality reduction
followed by HDBSCAN for density-based clustering, then names segments
automatically using their behavioral characteristics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class Segment:
    cluster_id: int
    name: str
    description: str
    size: int
    avg_health_score: float
    avg_monetary_value: float
    avg_recency_days: float
    avg_frequency: float
    avg_email_open_rate: float
    recommended_strategy: str
    characteristics: dict = field(default_factory=dict)
    customer_ids: list[str] = field(default_factory=list)


SEGMENT_NAMING_RULES = [
    {
        "name": "Champions",
        "conditions": lambda s: s["avg_recency_days"] < 30 and s["avg_frequency"] >= 5 and s["avg_monetary_value"] > 500,
        "description": "Bought recently, buy often, and spend the most.",
        "strategy": "Reward them. They can become brand ambassadors. Early access to new products.",
    },
    {
        "name": "Loyal Customers",
        "conditions": lambda s: s["avg_frequency"] >= 4 and s["avg_monetary_value"] > 200,
        "description": "Buy regularly and spend well. Strong brand affinity.",
        "strategy": "Offer membership or loyalty program. Upsell higher-value products.",
    },
    {
        "name": "Potential Loyalists",
        "conditions": lambda s: s["avg_recency_days"] < 60 and 2 <= s["avg_frequency"] < 4,
        "description": "Recent customers with growing purchase frequency.",
        "strategy": "Offer loyalty rewards. Educate on full product range.",
    },
    {
        "name": "New Customers",
        "conditions": lambda s: s["avg_frequency"] == 1 and s["avg_recency_days"] < 30,
        "description": "Just made their first purchase.",
        "strategy": "Welcome sequence. Introduce brand story. Drive second purchase.",
    },
    {
        "name": "Promising",
        "conditions": lambda s: s["avg_recency_days"] < 90 and s["avg_frequency"] < 3 and s["avg_monetary_value"] < 200,
        "description": "Recent shoppers with potential to grow.",
        "strategy": "Build relationship. Show product benefits. Gentle upsell.",
    },
    {
        "name": "Need Attention",
        "conditions": lambda s: 90 <= s["avg_recency_days"] < 180 and s["avg_frequency"] >= 2,
        "description": "Above-average customers who haven't purchased recently.",
        "strategy": "Reactivate with personalized offer. Remind them of value.",
    },
    {
        "name": "About to Sleep",
        "conditions": lambda s: 60 <= s["avg_recency_days"] < 90 and s["avg_frequency"] < 3,
        "description": "Below-average recency and frequency - at risk of going dormant.",
        "strategy": "Share valuable resources. Recommend products. Small incentive.",
    },
    {
        "name": "At Risk",
        "conditions": lambda s: 180 <= s["avg_recency_days"] < 365 and s["avg_frequency"] >= 2,
        "description": "Spent well and bought often, but haven't returned in a long time.",
        "strategy": "Personalized re-engagement. 'We miss you' campaign. Time-limited offer.",
    },
    {
        "name": "Can't Lose Them",
        "conditions": lambda s: s["avg_recency_days"] >= 180 and s["avg_monetary_value"] > 500,
        "description": "High-value customers who haven't purchased in a very long time.",
        "strategy": "Win back with strong offer. Personal outreach. Survey why they left.",
    },
    {
        "name": "Hibernating",
        "conditions": lambda s: s["avg_recency_days"] >= 180 and s["avg_monetary_value"] <= 200,
        "description": "Low recency, low spend. Mostly dormant.",
        "strategy": "Reactivation email. Low-value incentive to test response.",
    },
    {
        "name": "Lost",
        "conditions": lambda s: s["avg_recency_days"] >= 365,
        "description": "Bought long ago and haven't returned.",
        "strategy": "Only contact if cost is very low. Sunset or archive segment.",
    },
]


def name_segment(segment_stats: dict) -> tuple[str, str, str]:
    for rule in SEGMENT_NAMING_RULES:
        try:
            if rule["conditions"](segment_stats):
                return rule["name"], rule["description"], rule["strategy"]
        except Exception:
            continue
    return "General Customers", "Customers not fitting specific behavioral pattern.", "Standard marketing approach."


class DynamicClusteringEngine:
    def __init__(
        self,
        n_components: int = 10,
        min_cluster_size: int = 10,
        min_samples: int = 5,
        umap_n_neighbors: int = 15,
        use_kmeans_fallback: bool = True,
    ):
        self.n_components = n_components
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.umap_n_neighbors = umap_n_neighbors
        self.use_kmeans_fallback = use_kmeans_fallback
        self.umap_model = None
        self.cluster_model = None
        self.log = log.bind(component="DynamicClusteringEngine")

    def fit_predict(
        self,
        fingerprints: np.ndarray,
        customer_ids: list[str],
        feature_vectors: Optional[list[dict]] = None,
    ) -> list[Segment]:
        self.log.info("Starting clustering", n_customers=len(customer_ids))

        reduced = self._reduce_dimensions(fingerprints)

        labels = self._cluster(reduced)

        unique_labels = set(labels) - {-1}
        n_clusters = len(unique_labels)

        if n_clusters < 2 and self.use_kmeans_fallback:
            self.log.warning("HDBSCAN found too few clusters, falling back to K-Means", n_clusters=n_clusters)
            labels = self._kmeans_fallback(reduced, fingerprints)
            unique_labels = set(labels)

        self.log.info("Clusters found", n_clusters=len(unique_labels))

        segments = []
        for cluster_id in sorted(unique_labels):
            mask = labels == cluster_id
            cluster_customer_ids = [cid for cid, m in zip(customer_ids, mask) if m]

            stats = self._compute_cluster_stats(
                cluster_id=cluster_id,
                mask=mask,
                feature_vectors=feature_vectors,
                customer_ids=customer_ids,
            )

            name, description, strategy = name_segment(stats)

            segment = Segment(
                cluster_id=int(cluster_id),
                name=name,
                description=description,
                size=int(mask.sum()),
                avg_health_score=stats.get("avg_health_score", 0.0),
                avg_monetary_value=stats.get("avg_monetary_value", 0.0),
                avg_recency_days=stats.get("avg_recency_days", 0.0),
                avg_frequency=stats.get("avg_frequency", 0.0),
                avg_email_open_rate=stats.get("avg_email_open_rate", 0.0),
                recommended_strategy=strategy,
                characteristics=stats,
                customer_ids=cluster_customer_ids,
            )
            segments.append(segment)

        self.log.info("Segmentation complete", segments=[s.name for s in segments])
        return segments

    def _reduce_dimensions(self, fingerprints: np.ndarray) -> np.ndarray:
        try:
            import umap
            self.umap_model = umap.UMAP(
                n_components=min(self.n_components, fingerprints.shape[1]),
                n_neighbors=self.umap_n_neighbors,
                min_dist=0.0,
                metric="cosine",
                random_state=42,
            )
            return self.umap_model.fit_transform(fingerprints)
        except ImportError:
            self.log.warning("umap-learn not available, using PCA")
            from sklearn.decomposition import PCA
            pca = PCA(n_components=min(self.n_components, fingerprints.shape[1]))
            return pca.fit_transform(fingerprints)

    def _cluster(self, reduced: np.ndarray) -> np.ndarray:
        try:
            import hdbscan
            self.cluster_model = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric="euclidean",
                cluster_selection_method="eom",
            )
            return self.cluster_model.fit_predict(reduced)
        except ImportError:
            self.log.warning("hdbscan not available, using K-Means")
            return self._kmeans_fallback(reduced, reduced)

    def _kmeans_fallback(self, reduced: np.ndarray, original: np.ndarray, k: int = 8) -> np.ndarray:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        best_k = k
        best_score = -1.0

        for n_k in range(3, min(k + 1, len(reduced) // 5 + 1)):
            km = KMeans(n_clusters=n_k, random_state=42, n_init=10)
            labels = km.fit_predict(reduced)
            if len(set(labels)) > 1:
                score = silhouette_score(reduced, labels)
                if score > best_score:
                    best_score = score
                    best_k = n_k

        km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        return km.fit_predict(reduced)

    def _compute_cluster_stats(
        self,
        cluster_id: int,
        mask: np.ndarray,
        feature_vectors: Optional[list[dict]],
        customer_ids: list[str],
    ) -> dict:
        stats = {
            "cluster_id": cluster_id,
            "size": int(mask.sum()),
            "avg_recency_days": 0.0,
            "avg_frequency": 0.0,
            "avg_monetary_value": 0.0,
            "avg_health_score": 0.0,
            "avg_email_open_rate": 0.0,
        }

        if feature_vectors:
            cluster_fvs = [fv for fv, m in zip(feature_vectors, mask) if m]
            if cluster_fvs:
                for key in ["recency_days", "frequency", "monetary_value", "customer_health_score", "email_open_rate"]:
                    values = [fv.get(key) for fv in cluster_fvs if fv.get(key) is not None]
                    if values:
                        stat_key = f"avg_{key}" if key != "customer_health_score" else "avg_health_score"
                        stats[stat_key] = float(np.mean(values))

        return stats
