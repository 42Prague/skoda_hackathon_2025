"""
Skill Coach Skill Routes (Controllers)
---------------------------------------
API endpoints for skill ontology and analysis - interface layer only.
All business logic and DB access handled by services and repositories.
"""

import logging
from typing import Any, Dict, List, Optional

import anyio
import pandas as pd
from fastapi import APIRouter, Body

from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.skill_ontology_service import build_skill_ontology
from swx_api.app.services.skill_ai_service import SkillAIService
from swx_api.app.services.ingestion_service import paths
from swx_api.app.schemas.skill_schemas import SkillAnalysisRequest
from swx_api.app.utils.cache import global_cache
from swx_api.app.utils.scoring import compose_unified_score, ranking_dict
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("skill_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/skills")


@router.post("/ontology", responses=ERROR_RESPONSES)
async def build_ontology(
    dataset_id: Optional[str] = None
):
    """
    Build skill ontology from dataset.
    
    If dataset_id is provided, uses that dataset. Otherwise uses latest.
    """
    try:
        cache_namespace = "ontology"
        cache_key = dataset_id or "latest"
        cached_response = global_cache.get(cache_namespace, cache_key)
        if cached_response:
            return unified_success(
                data=cached_response,
                message="Skill ontology retrieved from cache"
            )
        # Load dataset (sync file I/O is OK for pandas)
        if dataset_id:
            normalized_path = paths.normalized_dir / f"{dataset_id}.csv"
        else:
            # Get latest dataset
            datasets = list(paths.normalized_dir.glob("*.csv"))
            if not datasets:
                return unified_error(
                    error_type="NotFound",
                    message="No datasets found",
                    status_code=404
                )
            normalized_path = max(datasets, key=lambda p: p.stat().st_mtime)
        
        if not normalized_path.exists():
            return unified_error(
                error_type="NotFound",
                message=f"Dataset not found: {dataset_id}",
                status_code=404
            )
        
        df = await anyio.to_thread.run_sync(pd.read_csv, normalized_path)
        ontology = await anyio.to_thread.run_sync(build_skill_ontology, df)
        global_cache.set(cache_namespace, cache_key, ontology)
        
        return unified_success(
            data=ontology,
            message="Skill ontology built successfully"
        )
    except Exception as exc:
        logger.error(f"Error building ontology: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to build ontology: {str(exc)}",
            status_code=500
        )


@router.post("/analysis", responses=ERROR_RESPONSES)
async def analyze_employee_skills(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    analysis_request: SkillAnalysisRequest
):
    """
    Analyze employee skills using AI.
    
    Returns:
        - current_skills
        - missing_skills
        - gap_score
        - strengths
        - recommended_roles
        - development_path
        - analysis_summary
    """
    try:
        # Get employee record using async repository
        employee_record = await employee_repo.get_by_employee_id(
            session,
            analysis_request.employee_id
        )
        
        if not employee_record:
            return unified_error(
                error_type="NotFound",
                message=f"Employee not found: {analysis_request.employee_id}",
                status_code=404
            )
        
        # Prepare employee data
        employee_data = {
            "employee_id": employee_record.employee_id,
            "department": employee_record.department,
            "skills": employee_record.skills or [],
            "metadata": employee_record.metadata or {},
        }
        
        # Perform analysis using async service
        ai_service = SkillAIService(employee_repo, skill_repo)
        analysis = await ai_service.analyze_employee(
            session,
            employee_record.employee_id,
            employee_data,
            analysis_request.role_requirements
        )
        
        # Extract AI insights and determine mode
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_mode = analysis.get("ai_mode", "heuristic")
        # Map "live" to "featherless" for consistency
        if ai_mode == "live":
            ai_mode = "featherless"
        ai_insights = extract_ai_insights(analysis) if ai_mode == "featherless" else None
        
        score = compose_unified_score(
            skill_scores=ranking_dict(analysis.get("strengths", analysis.get("current_skills", [])[:3])),
            gap_scores={"gap_score": analysis.get("gap_score", 65)},
            role_fit_score=analysis.get("gap_score", 65),
            next_role_readiness=analysis.get("gap_score", 65),
            risk_score=max(0, 100 - analysis.get("gap_score", 65)),
            ai_gap_score=analysis.get("ai_gap_score"),
            ai_readiness=analysis.get("ai_readiness"),
            ai_risk_signal=analysis.get("ai_risk_signal"),
            ai_skill_recommendations_count=analysis.get("ai_skill_recommendations_count"),
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/skills/analysis",
        )

        payload = {
            "analysis": analysis,
            "unified_score": score.model_dump(),
        }

        return unified_success(
            data=payload,
            message="Skill analysis completed successfully"
        )
    except Exception as exc:
        logger.error(f"Error analyzing skills: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Analysis failed: {str(exc)}",
            status_code=500
        )


@router.get("/analysis/{employee_id}", responses=ERROR_RESPONSES)
async def get_employee_analysis(
    session: AsyncSessionDep,
    skill_repo: SkillRepoDep,
    employee_id: str
):
    """Get latest skill analysis for an employee."""
    try:
        # Get latest analysis using async repository
        analysis_record = await skill_repo.get_latest_by_employee_id(
            session,
            employee_id
        )
        
        if not analysis_record:
            return unified_error(
                error_type="NotFound",
                message=f"No analysis found for employee: {employee_id}",
                status_code=404
            )
        
        analysis = analysis_record.analysis_json or {}
        
        # Extract AI insights and determine mode
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_mode = analysis.get("ai_mode", "heuristic")
        # Map "live" to "featherless" for consistency
        if ai_mode == "live":
            ai_mode = "featherless"
        ai_insights = extract_ai_insights(analysis) if ai_mode == "featherless" else None
        
        score = compose_unified_score(
            skill_scores=ranking_dict(analysis.get("strengths", analysis.get("current_skills", [])[:3])),
            gap_scores={"gap_score": analysis.get("gap_score", 65)},
            role_fit_score=analysis.get("gap_score", 65),
            next_role_readiness=analysis.get("gap_score", 65),
            risk_score=max(0, 100 - analysis.get("gap_score", 65)),
            ai_gap_score=analysis.get("ai_gap_score"),
            ai_readiness=analysis.get("ai_readiness"),
            ai_risk_signal=analysis.get("ai_risk_signal"),
            ai_skill_recommendations_count=analysis.get("ai_skill_recommendations_count"),
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/skills/analysis/{employee_id}",
        )

        payload = {
            "id": str(analysis_record.id),
            "employee_id": analysis_record.employee_id,
            "analysis": analysis,
            "recommendations": analysis_record.recommendations_json,
            "created_at": analysis_record.created_at.isoformat(),
            "unified_score": score.model_dump(),
        }

        return unified_success(
            data=payload,
            message="Analysis retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error retrieving analysis: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to retrieve analysis: {str(exc)}",
            status_code=500
        )


@router.post("/role-fit/{employee_id}", responses=ERROR_RESPONSES)
async def calculate_role_fit(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    employee_id: str,
    role_requirements: Dict[str, Any] = Body(...)
):
    """
    Calculate role-fit score for an employee.
    
    Request body:
    {
        "role_title": "Software Engineer",
        "required_skills": ["Python", "JavaScript"],
        "preferred_skills": ["React", "Node.js"],
        "department": "Engineering"
    }
    
    Returns:
        - role_fit_score: Integer 0-100
        - required_skills_match: Number of matching required skills
        - preferred_skills_match: Number of matching preferred skills
        - missing_required: List of missing required skills
        - missing_preferred: List of missing preferred skills
        - recommendation: Text recommendation
    """
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
        
        # Calculate role-fit using async service
        ai_service = SkillAIService(employee_repo, skill_repo)
        role_fit = ai_service.predict_role_readiness(employee_data, role_requirements)
        
        # Try to get AI analysis for this employee to extract insights
        try:
            analysis = await ai_service.analyze_employee(
                session,
                employee_id,
                employee_data,
                role_requirements
            )
            from swx_api.app.utils.scoring import extract_ai_insights
            ai_mode = analysis.get("ai_mode", "heuristic")
            ai_insights = extract_ai_insights(analysis) if ai_mode == "live" else None
        except Exception:
            ai_mode = "heuristic"
            ai_insights = None
        
        score = compose_unified_score(
            skill_scores=ranking_dict(role_fit.get("matching_skills", employee_data["skills"][:3])),
            gap_scores={"missing_required": len(role_fit.get("missing_required", [])) * 10},
            role_fit_score=role_fit.get("role_fit_score", 65),
            next_role_readiness=role_fit.get("readiness_score", 60),
            risk_score=max(15, len(role_fit.get("missing_required", [])) * 5),
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/skills/role-fit",
        )

        payload = {
            "role_fit": role_fit,
            "unified_score": score.model_dump(),
        }

        return unified_success(
            data=payload,
            message="Role-fit score calculated successfully"
        )
    except Exception as exc:
        logger.error(f"Error calculating role-fit: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to calculate role-fit: {str(exc)}",
            status_code=500
        )
