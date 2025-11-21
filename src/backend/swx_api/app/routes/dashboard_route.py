"""
Skill Coach Dashboard Routes (Controllers)
-------------------------------------------
API endpoints for dashboard data - interface layer only.
All business logic and DB access handled by services and repositories.
"""

from __future__ import annotations

import logging
from statistics import mean
from typing import Any, Dict, Optional

import anyio
import pandas as pd
from fastapi import APIRouter

from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.services.skill_ontology_service import build_skill_ontology
from swx_api.app.services.ingestion_service import paths, read_json_async
from swx_api.app.utils.cache import global_cache
from swx_api.app.utils.scoring import compose_unified_score, ranking_dict
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("skill_dashboard_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/dashboard")
analytics_service = SkillAnalyticsService()


async def _load_latest_ontology() -> Dict[str, Any]:
    cache_key = "latest"
    cached = global_cache.get("ontology", cache_key)
    if cached:
        return cached
    datasets = list(paths.normalized_dir.glob("*.csv"))
    if not datasets:
        return {"skills": [], "clusters": [], "normalized_mapping": {}, "department_skill_map": {}}
    latest_dataset = max(datasets, key=lambda p: p.stat().st_mtime)
    df = await anyio.to_thread.run_sync(pd.read_csv, latest_dataset)
    ontology = await anyio.to_thread.run_sync(build_skill_ontology, df)
    global_cache.set("ontology", cache_key, ontology)
    return ontology


async def _latest_dataset_metadata() -> Optional[Dict[str, Any]]:
    summary_files = list(paths.processed_dir.glob("*_summary.json"))
    if not summary_files:
        return None
    latest_summary = max(summary_files, key=lambda p: p.stat().st_mtime)
    payload = await read_json_async(latest_summary)
    return {
        "dataset_id": payload.get("dataset_id"),
        "row_count": payload.get("row_count"),
        "last_ingested_at": payload.get("generated_at"),
    }


def _group_by_department(records: list[Dict[str, Any]]) -> Dict[str, list[Dict[str, Any]]]:
    groups: Dict[str, list[Dict[str, Any]]] = {}
    for record in records:
        groups.setdefault(record["department"], []).append(record)
    return groups


@router.get("/overview", responses=ERROR_RESPONSES)
async def get_dashboard_overview(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep
):
    """Get dashboard overview data."""
    try:
        cached = global_cache.get("dashboard_overview", "overview")

        employee_records = await employee_repo.get_all_employees(session)
        all_employees = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (getattr(emp, "metadata", None) or {}),
            }
            for emp in employee_records
        ]

        if cached and cached.get("total_employees") == len(employee_records):
            return unified_success(cached, "Dashboard overview retrieved successfully")

        global_analytics = await analytics_service.analyze_global(all_employees)

        departments = {}
        for emp in employee_records:
            dept = emp.department
            if dept not in departments:
                departments[dept] = {
                    "name": dept,
                    "employee_count": 0,
                    "total_skills": 0,
                }
            departments[dept]["employee_count"] += 1
            if emp.skills:
                departments[dept]["total_skills"] += len(emp.skills)

        overview = {
            "total_employees": len(employee_records),
            "total_departments": len(departments),
            "departments": list(departments.values()),
            "global_analytics": global_analytics,
        }

        # Try to get AI insights from sample employees
        from swx_api.app.services.skill_ai_service import SkillAIService
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_mode = "heuristic"
        ai_insights = None
        if employee_records:
            try:
                sample_emp = employee_records[0]
                ai_service = SkillAIService(employee_repo, skill_repo)
                emp_data = {
                    "employee_id": sample_emp.employee_id,
                    "department": sample_emp.department,
                    "skills": sample_emp.skills or [],
                    "metadata": (sample_emp.meta_data or {}) if hasattr(sample_emp, "meta_data") else (getattr(sample_emp, "metadata", None) or {}),
                }
                ai_analysis = await ai_service.analyze_employee(
                    session,
                    sample_emp.employee_id,
                    emp_data,
                    None
                )
                analysis_mode = ai_analysis.get("ai_mode", "heuristic")
                if analysis_mode == "live" or analysis_mode == "featherless":
                    ai_mode = "featherless"
                    ai_insights = extract_ai_insights(ai_analysis)
            except Exception:
                pass
        
        score = compose_unified_score(
            skill_scores={"skill_coverage": min(100, len(global_analytics.get("skill_frequency", {})))},
            gap_scores={"department_load": len(departments) * 5},
            role_fit_score=82,
            next_role_readiness=78,
            risk_score=20,
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/dashboard/overview",
        )
        payload = {**overview, "unified_score": score.model_dump()}
        global_cache.set("dashboard_overview", "overview", payload)
        return unified_success(payload, "Dashboard overview retrieved successfully")
    except Exception as exc:
        logger.error(f"Error getting dashboard overview: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get dashboard overview: {str(exc)}",
            status_code=500
        )


@router.get("/skill-map", responses=ERROR_RESPONSES)
async def get_skill_map(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep
):
    """Get skill map visualization data."""
    try:
        ontology = await _load_latest_ontology()

        employee_records = await employee_repo.get_all_employees(session)
        distribution = _get_employee_skill_distribution(employee_records)

        skill_map = {
            "ontology": ontology,
            "employee_distribution": distribution,
        }
        
        # Try to get AI insights
        from swx_api.app.services.skill_ai_service import SkillAIService
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_mode = "heuristic"
        ai_insights = None
        if employee_records:
            try:
                sample_emp = employee_records[0]
                ai_service = SkillAIService(employee_repo, skill_repo)
                emp_data = {
                    "employee_id": sample_emp.employee_id,
                    "department": sample_emp.department,
                    "skills": sample_emp.skills or [],
                    "metadata": (sample_emp.meta_data or {}) if hasattr(sample_emp, "meta_data") else (getattr(sample_emp, "metadata", None) or {}),
                }
                ai_analysis = await ai_service.analyze_employee(
                    session,
                    sample_emp.employee_id,
                    emp_data,
                    None
                )
                analysis_mode = ai_analysis.get("ai_mode", "heuristic")
                if analysis_mode == "live" or analysis_mode == "featherless":
                    ai_mode = "featherless"
                    ai_insights = extract_ai_insights(ai_analysis)
            except Exception:
                pass
        
        score = compose_unified_score(
            skill_scores=ranking_dict(list(distribution.keys())[:3]),
            gap_scores={"skills_tracked": len(distribution)},
            role_fit_score=80,
            next_role_readiness=75,
            risk_score=25,
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/dashboard/skill-map",
        )
        payload = {**skill_map, "unified_score": score.model_dump()}

        return unified_success(
            data=payload,
            message="Skill map retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting skill map: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get skill map: {str(exc)}",
            status_code=500
        )


@router.get("/heatmap", responses=ERROR_RESPONSES)
async def get_skill_heatmap(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    department_name: Optional[str] = None
):
    """Get skill heatmap data."""
    try:
        cache_key = (department_name or "global").lower()
        cached = global_cache.get("dashboard_heatmap", cache_key)
        if cached:
            return unified_success(cached, "Skill heatmap retrieved successfully")

        if department_name:
            employee_records = await employee_repo.get_by_department(session, department_name)
        else:
            employee_records = await employee_repo.get_all_employees(session)

        department_data = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in employee_records
        ]

        if department_name:
            analytics = await analytics_service.analyze_department(department_name, department_data)
            heatmap_data = analytics.get("team_skill_heatmap", {})
            shortages = analytics.get("skill_shortages", [])
        else:
            global_analytics = await analytics_service.analyze_global(department_data)
            heatmap_data = global_analytics.get("skill_frequency", {})
            shortages = []

        score = compose_unified_score(
            skill_scores=ranking_dict(list(heatmap_data.keys())[:3]),
            gap_scores={"open_spots": len(shortages) * 5},
            role_fit_score=78,
            next_role_readiness=74,
            risk_score=25 if not department_name else 35,
        )
        payload = {"heatmap_data": heatmap_data, "unified_score": score.model_dump()}
        global_cache.set("dashboard_heatmap", cache_key, payload)

        return unified_success(
            data=payload,
            message="Skill heatmap retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting heatmap: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get heatmap: {str(exc)}",
            status_code=500
        )


@router.get("/trends", responses=ERROR_RESPONSES)
async def get_skill_trends(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    period_months: int = 6
):
    """Get skill trends over time."""
    try:
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

        trends = await analytics_service.analyze_trends(all_employees, period_months=period_months)
        score = compose_unified_score(
            skill_scores={"trend_strength": min(100, len(trends.get("top_growing_skills", [])) * 5)},
            gap_scores={"period_months": period_months * 2},
            role_fit_score=76,
            next_role_readiness=72,
            risk_score=30,
        )
        payload = {"trends": trends, "unified_score": score.model_dump()}

        return unified_success(
            data=payload,
            message="Skill trends retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting trends: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get trends: {str(exc)}",
            status_code=500
        )


@router.get("/instant-overview", responses=ERROR_RESPONSES)
async def get_instant_overview(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep
):
    """Provide cached instant overview for demos."""
    cached = global_cache.get("dashboard_instant", "org")
    if cached:
        return unified_success(cached, "Instant overview retrieved successfully")

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
    if not all_employees:
        return unified_error("NotFound", "No employee records available", status_code=404)

    total_employees = len(all_employees)
    department_groups = _group_by_department(all_employees)
    global_analytics = await analytics_service.analyze_global(all_employees)

    top_shortages: list[str] = []
    heatmap_matrix: Dict[str, Dict[str, int]] = {}
    department_risk_summary: Dict[str, Dict[str, float]] = {}

    for dept, members in department_groups.items():
        dept_analytics = await analytics_service.analyze_department(dept, members)
        heatmap_matrix[dept] = dept_analytics.get("team_skill_heatmap", {})
        department_risk_summary[dept] = dept_analytics.get("risk_scores", {})
        top_shortages.extend(dept_analytics.get("skill_shortages", []))

    unique_shortages = list(dict.fromkeys(top_shortages))[:5]
    strong_skills = list(global_analytics.get("skill_frequency", {}).keys())[:5]
    ontology = await _load_latest_ontology()
    dataset_metadata = await _latest_dataset_metadata()

    avg_skills = mean(len(emp["skills"]) for emp in all_employees if emp["skills"]) if all_employees else 0
    readiness_score = min(100, int(avg_skills * 10))
    next_role_summary = {
        "average_skills_per_employee": round(avg_skills, 2),
        "readiness_score": readiness_score,
        "recommended_focus": "Cross-train battery and autonomy squads" if readiness_score < 80 else "Expand leadership pipeline",
    }

    payload = {
        "total_employees": total_employees,
        "total_departments": len(department_groups),
        "global_skill_distribution": global_analytics.get("skill_frequency", {}),
        "top_skill_shortages": unique_shortages,
        "top_strong_skills": strong_skills,
        "department_risk_summary": department_risk_summary,
        "skill_heatmap_matrix": heatmap_matrix,
        "ontology_overview": {
            "skill_count": len(ontology.get("skills", [])),
            "cluster_count": len(ontology.get("clusters", [])),
            "departments": len(ontology.get("department_skill_map", {})),
        },
        "next_role_readiness": next_role_summary,
        "dataset_metadata": dataset_metadata,
    }

    # Try to get AI insights
    from swx_api.app.services.skill_ai_service import SkillAIService
    from swx_api.app.utils.scoring import extract_ai_insights
    ai_mode = "heuristic"
    ai_insights = None
    if employee_records:
        try:
            sample_emp = employee_records[0]
            ai_service = SkillAIService(employee_repo, skill_repo)
            emp_data = {
                "employee_id": sample_emp.employee_id,
                "department": sample_emp.department,
                "skills": sample_emp.skills or [],
                "metadata": sample_emp.metadata or {},
            }
            ai_analysis = await ai_service.analyze_employee(
                session,
                sample_emp.employee_id,
                emp_data,
                None
            )
            if ai_analysis.get("ai_mode") == "live":
                ai_mode = "featherless"
                ai_insights = extract_ai_insights(ai_analysis)
        except Exception:
            pass
    
    score = compose_unified_score(
        skill_scores=ranking_dict(strong_skills),
        gap_scores={"shortages": len(unique_shortages) * 5},
        role_fit_score=readiness_score,
        next_role_readiness=readiness_score,
        risk_score=30 if readiness_score >= 70 else 45,
        ai_insights=ai_insights,
        ai_mode=ai_mode,
        endpoint="/dashboard/instant-overview",
    )
    payload["unified_score"] = score.model_dump()

    global_cache.set("dashboard_instant", "org", payload)
    return unified_success(payload, "Instant overview retrieved successfully")


def _get_employee_skill_distribution(employee_records: list) -> dict:
    """Get skill distribution across employees."""
    from collections import Counter
    
    skill_counter = Counter()
    for emp in employee_records:
        if emp.skills:
            skill_counter.update(emp.skills)
    
    return {
        skill: count for skill, count in skill_counter.most_common(50)
    }
