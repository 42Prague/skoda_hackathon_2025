"""
Recommendations Schemas
----------------------
Pydantic schemas for skill and role recommendations.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from swx_api.app.schemas.common_schemas import UnifiedScoreModel


class RecommendationsResponse(BaseModel):
    """Response schema for skill recommendations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommended_skills": [
                    {"skill": "Battery Systems", "priority": "high", "reason": "Complementary to current role"}
                ],
                "reasoning": "Focus on electrification depth for the upcoming platform launch.",
                "priority": ["high", "medium"],
                "unified_score": UnifiedScoreModel.model_config["json_schema_extra"]["example"],
                "ai_used": True,
                "ai_mode": "live",
            }
        }
    )

    recommended_skills: List[Dict[str, Any]]
    reasoning: str
    priority: List[str]
    unified_score: UnifiedScoreModel
    ai_used: bool
    ai_mode: str


class TrainingPathRequest(BaseModel):
    """Request schema for training path generation."""
    
    employee_id: str = Field(..., description="Employee identifier")
    target_skills: List[str] = Field(..., description="Target skills to acquire")


class NextRoleRequest(BaseModel):
    """Request schema for next role recommendations."""
    
    employee_id: str = Field(..., description="Employee identifier")
    available_roles: List[Dict[str, Any]] = Field(..., description="List of available roles")

