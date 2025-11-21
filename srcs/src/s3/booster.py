"""Productivity booster suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .models import UserProfile


@dataclass
class Booster:
    skill: str
    title: str
    description: str
    link: str | None = None


BOOSTER_LIBRARY = [
    Booster(
        skill="word_formatting",
        title="Auto TOC in Word",
        description="Use Styles + References > Table of Contents to auto-generate docs.",
        link="https://learn.microsoft.com/word",
    ),
    Booster(
        skill="excel_analytics",
        title="Copilot for variance analysis",
        description="Use Škoda Copilot template to summarize KPI deltas in seconds.",
        link=None,
    ),
]


def suggest_boosters(profile: UserProfile) -> List[Booster]:
    suggestions: List[Booster] = []
    for evidence in profile.evidences.values():
        if evidence.status == "verified":
            suggestions.extend(
                booster for booster in BOOSTER_LIBRARY if booster.skill == evidence.skill
            )
    return suggestions

