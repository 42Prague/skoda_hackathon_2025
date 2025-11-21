"""Lightweight vector store backed by scikit-learn."""

from __future__ import annotations

import json
from typing import List, Sequence
from sklearn.neighbors import NearestNeighbors

from .config import ensure_artifacts, settings
from .embedder import Embedder
from .models import ContentChunk


class VectorStore:
    def __init__(self, embedder: Embedder | None = None):
        self.embedder = embedder or Embedder.create()
        self.nn = NearestNeighbors(metric="cosine")
        self.matrix = None
        self.chunks: List[ContentChunk] = []

    def fit(self, chunks: Sequence[ContentChunk]) -> None:
        self.chunks = list(chunks)
        texts = [chunk.text for chunk in chunks]
        self.matrix = self.embedder.fit_transform(texts)
        self.nn.fit(self.matrix)

    def save(self) -> None:
        ensure_artifacts()
        store_dir = settings.artifact_dir / "vector_store"
        store_dir.mkdir(parents=True, exist_ok=True)
        # save vectorizer vocabulary
        vocab_path = store_dir / "vocab.json"
        vocab = {
            key: int(value)
            for key, value in self.embedder.vectorizer.vocabulary_.items()
        }
        vocab_path.write_text(json.dumps(vocab), encoding="utf-8")
        # save chunks metadata
        meta = [
            {
                "id": chunk.id,
                "source_path": chunk.source_path,
                "tags": chunk.tags,
                "text": chunk.text,
            }
            for chunk in self.chunks
        ]
        (store_dir / "chunks.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

    def load(self) -> None:
        store_dir = settings.artifact_dir / "vector_store"
        vocab = json.loads((store_dir / "vocab.json").read_text(encoding="utf-8"))
        self.embedder.vectorizer.vocabulary_ = vocab
        self.embedder.vectorizer._validate_vocabulary()
        meta = json.loads((store_dir / "chunks.json").read_text(encoding="utf-8"))
        self.chunks = [
            ContentChunk(
                id=item["id"],
                source_path=item["source_path"],
                text=item.get("text", ""),
                tags=item["tags"],
            )
            for item in meta
        ]
        texts = [chunk.text for chunk in self.chunks]
        self.matrix = self.embedder.fit_transform(texts)
        self.nn.fit(self.matrix)

    def search(self, query: str, top_k: int = 5) -> List[ContentChunk]:
        vec = self.embedder.transform([query])
        distances, indices = self.nn.kneighbors(vec, n_neighbors=top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            chunk = self.chunks[idx]
            chunk.score = 1 - dist
            results.append(chunk)
        return results

