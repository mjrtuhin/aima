"""
Brand Voice Encoder - Module 3.
Learns a brand's unique voice from existing content samples.
Produces a Brand Voice Profile used to constrain all content generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import structlog

log = structlog.get_logger()


@dataclass
class BrandVoiceProfile:
    brand_id: str
    formality_score: float = 0.5
    warmth_score: float = 0.5
    urgency_score: float = 0.5
    complexity_score: float = 0.5
    humor_score: float = 0.1
    avg_sentence_length: float = 15.0
    preferred_vocab: list[str] = field(default_factory=list)
    avoided_vocab: list[str] = field(default_factory=list)
    tone_keywords: list[str] = field(default_factory=list)
    sample_count: int = 0

    def to_prompt_constraint(self) -> str:
        tone_desc = []
        if self.formality_score > 0.6:
            tone_desc.append("professional and formal")
        elif self.formality_score < 0.4:
            tone_desc.append("casual and conversational")
        if self.warmth_score > 0.6:
            tone_desc.append("warm and friendly")
        if self.urgency_score > 0.6:
            tone_desc.append("urgent and action-oriented")
        if self.humor_score > 0.5:
            tone_desc.append("light and humorous")

        constraint = f"Write in a {', '.join(tone_desc) if tone_desc else 'neutral'} tone. "
        if self.avg_sentence_length < 12:
            constraint += "Use short, punchy sentences. "
        elif self.avg_sentence_length > 20:
            constraint += "Use longer, more detailed sentences. "
        if self.preferred_vocab:
            constraint += f"Preferred vocabulary: {', '.join(self.preferred_vocab[:10])}. "
        if self.avoided_vocab:
            constraint += f"Avoid these words: {', '.join(self.avoided_vocab[:10])}. "
        return constraint


class BrandVoiceEncoder:
    def __init__(self):
        self.log = log.bind(component="BrandVoiceEncoder")

    def learn_from_samples(self, content_samples: list[str], brand_id: str) -> BrandVoiceProfile:
        self.log.info("Learning brand voice", brand_id=brand_id, n_samples=len(content_samples))

        if not content_samples:
            return BrandVoiceProfile(brand_id=brand_id)

        profile = BrandVoiceProfile(brand_id=brand_id, sample_count=len(content_samples))
        profile.avg_sentence_length = self._compute_avg_sentence_length(content_samples)
        profile.formality_score = self._score_formality(content_samples)
        profile.urgency_score = self._score_urgency(content_samples)
        profile.warmth_score = self._score_warmth(content_samples)
        profile.preferred_vocab = self._extract_distinctive_vocab(content_samples)

        self.log.info("Brand voice learned", brand_id=brand_id, formality=profile.formality_score)
        return profile

    def _compute_avg_sentence_length(self, samples: list[str]) -> float:
        lengths = []
        for text in samples:
            sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
            for s in sentences:
                lengths.append(len(s.split()))
        return float(np.mean(lengths)) if lengths else 15.0

    def _score_formality(self, samples: list[str]) -> float:
        informal_signals = ["hey", "!", "gonna", "wanna", "ya", "lol", "btw", "omg"]
        formal_signals = ["please", "however", "therefore", "regarding", "sincerely", "we are pleased"]
        text_lower = " ".join(samples).lower()
        informal_count = sum(text_lower.count(s) for s in informal_signals)
        formal_count = sum(text_lower.count(s) for s in formal_signals)
        total = informal_count + formal_count
        if total == 0:
            return 0.5
        return round(formal_count / total, 3)

    def _score_urgency(self, samples: list[str]) -> float:
        urgency_signals = ["now", "today", "limited", "last chance", "hurry", "expires", "deadline", "only"]
        text_lower = " ".join(samples).lower()
        count = sum(text_lower.count(s) for s in urgency_signals)
        total_words = len(text_lower.split())
        return round(min(count / max(total_words / 100, 1), 1.0), 3)

    def _score_warmth(self, samples: list[str]) -> float:
        warmth_signals = ["you", "your", "love", "thank", "appreciate", "excited", "happy", "care", "together"]
        text_lower = " ".join(samples).lower()
        count = sum(text_lower.count(s) for s in warmth_signals)
        total_words = len(text_lower.split())
        return round(min(count / max(total_words / 50, 1), 1.0), 3)

    def _extract_distinctive_vocab(self, samples: list[str], top_n: int = 20) -> list[str]:
        from collections import Counter
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were", "be", "been", "have", "has", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "it", "its", "we", "our", "you", "your", "they", "their"}
        all_words = []
        for text in samples:
            words = [w.lower().strip(".,!?;:'\"") for w in text.split()]
            all_words.extend([w for w in words if len(w) > 3 and w not in stop_words])
        counter = Counter(all_words)
        return [word for word, _ in counter.most_common(top_n)]
