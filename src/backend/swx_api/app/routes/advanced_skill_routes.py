"""
Advanced Skill Features Routes (Controllers)
---------------------------------------------
API endpoints for all advanced skill features - interface layer only.
All business logic and DB access handled by services and repositories.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Query, Body

from swx_api.app.services.skill_forecasting_service import SkillForecastingService
from swx_api.app.services.skill_taxonomy_service import SkillTaxonomyService
from swx_api.app.services.role_fit_service import RoleFitService
from swx_api.app.services.team_similarity_service import TeamSimilarityService
from swx_api.app.services.mentor_recommendation_service import MentorRecommendationService
from swx_api.app.services.scenario_simulation_service import ScenarioSimulationService
from swx_api.app.services.data_quality_service import AdvancedDQService
from swx_api.app.services.data_repair_service import DataRepairService
from swx_api.app.services.audit_service import AuditService
from swx_api.app.models.skill_models import (
    LearningHistory,
    LearningHistoryCreate,
    LearningHistoryUpdate,
    LearningHistoryPublic,
)
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.app.utils.dependencies import (
    EmployeeRepoDep,
    LearningHistoryRepoDep,
    AuditLogRepoDep
)
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("advanced_skill_routes")

router = APIRouter(prefix="/api")

# Initialize services (no session needed at init)
forecasting_service = SkillForecastingService()
taxonomy_service = SkillTaxonomyService()
role_fit_service = RoleFitService()
team_similarity_service = TeamSimilarityService()
mentor_service = MentorRecommendationService()
simulation_service = ScenarioSimulationService()
advanced_dq_service = AdvancedDQService()
data_repair_service = DataRepairService()


# ============================================================================
# Skill Forecasting
# ============================================================================

@router.get("/analytics/forecast")
async def get_skill_forecast(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    audit_repo: AuditLogRepoDep,
    months: int = Query(6, ge=3, le=12, description="Forecast horizon in months (3, 6, or 12)")
):
    """Get skill demand forecast."""
    try:
        # Get all employees using async repository
        employee_records = await employee_repo.get_all_employees(session)
        
        all_employees = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in employee_records
        ]
        
        # Generate forecast (async)
        forecast_horizon = f"{months}m"
        forecast = await forecasting_service.forecast_skills_async(
            all_employees,
            forecast_horizon=forecast_horizon
        )
        
        # Log AI call (async)
        audit_service = AuditService(audit_repo)
        await audit_service.log_ai_call(
            session,
            service_name="skill_forecasting",
            model="llama-3.1",
            prompt_length=1000,
            response_length=2000,
            success=True
        )
        
        return unified_success(
            data=forecast,
            message=f"Skill forecast generated for {forecast_horizon}"
        )
    except Exception as exc:
        logger.error(f"Error generating forecast: {exc}", exc_info=True)
        audit_service = AuditService(audit_repo)
        await audit_service.log_error(
            session,
            error_type="ForecastError",
            error_message=str(exc),
            service_name="skill_forecasting"
        )
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate forecast: {str(exc)}",
            status_code=500
        )


# ============================================================================
# Skill Taxonomy
# ============================================================================

@router.get("/skills/taxonomy")
async def get_skill_taxonomy(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    audit_repo: AuditLogRepoDep
):
    """Get automated skill taxonomy."""
    try:
        # Get all employees using async repository
        employee_records = await employee_repo.get_all_employees(session)
        
        all_skills = set()
        employee_data = []
        
        for emp in employee_records:
            skills = emp.skills or []
            all_skills.update(skills)
            employee_data.append({
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": skills,
            })
        
        # Build taxonomy (async)
        taxonomy = await taxonomy_service.build_taxonomy_async(
            list(all_skills),
            employee_data
        )
        
        # Log AI call (async)
        audit_service = AuditService(audit_repo)
        await audit_service.log_ai_call(
            session,
            service_name="skill_taxonomy",
            model="llama-3.1",
            prompt_length=1500,
            response_length=3000,
            success=True
        )
        
        return unified_success(
            data=taxonomy,
            message="Skill taxonomy generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error building taxonomy: {exc}", exc_info=True)
        audit_service = AuditService(audit_repo)
        await audit_service.log_error(
            session,
            error_type="TaxonomyError",
            error_message=str(exc),
            service_name="skill_taxonomy"
        )
        return unified_error(
            error_type="InternalError",
            message=f"Failed to build taxonomy: {str(exc)}",
            status_code=500
        )


# ============================================================================
# Role Fit Matching
# ============================================================================

@router.post("/skills/role-fit")
async def compute_role_fit(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    audit_repo: AuditLogRepoDep,
    employee_id: str = Body(..., description="Employee ID"),
    role_definition: dict = Body(..., description="Role definition with mandatory/preferred skills"),
    skill_importance: Optional[dict] = Body(None, description="Optional skill importance weights")
):
    """Compute role fit score for an employee."""
    try:
        # Get employee record using async repository
        employee_record = await employee_repo.get_by_employee_id(session, employee_id)
        
        if not employee_record:
            return unified_error(
                error_type="NotFound",
                message=f"Employee {employee_id} not found",
                status_code=404
            )
        
        employee_profile = {
            "employee_id": employee_record.employee_id,
            "department": employee_record.department,
            "skills": employee_record.skills or [],
            "metadata": employee_record.metadata or {},
        }
        
        # Compute fit (async)
        fit_result = await role_fit_service.compute_role_fit(
            employee_profile,
            role_definition,
            skill_importance
        )
        
        # Log AI call (async)
        audit_service = AuditService(audit_repo)
        await audit_service.log_ai_call(
            session,
            service_name="role_fit",
            model="llama-3.1",
            prompt_length=800,
            response_length=1500,
            success=True
        )
        
        return unified_success(
            data=fit_result,
            message="Role fit analysis completed"
        )
    except Exception as exc:
        logger.error(f"Error computing role fit: {exc}", exc_info=True)
        audit_service = AuditService(audit_repo)
        await audit_service.log_error(
            session,
            error_type="RoleFitError",
            error_message=str(exc),
            service_name="role_fit"
        )
        return unified_error(
            error_type="InternalError",
            message=f"Failed to compute role fit: {str(exc)}",
            status_code=500
        )


# ============================================================================
# Team Similarity Analysis
# ============================================================================

@router.get("/analytics/team-similarity")
async def get_team_similarity(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep
):
    """Get cross-team skill similarity analysis."""
    try:
        # Get all employees using async repository
        employee_records = await employee_repo.get_all_employees(session)
        
        all_employees = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in employee_records
        ]
        
        # Analyze similarity (async)
        similarity = await team_similarity_service.analyze_team_similarity(all_employees)
        
        return unified_success(
            data=similarity,
            message="Team similarity analysis completed"
        )
    except Exception as exc:
        logger.error(f"Error analyzing team similarity: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to analyze team similarity: {str(exc)}",
            status_code=500
        )


# ============================================================================
# Mentor Recommendation
# ============================================================================

@router.get("/recommendations/mentor/{employee_id}")
async def get_mentor_recommendations(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    employee_id: str,
    max_recommendations: int = Query(10, ge=1, le=50)
):
    """Get mentor recommendations for an employee."""
    try:
        # Get target employee using async repository
        employee_record = await employee_repo.get_by_employee_id(session, employee_id)
        
        if not employee_record:
            return unified_error(
                error_type="NotFound",
                message=f"Employee {employee_id} not found",
                status_code=404
            )
        
        # Get all employees using async repository
        all_records = await employee_repo.get_all_employees(session)
        
        employee_data = {
            "employee_id": employee_record.employee_id,
            "department": employee_record.department,
            "skills": employee_record.skills or [],
            "metadata": employee_record.metadata or {},
        }
        
        all_employees = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in all_records
        ]
        
        # Find mentors (async)
        recommendations = await mentor_service.find_mentors(
            employee_id,
            employee_data,
            all_employees,
            max_recommendations
        )
        
        return unified_success(
            data=recommendations,
            message="Mentor recommendations generated"
        )
    except Exception as exc:
        logger.error(f"Error finding mentors: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to find mentors: {str(exc)}",
            status_code=500
        )


# ============================================================================
# Scenario Simulation
# ============================================================================

@router.post("/analytics/simulate")
async def simulate_scenario(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    audit_repo: AuditLogRepoDep,
    scenario_type: str = Body(..., description="Type: 'employee_loss', 'training_completion', 'skill_mandatory'"),
    scenario_params: dict = Body(..., description="Scenario parameters")
):
    """Simulate a what-if scenario."""
    try:
        # Get current state using async repository
        employee_records = await employee_repo.get_all_employees(session)
        
        current_state = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in employee_records
        ]
        
        # Run simulation (async)
        simulation_result = await simulation_service.simulate_scenario_async(
            scenario_type,
            scenario_params,
            current_state
        )
        
        # Log AI call (async)
        audit_service = AuditService(audit_repo)
        await audit_service.log_ai_call(
            session,
            service_name="scenario_simulation",
            model="llama-3.1",
            prompt_length=1200,
            response_length=2500,
            success=True
        )
        
        return unified_success(
            data=simulation_result,
            message="Scenario simulation completed"
        )
    except Exception as exc:
        logger.error(f"Error simulating scenario: {exc}", exc_info=True)
        audit_service = AuditService(audit_repo)
        await audit_service.log_error(
            session,
            error_type="SimulationError",
            error_message=str(exc),
            service_name="scenario_simulation"
        )
        return unified_error(
            error_type="InternalError",
            message=f"Failed to simulate scenario: {str(exc)}",
            status_code=500
        )


# ============================================================================
# Learning History
# ============================================================================

@router.post("/employees/{employee_id}/learning-history")
async def create_learning_history(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    learning_history_repo: LearningHistoryRepoDep,
    audit_repo: AuditLogRepoDep,
    employee_id: str,
    learning_data: LearningHistoryCreate
):
    """Create a learning history record."""
    try:
        # Verify employee exists using async repository
        employee = await employee_repo.get_by_employee_id(session, employee_id)
        
        if not employee:
            return unified_error(
                error_type="NotFound",
                message=f"Employee {employee_id} not found",
                status_code=404
            )
        
        # Create learning history record using async repository
        learning_record = LearningHistory(
            employee_id=employee_id,
            **learning_data.model_dump()
        )
        
        created_record = await learning_history_repo.create(session, learning_record)
        
        # Log DB write (async)
        audit_service = AuditService(audit_repo)
        await audit_service.log_db_write(
            session,
            table_name="learning_history",
            operation="insert",
            record_id=str(created_record.id)
        )
        
        return unified_success(
            data=LearningHistoryPublic.model_validate(created_record),
            message="Learning history record created",
            status_code=201
        )
    except Exception as exc:
        logger.error(f"Error creating learning history: {exc}", exc_info=True)
        await session.rollback()
        return unified_error(
            error_type="InternalError",
            message=f"Failed to create learning history: {str(exc)}",
            status_code=500
        )


@router.get("/employees/{employee_id}/learning-history")
async def get_learning_history(
    session: AsyncSessionDep,
    learning_history_repo: LearningHistoryRepoDep,
    employee_id: str
):
    """Get learning history for an employee."""
    try:
        # Get learning history using async repository
        learning_records = await learning_history_repo.get_by_employee_id(session, employee_id)
        
        return unified_success(
            data=[LearningHistoryPublic.model_validate(record) for record in learning_records],
            message="Learning history retrieved"
        )
    except Exception as exc:
        logger.error(f"Error retrieving learning history: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to retrieve learning history: {str(exc)}",
            status_code=500
        )


# ============================================================================
# Data Repair
# ============================================================================

@router.post("/ingestion/data-repair")
async def analyze_data_repair(
    session: AsyncSessionDep,
    audit_repo: AuditLogRepoDep,
    dataset_id: str = Body(..., description="Dataset ID to analyze"),
    dataset_name: str = Body(..., description="Dataset name")
):
    """Analyze data and propose repair suggestions."""
    try:
        import pandas as pd
        from swx_api.app.services.ingestion_service import paths
        
        # Try to find the dataset file
        dataset_file = paths.normalized_dir / f"{dataset_name}.csv"
        
        if not dataset_file.exists():
            return unified_error(
                error_type="NotFound",
                message=f"Dataset file not found: {dataset_name}",
                status_code=404
            )
        
        # Read CSV (sync pandas is OK)
        df = pd.read_csv(dataset_file)
        
        # Analyze and propose repairs (async)
        repair_analysis = await data_repair_service.analyze_and_propose_repairs(
            df,
            dataset_id,
            dataset_name
        )
        
        # Log AI call (async)
        audit_service = AuditService(audit_repo)
        await audit_service.log_ai_call(
            session,
            service_name="data_repair",
            model="llama-3.1",
            prompt_length=2000,
            response_length=3000,
            success=True
        )
        
        return unified_success(
            data=repair_analysis,
            message="Data repair analysis completed"
        )
    except Exception as exc:
        logger.error(f"Error analyzing data repair: {exc}", exc_info=True)
        audit_service = AuditService(audit_repo)
        await audit_service.log_error(
            session,
            error_type="DataRepairError",
            error_message=str(exc),
            service_name="data_repair"
        )
        return unified_error(
            error_type="InternalError",
            message=f"Failed to analyze data repair: {str(exc)}",
            status_code=500
        )
