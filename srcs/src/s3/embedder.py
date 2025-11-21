"""Embedding utilities using TF-IDF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer

from .config import settings


@dataclass
class Embedder:
    vectorizer: TfidfVectorizer

    @classmethod
    def create(cls) -> "Embedder":
        vectorizer = TfidfVectorizer(
            max_features=settings.embedding.max_features,
            ngram_range=(1, 2),
            stop_words="english",
        )
        return cls(vectorizer)

    def fit_transform(self, texts: List[str]):
        return self.vectorizer.fit_transform(texts)

    def transform(self, texts: List[str]):
        return self.vectorizer.transform(texts)

