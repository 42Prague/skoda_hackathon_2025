"""
Skill Coach Recommendations Routes (Controllers)
------------------------------------------------
API endpoints for recommendations - interface layer only.
All business logic and DB access handled by services and repositories.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Body

from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.skill_recommendations_service import SkillRecommendationsService
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.schemas.recommendations_schemas import (
    RecommendationsResponse,
    TrainingPathRequest,
    NextRoleRequest,
)
from swx_api.app.utils.scoring import compose_unified_score, ranking_dict
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("skill_recommendations_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/skills/recommendations")


@router.get(
    "/skills/{employee_id}",
    response_model=RecommendationsResponse,
    responses=ERROR_RESPONSES,
)
async def get_skill_recommendations(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    employee_id: str
):
    """Get skill recommendations for an employee."""
    try:
        # Get employee record using async repository
        employee_record = await employee_repo.get_by_employee_id(session, employee_id)
        
        if not employee_record:
            return unified_error(
                error_type="NotFound",
                message=f"Employee not found: {employee_id}",
                status_code=404
            )
        
        employee_data = {
            "employee_id": employee_record.employee_id,
            "department": employee_record.department,
            "skills": employee_record.skills or [],
            "metadata": employee_record.metadata or {},
        }
        
        # Get department data for context using async repository
        dept_records = await employee_repo.get_by_department(
            session,
            employee_record.department
        )
        department_data = {
            "common_skills": _get_common_skills(dept_records),
        } if dept_records else None
        
        # Use async recommendations service
        recommendations_service = SkillRecommendationsService(employee_repo, skill_repo)
        rec_result = await recommendations_service.recommend_skills(
            session,
            employee_data,
            department_data
        )
        recommendations = rec_result["items"]
        ai_mode = rec_result["ai_mode"]
        ai_used = rec_result["ai_used"]
        ai_metrics = rec_result.get("ai_metrics", {})
        
        # Extract AI insights if available
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_insights = None
        # Map "live" to "featherless" for consistency
        if ai_mode == "live":
            ai_mode = "featherless"
        if ai_used and ai_mode == "featherless" and ai_metrics:
            # Reconstruct LLM result format from metrics
            llm_result_format = {
                "ai_readiness": ai_metrics.get("ai_readiness"),
                "ai_risk_signal": ai_metrics.get("ai_risk_signal"),
                "ai_gap_score": ai_metrics.get("ai_gap_score"),
                "missing_skills": [rec["skill"] for rec in recommendations if rec.get("priority") == "high"],
                "strengths": employee_data.get("skills", [])[:5],
                "analysis_summary": f"Recommended {len(recommendations)} skills for development",
            }
            ai_insights = extract_ai_insights(llm_result_format)
        
        skill_list = [rec["skill"] for rec in recommendations]
        score = compose_unified_score(
            skill_scores=ranking_dict(skill_list[:3]),
            gap_scores={"open_recommendations": len(skill_list) * 5},
            role_fit_score=75,
            next_role_readiness=70,
            risk_score=max(15, len(skill_list) * 2),
            ai_gap_score=ai_metrics.get("ai_gap_score"),
            ai_readiness=ai_metrics.get("ai_readiness"),
            ai_risk_signal=ai_metrics.get("ai_risk_signal"),
            ai_skill_recommendations_count=ai_metrics.get("ai_skill_recommendations_count"),
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/skills/recommendations/skills",
        )

        reasoning = "Recommendations derived from department skill distribution and AI analysis."
        priority_breakdown = sorted({rec["priority"] for rec in recommendations})
        payload = {
            "recommended_skills": recommendations,
            "reasoning": reasoning,
            "priority": priority_breakdown,
            "unified_score": score.model_dump(),
            "ai_used": ai_used,
            "ai_mode": ai_mode,
        }

        return unified_success(
            data=payload,
            message="Skill recommendations retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting recommendations: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get recommendations: {str(exc)}",
            status_code=500
        )


@router.post("/training-path", responses=ERROR_RESPONSES)
async def get_training_path(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    request: TrainingPathRequest
):
    """Get training path for acquiring target skills."""
    try:
        # Get employee record using async repository
        employee_record = await employee_repo.get_by_employee_id(
            session,
            request.employee_id
        )
        
        if not employee_record:
            return unified_error(
                error_type="NotFound",
                message=f"Employee not found: {request.employee_id}",
                status_code=404
            )
        
        employee_data = {
            "employee_id": employee_record.employee_id,
            "department": employee_record.department,
            "skills": employee_record.skills or [],
            "metadata": employee_record.metadata or {},
        }
        
        # Use async recommendations service
        recommendations_service = SkillRecommendationsService(employee_repo, skill_repo)
        training_path = await recommendations_service.recommend_training_path(
            employee_data,
            request.target_skills
        )
        
        # Try to get AI analysis for insights
        from swx_api.app.services.skill_ai_service import SkillAIService
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_service = SkillAIService(employee_repo, skill_repo)
        ai_mode = "heuristic"
        ai_insights = None
        try:
            ai_analysis = await ai_service.analyze_employee(
                session,
                request.employee_id,
                employee_data,
                {"required_skills": request.target_skills}
            )
            ai_mode = ai_analysis.get("ai_mode", "heuristic")
            # Map "live" to "featherless" for consistency
            if ai_mode == "live":
                ai_mode = "featherless"
            ai_insights = extract_ai_insights(ai_analysis) if ai_mode == "featherless" else None
        except Exception:
            pass
        
        skill_scores = ranking_dict(request.target_skills[:3])
        score = compose_unified_score(
            skill_scores=skill_scores,
            gap_scores={"remaining_skills": len(request.target_skills) * 5},
            role_fit_score=72,
            next_role_readiness=max(50, 90 - len(request.target_skills) * 3),
            risk_score=25,
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/skills/recommendations/training-path",
        )

        payload = {
            "training_path": training_path,
            "unified_score": score.model_dump(),
            "ai_used": False,
            "ai_mode": "heuristic_fallback",
        }

        return unified_success(
            data=payload,
            message="Training path generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating training path: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate training path: {str(exc)}",
            status_code=500
        )


@router.post("/next-role", responses=ERROR_RESPONSES)
async def get_next_role_recommendations(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    request: NextRoleRequest
):
    """Get next role recommendations for an employee."""
    try:
        # Get employee record using async repository
        employee_record = await employee_repo.get_by_employee_id(
            session,
            request.employee_id
        )
        
        if not employee_record:
            return unified_error(
                error_type="NotFound",
                message=f"Employee not found: {request.employee_id}",
                status_code=404
            )
        
        employee_data = {
            "employee_id": employee_record.employee_id,
            "department": employee_record.department,
            "skills": employee_record.skills or [],
            "metadata": employee_record.metadata or {},
        }
        
        # Use async recommendations service
        recommendations_service = SkillRecommendationsService(employee_repo, skill_repo)
        recommendations = await recommendations_service.recommend_next_role(
            employee_data,
            request.available_roles
        )
        
        # Try to get AI analysis for insights
        from swx_api.app.services.skill_ai_service import SkillAIService
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_service = SkillAIService(employee_repo, skill_repo)
        ai_mode = "heuristic"
        ai_insights = None
        if recommendations:
            try:
                top_role = recommendations[0]
                ai_analysis = await ai_service.analyze_employee(
                    session,
                    request.employee_id,
                    employee_data,
                    top_role
                )
                ai_mode = ai_analysis.get("ai_mode", "heuristic")
                ai_insights = extract_ai_insights(ai_analysis) if ai_mode == "live" else None
            except Exception:
                pass
        
        top_score = recommendations[0]["readiness_score"] if recommendations else 60
        skill_scores = ranking_dict([rec["role"] for rec in recommendations[:3]])
        score = compose_unified_score(
            skill_scores=skill_scores,
            gap_scores={"open_roles": len(recommendations) * 4},
            role_fit_score=top_score,
            next_role_readiness=top_score,
            risk_score=max(10, 100 - top_score),
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/skills/recommendations/next-role",
        )

        payload = {
            "recommendations": recommendations,
            "unified_score": score.model_dump(),
            "ai_used": False,
            "ai_mode": "heuristic_fallback",
        }

        return unified_success(
            data=payload,
            message="Role recommendations retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting role recommendations: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get role recommendations: {str(exc)}",
            status_code=500
        )


@router.get("/department-interventions/{department_name}", responses=ERROR_RESPONSES)
async def get_department_interventions(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    department_name: str
):
    """Get department-wide intervention recommendations."""
    try:
        # Get department employees using async repository
        employee_records = await employee_repo.get_by_department(session, department_name)
        
        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Department not found: {department_name}",
                status_code=404
            )
        
        department_data_list = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in employee_records
        ]
        
        # Use async analytics service
        analytics_service = SkillAnalyticsService()
        department_analytics = await analytics_service.analyze_department(
            department_name,
            department_data_list
        )
        
        # Use async recommendations service
        recommendations_service = SkillRecommendationsService(employee_repo, skill_repo)
        interventions = await recommendations_service.recommend_department_interventions(
            department_analytics
        )
        
        intervention_types = [item["type"] for item in interventions[:3]]
        score = compose_unified_score(
            skill_scores=ranking_dict(intervention_types or ["coaching"]),
            gap_scores={"intervention_count": len(interventions) * 6},
            role_fit_score=70,
            next_role_readiness=65,
            risk_score=max(20, len(interventions) * 5),
        )

        payload = {
            "interventions": interventions,
            "unified_score": score.model_dump(),
            "ai_used": False,
            "ai_mode": "heuristic_fallback",
        }

        return unified_success(
            data=payload,
            message="Department interventions retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting department interventions: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get department interventions: {str(exc)}",
            status_code=500
        )


def _get_common_skills(employee_records: List) -> List[str]:
    """Get common skills across employees."""
    from collections import Counter
    
    skill_counter = Counter()
    for emp in employee_records:
        if emp.skills:
            skill_counter.update(emp.skills)
    
    # Return skills that appear in at least 30% of employees
    threshold = max(1, len(employee_records) * 0.3)
    return [skill for skill, count in skill_counter.items() if count >= threshold]
