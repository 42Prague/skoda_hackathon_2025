"""
Dashboard Schemas
-----------------
Pydantic schemas for dashboard responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from swx_api.app.schemas.common_schemas import UnifiedScoreModel

UNIFIED_SCORE_EXAMPLE = {
    "overall_score": 82,
    "skill_scores": {"Battery Systems": 78, "Autonomous Software": 85},
    "gap_scores": {"Cloud Fleet": 65},
    "role_fit_score": 80,
    "next_role_readiness": 76,
    "risk_score": 32,
}


class DashboardOverviewResponse(BaseModel):
    """Response schema for dashboard overview."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_employees": 145,
                "total_departments": 7,
                "departments": [
                    {"name": "Powertrain Engineering", "employee_count": 32, "total_skills": 210}
                ],
                "global_analytics": {"total_skills": 120, "skill_frequency": {"Battery Systems": 22}},
                "unified_score": UNIFIED_SCORE_EXAMPLE,
            }
        }
    )

    total_employees: int
    total_departments: int
    departments: List[Dict[str, Any]]
    global_analytics: Dict[str, Any]
    unified_score: UnifiedScoreModel


class SkillMapResponse(BaseModel):
    """Response schema for skill map."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ontology": {
                    "skills": ["Battery Systems", "Autonomous Software"],
                    "clusters": [],
                    "normalized_mapping": {"Battery": "Battery Systems"},
                    "department_skill_map": {"Powertrain Engineering": ["Battery Systems"]},
                },
                "employee_distribution": {"Battery Systems": 18, "Autonomous Software": 12},
                "unified_score": UNIFIED_SCORE_EXAMPLE,
            }
        }
    )

    ontology: Dict[str, Any]
    employee_distribution: Dict[str, int]
    unified_score: UnifiedScoreModel


class SkillHeatmapResponse(BaseModel):
    """Response schema for skill heatmap."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "heatmap_data": {"Powertrain Engineering": 14, "Autonomous Systems": 9},
                "unified_score": UNIFIED_SCORE_EXAMPLE,
            }
        }
    )

    heatmap_data: Dict[str, Any]
    unified_score: UnifiedScoreModel


class SkillTrendsResponse(BaseModel):
    """Response schema for skill trends."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trends": {"period_months": 6, "top_growing_skills": ["Digital Twins", "Cybersecurity"]},
                "unified_score": UNIFIED_SCORE_EXAMPLE,
            }
        }
    )

    trends: Dict[str, Any]
    unified_score: UnifiedScoreModel


class InstantOverviewResponse(BaseModel):
    """Response schema for instant overview."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_employees": 145,
                "total_departments": 7,
                "global_skill_distribution": {"Battery Systems": 22, "Autonomous Software": 18},
                "top_skill_shortages": ["Cloud Fleet", "Safety Assurance"],
                "top_strong_skills": ["Battery Systems", "Chassis Design"],
                "department_risk_summary": {"Powertrain Engineering": {"skill_concentration_risk": 25.0}},
                "skill_heatmap_matrix": {"Powertrain Engineering": {"Battery Systems": 12}},
                "ontology_overview": {"skill_count": 58, "cluster_count": 12, "departments": 7},
                "next_role_readiness": {
                    "average_skills_per_employee": 5.4,
                    "readiness_score": 78,
                    "recommended_focus": "Expand leadership pipeline",
                },
                "dataset_metadata": {"dataset_id": "demo", "row_count": 145, "last_ingested_at": "2025-11-17T09:00:00Z"},
                "unified_score": UNIFIED_SCORE_EXAMPLE,
            }
        }
    )

    total_employees: int
    total_departments: int
    global_skill_distribution: Dict[str, int]
    top_skill_shortages: List[str]
    top_strong_skills: List[str]
    department_risk_summary: Dict[str, Dict[str, float]]
    skill_heatmap_matrix: Dict[str, Dict[str, int]]
    ontology_overview: Dict[str, Any]
    next_role_readiness: Dict[str, Any]
    dataset_metadata: Optional[Dict[str, Any]] = None
    unified_score: UnifiedScoreModel

