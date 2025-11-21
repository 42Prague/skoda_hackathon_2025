"""
Career Coach Routes
------------------
API endpoints for AI Career Coach Chat feature.
"""

import logging

from fastapi import APIRouter, Body

from swx_api.app.schemas.career_coach_schemas import (
    CareerChatRequest,
    CareerChatResponse,
)
from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.career_coach_service import CareerCoachService
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("career_coach_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/ai")


@router.post(
    "/career-chat",
    response_model=CareerChatResponse,
    responses=ERROR_RESPONSES,
)
async def career_chat(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    request: CareerChatRequest = Body(...),
):
    """
    AI Career Coach Chat endpoint.
    
    Provides conversational career guidance with:
    - Personalized coaching advice
    - Skill gap analysis
    - Next role recommendations
    - Readiness assessment
    - Training recommendations
    - Risk warnings
    """
    try:
        # Initialize career coach service
        coach_service = CareerCoachService(employee_repo, skill_repo)

        # Prepare context
        context = {
            "employee_id": request.employee_id,
            "skills": request.skills or [],
            "career_goals": request.career_goals or "",
            "department": request.department or "",
        }

        # Run chat
        result = await coach_service.run_chat(
            session=session,
            user_message=request.user_message,
            context=context,
        )

        return unified_success(
            data=result,
            message="Career coach response generated successfully"
        )

    except Exception as exc:
        logger.error(f"Error in career chat: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Career chat failed: {str(exc)}",
            status_code=500
        )

