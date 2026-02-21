"""
Aspect-Based Sentiment Analysis Model - Module 4.
Fine-tuned DeBERTa model that scores 10 brand dimensions
from raw review/social media text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np
import structlog

log = structlog.get_logger()

BRAND_DIMENSIONS = [
    "product_quality",
    "customer_service",
    "pricing_value",
    "brand_trust",
    "innovation",
    "sustainability_ethics",
    "user_experience",
    "delivery_logistics",
    "brand_personality",
    "competitive_position",
]


@dataclass
class SentimentResult:
    text: str
    overall: float
    dimensions: dict[str, float]
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "overall": round(self.overall, 4),
            **{f"sentiment_{k}": round(v, 4) for k, v in self.dimensions.items()},
        }


class ABSAModel:
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        self.model_path = model_path
        self.device = device
        self._model = None
        self._tokenizer = None
        self.log = log.bind(component="ABSAModel")

    def load(self) -> None:
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            model_name = self.model_path or "microsoft/deberta-v3-base"
            self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(BRAND_DIMENSIONS),
            )
            self._model.to(self.device)
            self._model.eval()
            self.log.info("ABSA model loaded", model=model_name)
        except ImportError:
            self.log.warning("transformers not installed - using keyword-based fallback")

    def analyze(self, text: str, source: Optional[str] = None) -> SentimentResult:
        if self._model is not None:
            return self._neural_analyze(text, source)
        return self._keyword_analyze(text, source)

    def analyze_batch(self, texts: list[str], sources: Optional[list[str]] = None) -> list[SentimentResult]:
        sources = sources or [None] * len(texts)
        return [self.analyze(t, s) for t, s in zip(texts, sources)]

    def _neural_analyze(self, text: str, source: Optional[str]) -> SentimentResult:
        import torch
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        ).to(self.device)
        with torch.no_grad():
            outputs = self._model(**inputs)
            scores = torch.sigmoid(outputs.logits).squeeze(0).cpu().numpy()

        dimensions = {dim: float(score) for dim, score in zip(BRAND_DIMENSIONS, scores)}
        overall = float(np.mean(scores))
        return SentimentResult(text=text, overall=overall, dimensions=dimensions, source=source)

    def _keyword_analyze(self, text: str, source: Optional[str]) -> SentimentResult:
        text_lower = text.lower()

        positive_keywords = {
            "product_quality": ["amazing", "excellent", "great product", "love", "perfect", "high quality", "well made"],
            "customer_service": ["helpful", "responsive", "quick reply", "great support", "resolved", "fantastic team"],
            "pricing_value": ["worth it", "good value", "fair price", "affordable", "great deal", "reasonable"],
            "brand_trust": ["reliable", "trustworthy", "always delivers", "consistent", "dependable"],
            "innovation": ["innovative", "cutting edge", "new features", "ahead", "modern", "pioneering"],
            "sustainability_ethics": ["eco-friendly", "sustainable", "ethical", "green", "responsible"],
            "user_experience": ["easy to use", "intuitive", "smooth", "seamless", "clean design"],
            "delivery_logistics": ["fast delivery", "quick shipping", "arrived early", "well packaged"],
            "brand_personality": ["love the brand", "authentic", "relatable", "genuine", "fun"],
            "competitive_position": ["best in class", "better than", "leading", "top choice"],
        }
        negative_keywords = {
            "product_quality": ["poor quality", "broke", "defective", "cheap", "disappointing", "terrible"],
            "customer_service": ["rude", "unhelpful", "slow response", "ignored", "no support", "useless"],
            "pricing_value": ["expensive", "overpriced", "not worth", "too costly", "rip off"],
            "brand_trust": ["untrustworthy", "scam", "misleading", "false", "dishonest"],
            "innovation": ["outdated", "old fashioned", "behind", "no updates"],
            "sustainability_ethics": ["wasteful", "unethical", "harmful", "pollution"],
            "user_experience": ["confusing", "complicated", "hard to use", "buggy", "crashes"],
            "delivery_logistics": ["late", "delayed", "damaged", "wrong item", "lost"],
            "brand_personality": ["boring", "corporate", "fake", "impersonal"],
            "competitive_position": ["worse than", "inferior", "losing ground"],
        }

        dimensions = {}
        for dim in BRAND_DIMENSIONS:
            pos = sum(1 for kw in positive_keywords.get(dim, []) if kw in text_lower)
            neg = sum(1 for kw in negative_keywords.get(dim, []) if kw in text_lower)
            if pos + neg == 0:
                dimensions[dim] = 0.5
            else:
                dimensions[dim] = round(pos / (pos + neg), 4)

        overall = round(float(np.mean(list(dimensions.values()))), 4)
        return SentimentResult(text=text, overall=overall, dimensions=dimensions, source=source)
