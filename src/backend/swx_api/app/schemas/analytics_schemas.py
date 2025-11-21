"""
Advanced Analytics Schemas
--------------------------
Pydantic models for succession radar and AI narrative endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from swx_api.app.schemas.common_schemas import UnifiedScoreModel


class SuccessionPipelineSummary(BaseModel):
    """Pipeline readiness summary."""

    ready_now: int
    ready_soon: int
    developing: int
    narrative: str
    risk_outlook: Literal["low", "medium", "high"]


class SuccessionCandidate(BaseModel):
    """Represents a single employee in the succession radar."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_id": "EMP-001",
                "name": "Ava Novak",
                "department": "Battery Systems",
                "readiness_score": 82,
                "next_role_readiness": 86,
                "risk_score": 24,
                "skill_strengths": ["Battery Systems", "Thermal Modeling", "Program Leadership"],
                "skill_gaps": ["Cloud Telemetry"],
                "unified_score": UnifiedScoreModel.model_config["json_schema_extra"]["example"],
            }
        }
    )

    employee_id: str
    name: str
    department: str
    readiness_score: int = Field(..., ge=0, le=100)
    next_role_readiness: int = Field(..., ge=0, le=100)
    risk_score: int = Field(..., ge=0, le=100)
    skill_strengths: List[str]
    skill_gaps: List[str]
    unified_score: UnifiedScoreModel
    metadata: Optional[Dict[str, str]] = None
    ai_metadata: Optional[Dict[str, Any]] = None


class SuccessionRadarResponse(BaseModel):
    """Response schema for the succession radar feature."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "department": "Battery Systems",
                "generated_at": "2025-11-17T10:00:00Z",
                "candidate_count": 6,
                "pipeline_summary": {
                    "ready_now": 2,
                    "ready_soon": 3,
                    "developing": 1,
                    "narrative": "2 leaders can step in today, pipeline stable.",
                    "risk_outlook": "low",
                },
                "unified_score": UnifiedScoreModel.model_config["json_schema_extra"]["example"],
                "candidates": [
                    SuccessionCandidate.model_config["json_schema_extra"]["example"]  # type: ignore[index]
                ],
            }
        }
    )

    department: str
    generated_at: str
    candidate_count: int
    pipeline_summary: SuccessionPipelineSummary
    unified_score: UnifiedScoreModel
    candidates: List[SuccessionCandidate]


class DepartmentNarrativeResponse(BaseModel):
    """Template-based AI narrative summarising department health."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "department": "Battery Systems",
                "risk_level": "medium",
                "risk_score": 48,
                "narrative": "Battery Systems demonstrates strong competency in Battery Systems, Thermal Modeling while needing hires in Cloud Telemetry.",
                "strengths": ["Battery Systems", "Thermal Modeling"],
                "shortages": ["Cloud Telemetry"],
                "insights": ["Strength in thermal modeling lifts readiness"],
                "risks": ["medium risk at 48/100"],
                "numeric_references": ["risk_score=48", "readiness=78"],
                "readiness_summary": "Readiness holds at 78/100 with a stable promotion queue.",
                "succession_summary": "2 ready-now leaders, 3 developing within 6 months.",
                "generated_at": "2025-11-17T10:05:00Z",
                "unified_score": UnifiedScoreModel.model_config["json_schema_extra"]["example"],
                "ai_mode": "live",
                "ai_provider": "featherless",
                "ai_used": True,
            }
        }
    )

    department: str
    risk_level: Literal["low", "medium", "high"]
    risk_score: int = Field(..., ge=0, le=100)
    narrative: str
    strengths: List[str]
    shortages: List[str]
    insights: List[str]
    risks: List[str]
    numeric_references: List[str]
    readiness_summary: str
    succession_summary: str
    generated_at: str
    unified_score: UnifiedScoreModel
    ai_mode: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_used: Optional[bool] = None
    error: Optional[str] = None


