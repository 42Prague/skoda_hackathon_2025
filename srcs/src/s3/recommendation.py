"""Recommendation engine logic."""

from __future__ import annotations

from typing import List

from .config import settings
from .models import ContentChunk, Recommendation, UserProfile
from .vector_store import VectorStore


def recommend(profile: UserProfile, vector_store: VectorStore) -> List[Recommendation]:
    recs: List[Recommendation] = []
    holes = profile.holes()
    if not holes:
        return recs
    for hole in holes:
        query = f"{hole} learning snippet"
        matches = vector_store.search(query, top_k=settings.recommendation.top_k)
        for chunk in matches:
            recs.append(
                Recommendation(
                    user_id=profile.user_id,
                    chunk_id=chunk.id,
                    reason=f"Fill {hole}",
                    score=chunk.score,
                )
            )
    recs.sort(key=lambda r: r.score, reverse=True)
    return recs[: settings.recommendation.top_k * len(holes)]

