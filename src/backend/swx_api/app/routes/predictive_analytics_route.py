"""
Predictive Analytics Routes
---------------------------
API endpoints for predictive analytics and forecasting.
"""

import logging

from fastapi import APIRouter, Query

from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.predictive_analytics_service import PredictiveAnalyticsService
from swx_api.app.utils.dependencies import EmployeeRepoDep
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("predictive_analytics_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/analytics")


@router.get("/predicted-shortages/{department}", responses=ERROR_RESPONSES)
async def get_predicted_shortages(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    department: str,
    forecast_months: int = Query(default=6, ge=3, le=12)
):
    """Get predicted skill shortages for a department."""
    try:
        service = PredictiveAnalyticsService(employee_repo)
        shortages = await service.estimate_department_shortages(
            session,
            department,
            forecast_months
        )
        
        return unified_success(
            data=shortages,
            message="Predicted shortages retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting predicted shortages: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get predicted shortages: {str(exc)}",
            status_code=500
        )


@router.get("/skill-demand-forecast/{skill}", responses=ERROR_RESPONSES)
async def get_skill_demand_forecast(
    session: AsyncSessionDep,
    skill: str,
    forecast_months: int = Query(default=6, ge=3, le=12),
    historical_snapshots: list = Query(default=None)
):
    """Get skill demand forecast."""
    try:
        service = PredictiveAnalyticsService()
        
        forecast = await service.forecast_skill_demand(
            skill,
            historical_snapshots or [],
            forecast_months
        )
        
        return unified_success(
            data=forecast,
            message="Skill demand forecast retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting skill demand forecast: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get skill demand forecast: {str(exc)}",
            status_code=500
        )

