"""Unit tests for data models."""

import pytest
from pydantic import ValidationError

from src.models import (
    ExtractedSkill,
    SkillCategory,
    SkillLevel,
    NormalizedSkill,
    Job,
    ValidatedSkill,
)


def test_extracted_skill_valid():
    """Test creating a valid ExtractedSkill."""
    skill = ExtractedSkill(
        name="Python",
        category=SkillCategory.TECHNICAL,
        confidence=0.95,
        required=True,
        level=SkillLevel.MID,
    )

    assert skill.name == "Python"
    assert skill.category == SkillCategory.TECHNICAL
    assert skill.confidence == 0.95
    assert skill.required is True
    assert skill.level == SkillLevel.MID


def test_extracted_skill_invalid_confidence():
    """Test that invalid confidence scores raise errors."""
    with pytest.raises(ValidationError):
        ExtractedSkill(
            name="Python",
            category=SkillCategory.TECHNICAL,
            confidence=1.5,  # Invalid: > 1.0
            required=True,
        )


def test_extracted_skill_name_strip():
    """Test that skill names are stripped of whitespace."""
    skill = ExtractedSkill(
        name="  Python  ",
        category=SkillCategory.TECHNICAL,
        confidence=0.95,
    )

    assert skill.name == "Python"


def test_normalized_skill():
    """Test creating a NormalizedSkill."""
    skill = NormalizedSkill(
        canonical_name="Python",
        original_name="python",
        category=SkillCategory.TECHNICAL,
        aliases=["Py", "Python3"],
        embedding=[0.1, 0.2, 0.3],
        cluster_id=5,
    )

    assert skill.canonical_name == "Python"
    assert len(skill.aliases) == 2
    assert skill.cluster_id == 5


def test_job_model():
    """Test creating a Job model."""
    job = Job(
        id="123",
        title="Python Developer",
        description="Looking for a Python developer...",
        company="Tech Corp",
        location="San Francisco, CA",
    )

    assert job.id == "123"
    assert job.title == "Python Developer"
    assert job.company == "Tech Corp"


def test_validated_skill():
    """Test creating a ValidatedSkill."""
    skill = ValidatedSkill(
        original="ReactJS",
        canonical="React",
        match_type="alias",
        confidence=1.0,
    )

    assert skill.original == "ReactJS"
    assert skill.canonical == "React"
    assert skill.match_type == "alias"
