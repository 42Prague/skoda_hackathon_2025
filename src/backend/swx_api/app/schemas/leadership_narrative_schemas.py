"""
Leadership Narrative Schemas
----------------------------
Pydantic schemas for AI Leadership Narrative feature.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class LeadershipActionItem(BaseModel):
    """Leadership action recommendation."""

    action: str = Field(..., description="Action description")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority level")
    timeline: str = Field(..., description="Timeline for action (e.g., 'Q1 2025', '6 months')")
    impact: str = Field(..., description="Expected impact description")


class RiskSummaryItem(BaseModel):
    """Risk summary for succession pipeline."""

    pipeline_strength: int = Field(..., ge=0, le=100, description="Pipeline strength score (0-100)")
    key_risks: List[str] = Field(default_factory=list, description="List of key risk descriptions")
    vacancy_risk: int = Field(..., ge=0, le=100, description="Vacancy risk score (0-100)")


class SuccessorCandidateItem(BaseModel):
    """Successor candidate information."""

    employee_id: str = Field(..., description="Employee identifier")
    name: str = Field(..., description="Employee name")
    readiness_score: int = Field(..., ge=0, le=100, description="Readiness score (0-100)")
    strengths: List[str] = Field(default_factory=list, description="Key strengths")
    development_areas: List[str] = Field(default_factory=list, description="Areas for development")
    time_to_readiness: str = Field(..., description="Time to readiness (e.g., 'Ready now', '6 months')")


class LeadershipNarrativeResponse(BaseModel):
    """Response schema for leadership narrative."""

    narrative: str = Field(..., description="McKinsey-style narrative paragraphs")
    leadership_actions: List[LeadershipActionItem] = Field(
        default_factory=list, description="Recommended leadership actions"
    )
    risk_summary: RiskSummaryItem = Field(..., description="Risk summary")
    successor_candidates: List[SuccessorCandidateItem] = Field(
        default_factory=list, description="Top successor candidates"
    )
    ai_mode: str = Field(..., description="AI mode: 'featherless' or 'heuristic'")

