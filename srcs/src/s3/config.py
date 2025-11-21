"""Configuration primitives for S³."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("S3_DATA_DIR", PROJECT_ROOT / "data"))
ARTIFACT_DIR = Path(os.getenv("S3_ARTIFACT_DIR", PROJECT_ROOT / "artifacts"))


class ChunkingConfig(BaseModel):
    target_tokens: int = Field(
        default=120,
        description="Approximate number of tokens per content chunk.",
    )
    overlap_tokens: int = Field(
        default=30, description="Overlap between consecutive chunks to preserve context."
    )


class TaggingConfig(BaseModel):
    min_confidence: float = Field(
        default=0.5, description="Confidence threshold for auto-generated tags."
    )


class EmbeddingConfig(BaseModel):
    max_features: int = Field(
        default=4096, description="Max vocabulary size for TF-IDF vectorizer."
    )


class RecommendationConfig(BaseModel):
    top_k: int = Field(default=5, description="How many chunks to return per hole.")


class Settings(BaseModel):
    chunking: ChunkingConfig = ChunkingConfig()
    tagging: TaggingConfig = TaggingConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    recommendation: RecommendationConfig = RecommendationConfig()
    data_dir: Path = DATA_DIR
    artifact_dir: Path = ARTIFACT_DIR


settings = Settings()


def ensure_artifacts() -> None:
    """Create artifact directories if needed."""
    settings.artifact_dir.mkdir(parents=True, exist_ok=True)
    (settings.artifact_dir / "vector_store").mkdir(parents=True, exist_ok=True)

