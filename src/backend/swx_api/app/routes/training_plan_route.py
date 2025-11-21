"""
Training Plan Routes
--------------------
API endpoints for AI Training Plan Generator feature.
"""

import logging

from fastapi import APIRouter, Body

from swx_api.app.schemas.training_plan_schemas import (
    TrainingPlanRequest,
    TrainingPlanResponse,
)
from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.training_plan_service import TrainingPlanService
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("training_plan_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/ai")


@router.post(
    "/training-plan",
    response_model=TrainingPlanResponse,
    responses=ERROR_RESPONSES,
)
async def generate_training_plan(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    request: TrainingPlanRequest = Body(...),
):
    """
    Generate personalized AI training plan.
    
    Creates comprehensive training plan with:
    - Weekly breakdown (12-16 weeks)
    - Course recommendations (external + Škoda Academy)
    - Skill progression map
    - Mentor recommendations
    - Risk assessment
    - Practice tasks
    - Estimated time to readiness
    """
    try:
        # Initialize training plan service
        plan_service = TrainingPlanService(employee_repo, skill_repo)

        # Generate training plan
        result = await plan_service.generate_training_plan(
            session=session,
            employee_id=request.employee_id,
            skills=request.skills,
            gaps=request.gaps,
            desired_role=request.desired_role,
        )

        return unified_success(
            data=result,
            message="Training plan generated successfully"
        )

    except Exception as exc:
        logger.error(f"Error generating training plan: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Training plan generation failed: {str(exc)}",
            status_code=500
        )

