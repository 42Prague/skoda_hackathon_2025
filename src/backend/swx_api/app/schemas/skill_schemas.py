"""
Skill Schemas
-------------
Pydantic schemas for skill analysis, forecasting, and role-fit requests/responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SkillAnalysisCreate(BaseModel):
    """Schema for creating a skill analysis."""
    
    employee_id: str = Field(..., description="Employee identifier")
    role_requirements: Optional[Dict[str, Any]] = Field(default=None, description="Optional role requirements for comparison")


class SkillAnalysisPublic(BaseModel):
    """Public schema for skill analysis."""
    
    id: UUID
    employee_id: str
    analysis_json: Dict[str, Any]
    recommendations_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SkillAnalysisRequest(BaseModel):
    """Request schema for skill analysis endpoint."""
    
    employee_id: str = Field(..., description="Employee identifier")
    role_requirements: Optional[Dict[str, Any]] = Field(default=None, description="Role requirements for comparison")


class SkillForecastingRequest(BaseModel):
    """Request schema for skill forecasting."""
    
    months: int = Field(6, ge=3, le=12, description="Forecast horizon in months (3, 6, or 12)")
    department: Optional[str] = Field(default=None, description="Optional department filter")


class RoleFitRequest(BaseModel):
    """Request schema for role-fit calculation."""
    
    employee_id: str = Field(..., description="Employee identifier")
    role_definition: Dict[str, Any] = Field(..., description="Role definition with mandatory/preferred skills")
    skill_importance: Optional[Dict[str, Any]] = Field(default=None, description="Optional skill importance weights")


class ScenarioSimulationRequest(BaseModel):
    """Request schema for scenario simulation."""
    
    scenario_type: str = Field(..., description="Type: 'employee_loss', 'training_completion', 'skill_mandatory'")
    scenario_params: Dict[str, Any] = Field(..., description="Scenario parameters")


class MentorRecommendationRequest(BaseModel):
    """Request schema for mentor recommendations."""
    
    employee_id: str = Field(..., description="Employee identifier")
    max_recommendations: int = Field(10, ge=1, le=50, description="Maximum number of recommendations")

