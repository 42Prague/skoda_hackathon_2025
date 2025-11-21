"""
AI Routes
---------
API endpoints for AI-powered intelligence and analysis.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel

from swx_api.app.schemas.ai_schemas import (
    AIEmployeeSummary,
    AITeamSummary,
    AISuccessionSummary,
    AIForecastExplanation,
    AIDepartmentComparison,
)
from swx_api.app.schemas.common_schemas import ErrorResponse


class FreeFormAIRequest(BaseModel):
    """Request model for free-form AI endpoint."""
    prompt: str
    schema_data: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
from swx_api.app.services.ai.ai_employee_service import AIEmployeeService
from swx_api.app.services.ai.ai_team_service import AITeamService
from swx_api.app.services.ai.ai_succession_service import AISuccessionService
from swx_api.app.services.ai.ai_forecast_service import AIForecastService
from swx_api.app.services.ai.ai_compare_service import AICompareService
from swx_api.app.services.ai.ai_what_if_service import AIWhatIfService
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.core.database.db import AsyncSessionDep
from swx_api.app.repositories.employee_repository import EmployeeRepository

logger = logging.getLogger("ai_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/ai")


@router.get("/employee-intel/{employee_id}", response_model=AIEmployeeSummary, responses=ERROR_RESPONSES)
async def get_employee_intel(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    employee_id: str,
    language: Optional[str] = Query(default=None, description="Language: 'cz' or 'en'")
):
    """Get AI-powered employee intelligence summary."""
    try:
        employee = await employee_repo.get_by_employee_id(session, employee_id)
        if not employee:
            return unified_error(
                error_type="NotFound",
                message=f"Employee not found: {employee_id}",
                status_code=404
            )
        
        from swx_api.app.models.skoda_models import QualificationRecord, HistoricalEmployeeSnapshot
        from sqlmodel import select
        
        qualifications_stmt = select(QualificationRecord).where(
            QualificationRecord.employee_id == employee_id
        )
        # SQLAlchemy AsyncSession uses execute().scalars(), not exec()
        result = await session.execute(qualifications_stmt)
        qualifications_result = result.scalars()
        qualifications = [
            {
                "qualification_id": q.qualification_id,
                "name_cz": q.qualification_name_cz,
                "name_en": q.qualification_name_en,
                "status": q.status
            }
            for q in qualifications_result.all()
        ]
        
        history_stmt = select(HistoricalEmployeeSnapshot).where(
            HistoricalEmployeeSnapshot.employee_id == employee_id
        )
        # SQLAlchemy AsyncSession uses execute().scalars(), not exec()
        result = await session.execute(history_stmt)
        history_result = result.scalars()
        history = [
            {
                "snapshot_date": h.snapshot_date.isoformat() if h.snapshot_date else None,
                "department": h.department,
                "skills": h.skills or [],
            }
            for h in history_result.all()
        ]
        
        employee_service = AIEmployeeService()
        summary = await employee_service.generate_summary(
            employee_data={
                "employee_id": employee.employee_id,
                "department": employee.department,
                "personal_number": getattr(employee, "personal_number", None),
            },
            skills=employee.skills or [],
            history=history,
            qualifications=qualifications,
            language=language
        )
        
        return unified_success(
            data=summary.dict(),
            message="Employee intelligence generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating employee intel: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate employee intelligence: {str(exc)}",
            status_code=500
        )


@router.get("/team-intel/{department}", response_model=AITeamSummary, responses=ERROR_RESPONSES)
async def get_team_intel(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    department: str,
    language: Optional[str] = Query(default=None, description="Language: 'cz' or 'en'")
):
    """Get AI-powered team health intelligence."""
    try:
        employees = await employee_repo.get_by_department(session, department)
        if not employees:
            return unified_error(
                error_type="NotFound",
                message=f"Department not found: {department}",
                status_code=404
            )
        
        from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
        analytics_service = SkillAnalyticsService()
        
        team_data = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
            }
            for emp in employees
        ]
        
        department_analytics = await analytics_service.analyze_department(department, team_data)
        
        skill_coverage = department_analytics.get("team_skill_heatmap", {})
        risk_indicators = {
            "risk_score": department_analytics.get("risk_scores", {}).get("overall", 30),
            "skill_shortages": department_analytics.get("skill_shortages", []),
        }
        
        team_service = AITeamService()
        summary = await team_service.generate_summary(
            team_data=team_data,
            department=department,
            skill_coverage=skill_coverage,
            risk_indicators=risk_indicators,
            language=language
        )
        
        return unified_success(
            data=summary.dict(),
            message="Team intelligence generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating team intel: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate team intelligence: {str(exc)}",
            status_code=500
        )


@router.get("/succession-intel/{department}", response_model=AISuccessionSummary, responses=ERROR_RESPONSES)
async def get_succession_intel(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    department: str,
    language: Optional[str] = Query(default=None, description="Language: 'cz' or 'en'")
):
    """Get AI-powered succession intelligence."""
    try:
        from swx_api.app.routes.analytics_route import _build_succession_snapshot
        from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
        
        employees = await employee_repo.get_by_department(session, department)
        if not employees:
            return unified_error(
                error_type="NotFound",
                message=f"Department not found: {department}",
                status_code=404
            )
        
        analytics_service = SkillAnalyticsService()
        department_payload = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (emp.metadata or {}),
            }
            for emp in employees
        ]
        
        department_analytics = await analytics_service.analyze_department(department, department_payload)
        snapshot = await _build_succession_snapshot(
            session=session,
            employee_repo=employee_repo,
            skill_repo=skill_repo,
            department_name=department,
            employee_records=employees,
            department_analytics=department_analytics,
        )
        
        succession_service = AISuccessionService()
        summary = await succession_service.analyze_succession(
            department=department,
            candidates=snapshot.get("candidates", []),
            pipeline_data=snapshot.get("pipeline_summary", {}),
            language=language
        )
        
        return unified_success(
            data=summary.dict(),
            message="Succession intelligence generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating succession intel: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate succession intelligence: {str(exc)}",
            status_code=500
        )


@router.get("/forecast-intel/{skill}", response_model=AIForecastExplanation, responses=ERROR_RESPONSES)
async def get_forecast_intel(
    session: AsyncSessionDep,
    skill: str,
    forecast_months: int = Query(default=6, ge=3, le=12),
    language: Optional[str] = Query(default=None, description="Language: 'cz' or 'en'")
):
    """Get AI-powered forecast explanation."""
    try:
        from swx_api.app.services.predictive_analytics_service import PredictiveAnalyticsService
        from swx_api.app.models.skoda_models import HistoricalEmployeeSnapshot
        from sqlmodel import select
        
        history_stmt = select(HistoricalEmployeeSnapshot).order_by(
            HistoricalEmployeeSnapshot.snapshot_date
        )
        # SQLAlchemy AsyncSession uses execute().scalars(), not exec()
        result = await session.execute(history_stmt)
        history_result = result.scalars()
        historical_snapshots = [
            {
                "snapshot_date": h.snapshot_date.isoformat() if h.snapshot_date else None,
                "skills": h.skills or [],
            }
            for h in history_result.all()
        ]
        
        analytics_service = PredictiveAnalyticsService()
        forecast = await analytics_service.forecast_skill_demand(
            skill=skill,
            historical_snapshots=historical_snapshots,
            forecast_months=forecast_months
        )
        
        forecast_service = AIForecastService()
        explanation = await forecast_service.explain_forecast(
            forecast_data=forecast,
            historical_trend=[],
            method=forecast.get("method", "arima"),
            language=language
        )
        
        return unified_success(
            data=explanation.dict(),
            message="Forecast intelligence generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating forecast intel: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate forecast intelligence: {str(exc)}",
            status_code=500
        )


@router.get("/compare/{dep1}/{dep2}", response_model=AIDepartmentComparison, responses=ERROR_RESPONSES)
async def compare_departments(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    dep1: str,
    dep2: str,
    language: Optional[str] = Query(default=None, description="Language: 'cz' or 'en'")
):
    """Compare two departments with AI analysis."""
    try:
        from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
        
        dept1_employees = await employee_repo.get_by_department(session, dep1)
        dept2_employees = await employee_repo.get_by_department(session, dep2)
        
        if not dept1_employees or not dept2_employees:
            return unified_error(
                error_type="NotFound",
                message="One or both departments not found",
                status_code=404
            )
        
        analytics_service = SkillAnalyticsService()
        
        dept1_payload = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
            }
            for emp in dept1_employees
        ]
        
        dept2_payload = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
            }
            for emp in dept2_employees
        ]
        
        dept1_analytics = await analytics_service.analyze_department(dep1, dept1_payload)
        dept2_analytics = await analytics_service.analyze_department(dep2, dept2_payload)
        
        compare_service = AICompareService()
        comparison = await compare_service.compare_departments(
            department1_data={
                "name": dep1,
                "employees": dept1_payload,
                "analytics": dept1_analytics,
            },
            department2_data={
                "name": dep2,
                "employees": dept2_payload,
                "analytics": dept2_analytics,
            },
            metrics={
                "dept1_size": len(dept1_employees),
                "dept2_size": len(dept2_employees),
            },
            language=language
        )
        
        return unified_success(
            data=comparison.dict(),
            message="Department comparison generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error comparing departments: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to compare departments: {str(exc)}",
            status_code=500
        )


@router.post("/what-if", responses=ERROR_RESPONSES)
async def what_if_scenario(
    session: AsyncSessionDep,
    scenario_type: str = Query(..., description="remove_employee, add_skill, remove_skill, complete_course, move_department"),
    employee_id: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None),
    changes: Dict[str, Any] = {}
):
    """Run what-if scenario simulation."""
    try:
        from swx_api.app.utils.dependencies import EmployeeRepoDep
        from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
        
        employee_repo = EmployeeRepository()
        
        base_data = {}
        if employee_id:
            employee = await employee_repo.get_by_employee_id(session, employee_id)
            if employee:
                base_data = {
                    "employee_id": employee.employee_id,
                    "department": employee.department,
                    "skills": employee.skills or [],
                }
        elif department:
            employees = await employee_repo.get_by_department(session, department)
            base_data = {
                "department": department,
                "employees": [
                    {
                        "employee_id": emp.employee_id,
                        "skills": emp.skills or [],
                    }
                    for emp in employees
                ]
            }
        
        what_if_service = AIWhatIfService()
        result = await what_if_service.simulate_scenario(
            scenario_type=scenario_type,
            base_data=base_data,
            changes=changes
        )
        
        return unified_success(
            data=result,
            message="What-if scenario completed successfully"
        )
    except Exception as exc:
        logger.error(f"Error running what-if scenario: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"What-if scenario failed: {str(exc)}",
            status_code=500
        )


@router.post("/free-form", responses=ERROR_RESPONSES)
async def free_form_ai(request: FreeFormAIRequest):
    """Execute free-form AI prompt."""
    try:
        from swx_api.app.services.ai_orchestrator import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        result = await orchestrator.run(
            prompt_name="employee_summary",
            variables={"employee_data": request.prompt},
            schema=request.schema_data or {"response": str},
            language=request.language
        )
        
        return unified_success(
            data=result,
            message="Free-form AI query completed successfully"
        )
    except Exception as exc:
        logger.error(f"Error executing free-form AI: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Free-form AI query failed: {str(exc)}",
            status_code=500
        )

