"""Swiss-cheese user profile utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from .models import SkillEvidence, UserProfile


def mock_profile(user_id: str) -> UserProfile:
    """Generate a demo profile with intentional gaps."""
    evidences: Dict[str, SkillEvidence] = {
        "excel_analytics": SkillEvidence(
            skill="excel_analytics",
            level="advanced",
            status="verified",
            last_verified=datetime(2024, 11, 15),
        ),
        "word_formatting": SkillEvidence(
            skill="word_formatting",
            level="advanced",
            status="verified",
            last_verified=datetime(2024, 10, 4),
        ),
        "powerpoint_basics": SkillEvidence(
            skill="powerpoint_basics",
            level="beginner",
            status="gap",
            notes="Needs templates + design patterns",
        ),
        "copilot_assistance": SkillEvidence(
            skill="copilot_assistance",
            level="intermediate",
            status="gap",
            notes="Hasn't adopted prompt packs",
        ),
    }
    return UserProfile(user_id=user_id, role="Project Manager", evidences=evidences)


def fill_hole(profile: UserProfile, skill: str) -> None:
    evidence = profile.evidences.get(skill)
    if evidence:
        evidence.status = "verified"
        evidence.last_verified = datetime.utcnow()
    else:
        profile.evidences[skill] = SkillEvidence(
            skill=skill,
            level="baseline",
            status="verified",
            last_verified=datetime.utcnow(),
        )

