"""
Common schemas shared across the Skill Coach MVP.
"""

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class UnifiedScoreModel(BaseModel):
    """Standard scoring envelope returned by analytics-endpoints with AI-driven scoring."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_score": 82,
                "skill_scores": {"Battery Systems": 78, "Autonomous Software": 85},
                "gap_scores": {"Cloud Fleet": 65, "ai_missing_skills": 15},
                "role_fit_score": 80,
                "next_role_readiness": 76,
                "risk_score": 32,
                "ai_gap_score": 78,
                "ai_readiness": 80,
                "ai_risk_signal": 22,
                "ai_skill_recommendations_count": 4,
                "ai_mode": "featherless",
            }
        }
    )

    overall_score: int = Field(..., ge=0, le=100)
    skill_scores: Dict[str, int]
    gap_scores: Dict[str, int]
    role_fit_score: int = Field(..., ge=0, le=100)
    next_role_readiness: int = Field(..., ge=0, le=100)
    risk_score: int = Field(..., ge=0, le=100)
    ai_gap_score: int | None = Field(default=None, ge=0, le=100)
    ai_readiness: int | None = Field(default=None, ge=0, le=100)
    ai_risk_signal: int | None = Field(default=None, ge=0, le=100)
    ai_skill_recommendations_count: int | None = Field(default=None, ge=0)
    ai_mode: str | None = Field(default=None, description="AI mode: 'featherless' | 'heuristic'")


class ErrorResponse(BaseModel):
    """Shared error response payload."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Unauthorized",
                "detail": "Invalid bearer token",
                "details": {"header": "Authorization"},
            }
        }
    )

    error: str
    detail: str
    details: Dict[str, str] | None = None

