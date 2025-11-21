"""
Hackathon Routes
----------------
5 winning feature endpoints for hackathon demo.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query

from swx_api.app.services.team_capability_service import TeamCapabilityService
from swx_api.app.services.risk_radar_service import RiskRadarService
from swx_api.app.services.promotion_readiness_service import PromotionReadinessService
from swx_api.app.services.career_path_service import CareerPathService
from swx_api.app.services.forecast_service import ForecastService
from swx_api.app.utils.dependencies import EmployeeRepoDep
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("hackathon_routes")

# Set empty prefix - routes define full paths. Router.py adds /api automatically.
# Final paths will be: /api/team/{team_id}/capability (NOT /api/hackathon_routes/team/...)
router = APIRouter(prefix="")

# Initialize services
team_capability_service = TeamCapabilityService()
risk_radar_service = RiskRadarService()
promotion_readiness_service = PromotionReadinessService()
career_path_service = CareerPathService()
forecast_service = ForecastService()


@router.get("/team/{team_id}/capability")
async def get_team_capability(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    team_id: str
):
    """
    Get team capability metrics.
    
    Team ID can be department name or team identifier.
    
    Returns:
    {
        "capability_score": 72.5,
        "capability_level": 3,
        "capability_level_name": "Advanced",
        "capability_vector": {
            "skill_coverage": 65.0,
            "skill_diversity": 75.0,
            "skill_depth": 70.0,
            "skill_distribution": 80.0,
            "requirement_alignment": 60.0,
            "skill_maturity": 55.0
        },
        "skill_coverage": {"Python": 80.0, "React": 60.0},
        "avg_coverage": 65.5,
        "skill_strength": {
            "avg_skills_per_employee": 8.5,
            "max_skills_per_employee": 15,
            "unique_skills_count": 45
        },
        "team_summary": {
            "total_employees": 20,
            "total_skills": 170,
            "unique_skills": 45,
            "top_skills": ["Python", "React", "JavaScript"],
            "critical_gaps": ["Kubernetes (only 15.0% coverage)"]
        }
    }
    """
    try:
        # Get team employees (team_id is department name for now)
        employee_records = await employee_repo.get_by_department(session, team_id)
        
        # Fallback to "Unknown" if department not found (98% of employees have "Unknown")
        # Special handling for demo team "SE" - try common variations
        if not employee_records:
            if team_id.upper() == "SE":
                # Try variations: SE, Software Engineering, Software, Eng
                for fallback_dept in ["SE", "Software Engineering", "Software", "Eng", "Unknown"]:
                    employee_records = await employee_repo.get_by_department(session, fallback_dept)
                    if employee_records:
                        break
            elif team_id.lower() != "unknown":
                employee_records = await employee_repo.get_by_department(session, "Unknown")
        
        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Team/department not found: {team_id}. Available departments can be retrieved from /departments endpoint.",
                status_code=404
            )
        
        # Convert to dict format
        team_data = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (emp.metadata or {}),
            }
            for emp in employee_records
        ]
        
        # Calculate capability
        capability = await team_capability_service.calculate_team_capability(team_data)
        
        return unified_success(
            data=capability,
            message="Team capability computed successfully"
        )
    except Exception as exc:
        logger.error(f"Error computing team capability: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to compute team capability: {str(exc)}",
            status_code=500
        )


@router.get("/team/{team_id}/risk-radar")
async def get_team_risk_radar(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    team_id: str
):
    """
    Get team risk radar - expired certs, expiring certs, missing training, skill gaps.
    
    Returns:
    {
        "risk_summary": {
            "total_employees": 20,
            "employees_with_risks": 8,
            "risk_percentage": 40.0,
            "average_risk_score": 35.5,
            "risk_level": "medium",
            "critical_alerts_count": 3,
            "high_alerts_count": 5,
            "medium_alerts_count": 10,
            "total_alerts_count": 18
        },
        "risk_distribution": {
            "critical": 2,
            "high": 3,
            "medium": 3,
            "low": 12
        },
        "employee_risks": [
            {
                "employee_id": "EMP001",
                "risk_score": 65,
                "risk_count": 3,
                "critical_count": 1,
                "high_count": 2,
                "medium_count": 0,
                "alerts": [
                    {
                        "type": "expired_certification",
                        "severity": "critical",
                        "message": "Certification 'Python Certified' expired 30 days ago"
                    }
                ]
            }
        ],
        "total_alerts": 18,
        "critical_alerts": [...],
        "high_alerts": [...]
    }
    """
    try:
        # Get team employees
        employee_records = await employee_repo.get_by_department(session, team_id)
        
        # Fallback to "Unknown" if department not found
        if not employee_records and team_id.lower() != "unknown":
            employee_records = await employee_repo.get_by_department(session, "Unknown")
        
        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Team/department not found: {team_id}",
                status_code=404
            )
        
        # Convert to dict format
        team_data = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (emp.metadata or {}),
            }
            for emp in employee_records
        ]
        
        # Scan risks
        risk_radar = await risk_radar_service.scan_team_risks(
            session,
            team_data,
            employee_records
        )
        
        return unified_success(
            data=risk_radar,
            message="Team risk radar computed successfully"
        )
    except Exception as exc:
        logger.error(f"Error computing risk radar: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to compute risk radar: {str(exc)}",
            status_code=500
        )


@router.get("/team/{team_id}/promotion-readiness")
async def get_team_promotion_readiness(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    team_id: str,
    target_job_family_id: Optional[str] = Query(None, description="Target job family ID for promotion")
):
    """
    Get team promotion readiness - readiness scores, gaps, timelines, training actions.
    
    Returns:
    {
        "pipeline_summary": {
            "ready_now": 3,
            "ready_soon": 5,
            "developing": 12,
            "total_candidates": 20
        },
        "candidates": [
            {
                "employee_id": "EMP001",
                "readiness_score": 85.5,
                "readiness_level": "Ready Now",
                "estimated_timeline": "Ready now",
                "missing_skills_count": 1,
                "missing_qualifications_count": 0
            }
        ]
    }
    """
    try:
        # Get team employees
        employee_records = await employee_repo.get_by_department(session, team_id)
        
        # Fallback to "Unknown" if department not found
        if not employee_records and team_id.lower() != "unknown":
            employee_records = await employee_repo.get_by_department(session, "Unknown")
        
        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Team/department not found: {team_id}",
                status_code=404
            )
        
        # Convert to dict format
        team_data = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (emp.metadata or {}),
            }
            for emp in employee_records
        ]
        
        # Get promotion readiness
        promotion_readiness = await promotion_readiness_service.get_team_promotion_candidates(
            session,
            team_data,
            employee_records,
            target_job_family_id=target_job_family_id
        )
        
        return unified_success(
            data=promotion_readiness,
            message="Team promotion readiness computed successfully"
        )
    except Exception as exc:
        logger.error(f"Error computing promotion readiness: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to compute promotion readiness: {str(exc)}",
            status_code=500
        )


@router.get("/employee/{employee_id}/career-path")
async def get_employee_career_path(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    employee_id: str
):
    """
    Get employee career path - top 3 roles, readiness, gaps, training, timeline.
    
    Uses Azure OpenAI to predict career paths.
    
    Returns:
    {
        "employee_id": "EMP001",
        "current_role": "Software Engineer",
        "career_paths": [
            {
                "role_name": "Senior Software Engineer",
                "job_family_id": "SENIOR_ENG",
                "readiness_percentage": 75.5,
                "readiness_level": "Ready Soon",
                "skill_gaps": ["Leadership", "Architecture"],
                "required_trainings": ["Leadership training course", "Architecture training"],
                "timeline_to_reach": "6-12 months",
                "path_step": 1
            },
            {
                "role_name": "Tech Lead",
                "job_family_id": "TECH_LEAD",
                "readiness_percentage": 55.0,
                "readiness_level": "Developing",
                "skill_gaps": ["Team Management", "System Design"],
                "required_trainings": [...],
                "timeline_to_reach": "12-18 months",
                "path_step": 2
            }
        ],
        "career_insights": "Employee shows strong technical foundation...",
        "ai_generated": true
    }
    """
    try:
        # Get employee
        employee_record = await employee_repo.get_by_employee_id(session, employee_id)
        
        if not employee_record:
            return unified_error(
                error_type="NotFound",
                message=f"Employee not found: {employee_id}",
                status_code=404
            )
        
        # Convert to dict format
        employee_data = {
            "employee_id": employee_record.employee_id,
            "department": employee_record.department,
            "skills": employee_record.skills or [],
            "metadata": (employee_record.meta_data or {}) if hasattr(employee_record, "meta_data") else (employee_record.metadata or {}),
        }
        
        # Generate career path
        career_path = await career_path_service.generate_career_path(
            session,
            employee_id,
            employee_data,
            employee_record
        )
        
        return unified_success(
            data=career_path,
            message="Career path generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating career path: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate career path: {str(exc)}",
            status_code=500
        )


@router.get("/forecast/skills-5y")
async def get_skills_forecast_5y(
    session: AsyncSessionDep,
    top_n: int = Query(20, ge=5, le=50, description="Number of top skills to forecast")
):
    """
    Get 5-year skill forecast - emerging skills, declining skills, shortages, hiring, training.
    
    Uses Azure OpenAI for long-term predictions.
    
    Returns:
    {
        "forecast_period": "5 years (2025-2029)",
        "emerging_skills": [
            {
                "skill": "AI/ML Engineering",
                "growth_percentage": 45.0,
                "reason": "Rapid AI adoption across industries"
            }
        ],
        "declining_skills": [
            {
                "skill": "Legacy Framework X",
                "decline_percentage": 15.0,
                "reason": "Technology lifecycle ending"
            }
        ],
        "skill_shortages": [
            {
                "skill": "Kubernetes",
                "shortage_severity": "high",
                "estimated_shortage": 25
            }
        ],
        "hiring_predictions": [
            {
                "skill": "Kubernetes",
                "hiring_needs": 25,
                "timeframe": "Next 2 years"
            }
        ],
        "training_recommendations": [
            {
                "skill": "Kubernetes",
                "priority": "high",
                "recommended_courses": ["Kubernetes Fundamentals", "K8s Advanced"]
            }
        ],
        "forecast_insights": "AI predicts strong growth in AI/ML...",
        "current_skill_count": 150,
        "ai_generated": true
    }
    """
    try:
        # Generate 5-year forecast
        forecast = await forecast_service.forecast_skills_5year(session, top_n=top_n)
        
        return unified_success(
            data=forecast,
            message="5-year skill forecast generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating 5-year forecast: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate 5-year forecast: {str(exc)}",
            status_code=500
        )

