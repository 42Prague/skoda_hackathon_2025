"""
Career Coach Schemas
--------------------
Pydantic schemas for AI Career Coach Chat feature.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class CareerChatRequest(BaseModel):
    """Request schema for career coaching chat."""

    employee_id: Optional[str] = Field(
        default=None, description="Employee identifier (optional)"
    )
    user_message: str = Field(..., description="User's message or question")
    skills: Optional[List[str]] = Field(
        default=None, description="List of employee skills (optional if employee_id provided)"
    )
    career_goals: Optional[str] = Field(
        default=None, description="Employee career goals or aspirations"
    )
    department: Optional[str] = Field(
        default=None, description="Employee department (optional if employee_id provided)"
    )


class CareerChatSummary(BaseModel):
    """Summary section of career chat response."""

    next_role: str = Field(..., description="Proposed next role")
    readiness_score: int = Field(..., ge=0, le=100, description="Readiness score (0-100)")
    time_to_readiness_months: int = Field(
        ..., ge=0, description="Estimated months to readiness"
    )
    risk_score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    recommended_skills: List[str] = Field(
        default_factory=list, description="Recommended skills to develop"
    )
    recommended_training: List[str] = Field(
        default_factory=list, description="Recommended training paths"
    )


class CareerChatResponse(BaseModel):
    """Response schema for career coaching chat."""

    assistant: str = Field(..., description="AI assistant's conversational response")
    summary: CareerChatSummary = Field(..., description="Structured summary")
    ai_mode: str = Field(
        ..., description="AI mode: 'featherless' or 'heuristic'"
    )

