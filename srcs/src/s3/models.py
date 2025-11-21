"""Core domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class ContentChunk:
    id: str
    source_path: str
    text: str
    tags: Dict[str, str]
    score: float = 0.0


@dataclass
class SkillEvidence:
    skill: str
    level: str
    status: str  # e.g. verified/inferred/gap
    last_verified: datetime | None = None
    notes: str | None = None


@dataclass
class UserProfile:
    user_id: str
    role: str
    evidences: Dict[str, SkillEvidence] = field(default_factory=dict)

    def holes(self) -> List[str]:
        return [skill for skill, ev in self.evidences.items() if ev.status == "gap"]


@dataclass
class Recommendation:
    user_id: str
    chunk_id: str
    reason: str
    score: float

