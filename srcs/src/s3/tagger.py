"""Tagging heuristics and hooks."""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict

from .config import settings

KEYWORD_TAGS = {
    "powerpoint": ("powerpoint_basics", "beginner", "presentation_creation"),
    "excel": ("excel_analytics", "intermediate", "reporting"),
    "word": ("word_formatting", "intermediate", "documentation"),
    "copilot": ("copilot_assistance", "advanced", "productivity"),
    "ai": ("ai_productivity", "intermediate", "automation"),
}


def tag_text(text: str) -> Dict[str, str]:
    """Assign lightweight skill tags to a chunk."""
    lowered = text.lower()
    found = [
        (skill, level, use_case)
        for keyword, (skill, level, use_case) in KEYWORD_TAGS.items()
        if keyword in lowered
    ]
    tags: Dict[str, str] = {}
    if found:
        freq = Counter(skill for skill, *_ in found)
        skill, count = freq.most_common(1)[0]
        level = next(level for s, level, _ in found if s == skill)
        use_case = next(use_case for s, _, use_case in found if s == skill)
        tags = {
            "skill": skill,
            "level": level,
            "use_case": use_case,
            "confidence": str(min(1.0, count / len(found) + 0.3)),
        }
    else:
        tags = {
            "skill": "general_productivity",
            "level": "baseline",
            "use_case": _guess_use_case(lowered),
            "confidence": str(settings.tagging.min_confidence),
        }
    return tags


def _guess_use_case(text: str) -> str:
    if re.search(r"report|analysis|excel", text):
        return "reporting"
    if re.search(r"slide|presentation|powerpoint", text):
        return "presentation_creation"
    if re.search(r"email|communication|word", text):
        return "communication"
    return "general"

