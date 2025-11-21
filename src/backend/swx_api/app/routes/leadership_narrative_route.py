"""
Leadership Narrative Routes
---------------------------
API endpoints for AI Leadership Narrative feature.
"""

import logging

from fastapi import APIRouter

from swx_api.app.schemas.leadership_narrative_schemas import LeadershipNarrativeResponse
from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.leadership_narrative_service import LeadershipNarrativeService
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.core.database.db import AsyncSessionDep
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.routes.analytics_route import _build_succession_snapshot

logger = logging.getLogger("leadership_narrative_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/ai")


@router.get(
    "/leadership-narrative/{department}",
    response_model=LeadershipNarrativeResponse,
    responses=ERROR_RESPONSES,
)
async def get_leadership_narrative(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    department: str,
):
    """
    Generate AI-powered leadership succession narrative.
    
    Analyzes succession radar data and generates:
    - McKinsey-style narrative paragraphs
    - Leadership action recommendations
    - Risk summary with pipeline strength
    - Top successor candidates
    """
    try:
        # Get employee records for department
        employee_records = await employee_repo.get_by_department(session, department)
        
        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Department not found: {department}",
                status_code=404
            )
        
        # Build department payload
        department_payload = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (emp.metadata or {}),
            }
            for emp in employee_records
        ]
        
        # Get department analytics
        analytics_service = SkillAnalyticsService()
        department_analytics = await analytics_service.analyze_department(
            department, department_payload
        )
        
        # Build succession snapshot
        snapshot = await _build_succession_snapshot(
            session=session,
            employee_repo=employee_repo,
            skill_repo=skill_repo,
            department_name=department,
            employee_records=employee_records,
            department_analytics=department_analytics,
        )
        
        # Initialize narrative service
        narrative_service = LeadershipNarrativeService(employee_repo, skill_repo)
        
        # Generate narrative
        result = await narrative_service.generate_leadership_narrative(
            session=session,
            department_name=department,
            succession_data=snapshot,
        )
        
        return unified_success(
            data=result,
            message="Leadership narrative generated successfully"
        )
        
    except Exception as exc:
        logger.error(f"Error generating leadership narrative: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Leadership narrative generation failed: {str(exc)}",
            status_code=500
        )

