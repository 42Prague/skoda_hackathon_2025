"""
Skill Coach Analytics Routes (Controllers)
------------------------------------------
API endpoints for analytics - interface layer only.
All business logic and DB access handled by services and repositories.
"""

import logging
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from swx_api.app.schemas.analytics_schemas import (
    DepartmentNarrativeResponse,
    SuccessionRadarResponse,
)
from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.skill_ai_service import SkillAIService
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.services.skill_recommendations_service import SkillRecommendationsService
from swx_api.app.utils.cache import global_cache
from swx_api.app.utils.scoring import compose_unified_score, ranking_dict
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.app.utils.dependencies import EmployeeRepoDep, SkillRepoDep
from swx_api.core.database.db import AsyncSessionDep

logger = logging.getLogger("skill_analytics_routes")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/analytics")
analytics_service = SkillAnalyticsService()


@router.get("/employees/{employee_id}", responses=ERROR_RESPONSES)
async def get_employee_analytics(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    employee_id: str
):
    """Get employee-level analytics."""
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
        
        # Use async analytics service
        analytics = await analytics_service.analyze_employee(
            employee_record.employee_id,
            employee_data
        )
        
        # Get AI analysis for this employee
        from swx_api.app.services.skill_ai_service import SkillAIService
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_service = SkillAIService(employee_repo, skill_repo)
        try:
            ai_analysis = await ai_service.analyze_employee(
                session,
                employee_id,
                employee_data,
                None
            )
            ai_mode = ai_analysis.get("ai_mode", "heuristic")
            # Map "live" to "featherless" for consistency
            if ai_mode == "live":
                ai_mode = "featherless"
            ai_insights = extract_ai_insights(ai_analysis) if ai_mode == "featherless" else None
        except Exception:
            ai_mode = "heuristic"
            ai_insights = None
        
        skill_stats = analytics.get("skill_level_stats", {})
        skill_scores = {
            "skill_diversity": min(100, skill_stats.get("skill_diversity", 0) * 10),
            "total_skills": min(100, skill_stats.get("total_skills", 0) * 5),
        }
        score = compose_unified_score(
            skill_scores=skill_scores,
            gap_scores={"stagnation": 40 if analytics.get("stagnation_detected") else 80},
            role_fit_score=analytics.get("readiness_score", 70),
            next_role_readiness=analytics.get("readiness_score", 70),
            risk_score=65 if analytics.get("stagnation_detected") else 25,
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/analytics/employees",
        )

        payload = {
            "analytics": analytics,
            "unified_score": score.model_dump(),
        }

        return unified_success(
            data=payload,
            message="Employee analytics retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting employee analytics: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get employee analytics: {str(exc)}",
            status_code=500
        )


@router.get("/departments/{department_name}", responses=ERROR_RESPONSES)
async def get_department_analytics(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    department_name: str
):
    """Get department-level analytics."""
    try:
        # Get all employees in department using async repository
        employee_records = await employee_repo.get_by_department(session, department_name)
        
        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Department not found: {department_name}",
                status_code=404
            )
        
        department_data = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in employee_records
        ]
        
        cache_key = department_name.lower()
        cached = global_cache.get("analytics_department", cache_key)
        if cached:
            return unified_success(
                data=cached,
                message="Department analytics retrieved successfully"
            )

        analytics = await analytics_service.analyze_department(
            department_name,
            department_data
        )

        # Get AI insights from department employees (aggregate)
        from swx_api.app.services.skill_ai_service import SkillAIService
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_service = SkillAIService(employee_repo, skill_repo)
        ai_insights_aggregated = None
        ai_mode = "heuristic"
        
        # Sample first few employees for AI insights
        for emp_data in department_data[:3]:
            try:
                ai_analysis = await ai_service.analyze_employee(
                    session,
                    emp_data["employee_id"],
                    emp_data,
                    None
                )
                analysis_mode = ai_analysis.get("ai_mode", "heuristic")
                if analysis_mode == "live" or analysis_mode == "featherless":
                    ai_mode = "featherless"
                    if not ai_insights_aggregated:
                        ai_insights_aggregated = extract_ai_insights(ai_analysis)
                    break
            except Exception:
                continue

        shortages = analytics.get("skill_shortages", [])
        risk_scores = analytics.get("risk_scores", {})
        score = compose_unified_score(
            skill_scores=ranking_dict(list(analytics.get("team_skill_heatmap", {}).keys())[:3]),
            gap_scores={"shortages": len(shortages) * 5},
            role_fit_score=80 - len(shortages) * 2,
            next_role_readiness=85 - len(shortages) * 2,
            risk_score=int(risk_scores.get("skill_concentration_risk", 30)),
            ai_insights=ai_insights_aggregated,
            ai_mode=ai_mode,
            endpoint="/analytics/departments",
        )

        payload = {
            "analytics": analytics,
            "unified_score": score.model_dump(),
        }
        global_cache.set("analytics_department", cache_key, payload)
        
        return unified_success(
            data=payload,
            message="Department analytics retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting department analytics: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get department analytics: {str(exc)}",
            status_code=500
        )


@router.get("/global", responses=ERROR_RESPONSES)
async def get_global_analytics(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep
):
    """Get global analytics across all employees."""
    try:
        cached = global_cache.get("analytics_global", "global")
        if cached:
            return unified_success(
                data=cached,
                message="Global analytics retrieved successfully"
            )

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

        analytics = await analytics_service.analyze_global(all_employees)
        skill_frequency = analytics.get("skill_frequency", {})
        score = compose_unified_score(
            skill_scores=ranking_dict(list(skill_frequency.keys())[:3]),
            gap_scores={"coverage": 100 - min(100, len(skill_frequency))},
            role_fit_score=78,
            next_role_readiness=75,
            risk_score=30,
        )
        payload = {
            "analytics": analytics,
            "unified_score": score.model_dump(),
        }
        global_cache.set("analytics_global", "global", payload)

        return unified_success(
            data=payload,
            message="Global analytics retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting global analytics: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get global analytics: {str(exc)}",
            status_code=500
        )


@router.get(
    "/succession/{department_name}",
    response_model=SuccessionRadarResponse,
    responses=ERROR_RESPONSES,
)
async def get_succession_radar(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    department_name: str
):
    """Return ranked succession readiness for a department."""
    try:
        employee_records = await employee_repo.get_by_department(session, department_name)

        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Department not found: {department_name}",
                status_code=404
            )

        cache_key = department_name.lower()
        cached = global_cache.get("succession_department", cache_key)
        if cached:
            return unified_success(
                data=cached,
                message="Succession radar retrieved successfully"
            )

        department_payload = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (emp.metadata or {}),
            }
            for emp in employee_records
        ]

        department_analytics = await analytics_service.analyze_department(
            department_name,
            department_payload
        )

        snapshot = await _build_succession_snapshot(
            session=session,
            employee_repo=employee_repo,
            skill_repo=skill_repo,
            department_name=department_name,
            employee_records=employee_records,
            department_analytics=department_analytics,
        )

        payload = {
            "department": department_name,
            "generated_at": datetime.utcnow().isoformat(),
            **snapshot,
        }
        global_cache.set("succession_department", cache_key, payload)

        return unified_success(
            data=payload,
            message="Succession radar retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error building succession radar: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to build succession radar: {str(exc)}",
            status_code=500
        )


@router.get(
    "/narrative/{department_name}",
    response_model=DepartmentNarrativeResponse,
    responses=ERROR_RESPONSES,
)
async def get_department_narrative(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    department_name: str
):
    """Return deterministic narrative for a department."""
    try:
        employee_records = await employee_repo.get_by_department(session, department_name)

        if not employee_records:
            return unified_error(
                error_type="NotFound",
                message=f"Department not found: {department_name}",
                status_code=404
            )

        cache_key = department_name.lower()
        cached = global_cache.get("narrative_department", cache_key)
        if cached:
            return unified_success(
                data=cached,
                message="Department narrative retrieved successfully"
            )

        # Reuse succession snapshot when available to keep narratives aligned
        succession_cached = global_cache.get("succession_department", cache_key)

        department_payload = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": (emp.meta_data or {}) if hasattr(emp, "meta_data") else (emp.metadata or {}),
            }
            for emp in employee_records
        ]

        department_analytics = await analytics_service.analyze_department(
            department_name,
            department_payload
        )

        if not succession_cached:
            snapshot = await _build_succession_snapshot(
                session=session,
                employee_repo=employee_repo,
                skill_repo=skill_repo,
                department_name=department_name,
                employee_records=employee_records,
                department_analytics=department_analytics,
            )
            succession_cached = {
                "department": department_name,
                "generated_at": datetime.utcnow().isoformat(),
                **snapshot,
            }
            global_cache.set("succession_department", cache_key, succession_cached)

        narrative_payload = await SkillAIService.generate_department_narrative(
            {
                "department_name": department_name,
                "department_analytics": department_analytics,
                "succession_snapshot": succession_cached,
            }
        )

        global_cache.set("narrative_department", cache_key, narrative_payload)

        return unified_success(
            data=narrative_payload,
            message="Department narrative generated successfully"
        )
    except Exception as exc:
        logger.error(f"Error generating department narrative: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to generate department narrative: {str(exc)}",
            status_code=500
        )


async def _build_succession_snapshot(
    *,
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    skill_repo: SkillRepoDep,
    department_name: str,
    employee_records: List,
    department_analytics: Dict[str, Any],
) -> Dict[str, Any]:
    """Compose reusable succession snapshot payload."""
    ai_service = SkillAIService(employee_repo, skill_repo)
    recommendations_service = SkillRecommendationsService(employee_repo, skill_repo)
    heatmap = department_analytics.get("team_skill_heatmap", {})
    shortages = department_analytics.get("skill_shortages", [])
    risk_scores = department_analytics.get("risk_scores", {})

    ai_gap_scores: List[int] = []
    ai_readiness_scores: List[int] = []
    ai_risk_signals: List[int] = []
    ai_skill_recommendation_counts: List[int] = []

    candidates = []
    for record in employee_records:
        metadata = (record.meta_data or {}) if hasattr(record, "meta_data") else (record.metadata or {})  # type: ignore[attr-defined]
        employee_data = {
            "employee_id": record.employee_id,
            "department": record.department,
            "skills": record.skills or [],
            "metadata": metadata,
        }

        employee_analysis = await analytics_service.analyze_employee(
            record.employee_id,
            employee_data
        )

        ai_analysis = await ai_service.analyze_employee(
            session,
            record.employee_id,
            employee_data,
        )

        rec_result = await recommendations_service.recommend_skills(
            session,
            employee_data,
            {"common_skills": list(heatmap.keys())[:10]} if heatmap else None,
        )
        recommendations = rec_result["items"]
        rec_ai_metrics = rec_result.get("ai_metrics", {})

        strengths = employee_data["skills"][:3] if employee_data["skills"] else ["Multidisciplinary"]
        gaps = [rec["skill"] for rec in recommendations[:3]] or ["Leadership Depth"]
        readiness = ai_analysis.get("ai_readiness", employee_analysis.get("readiness_score", 60))
        next_role_readiness = min(100, readiness + (5 if readiness < 85 else 0))
        risk_score = int(ai_analysis.get("ai_risk_signal", 65 if employee_analysis.get("stagnation_detected") else max(10, 100 - readiness)))

        ai_gap = ai_analysis.get("ai_gap_score", ai_analysis.get("gap_score", 65))
        ai_skill_recs = rec_ai_metrics.get("ai_skill_recommendations_count", ai_analysis.get("ai_skill_recommendations_count", len(gaps)))

        ai_gap_scores.append(int(ai_gap))
        ai_readiness_scores.append(int(readiness))
        ai_risk_signals.append(risk_score)
        ai_skill_recommendation_counts.append(int(ai_skill_recs))

        # Extract AI insights for this candidate
        from swx_api.app.utils.scoring import extract_ai_insights
        ai_mode = ai_analysis.get("ai_mode", "heuristic")
        # Map "live" to "featherless" for consistency
        if ai_mode == "live":
            ai_mode = "featherless"
        ai_insights = extract_ai_insights(ai_analysis) if ai_mode == "featherless" else None

        candidate_score = compose_unified_score(
            skill_scores=ranking_dict(strengths),
            gap_scores=ranking_dict(gaps, base=70),
            role_fit_score=readiness,
            next_role_readiness=next_role_readiness,
            risk_score=risk_score,
            ai_gap_score=int(ai_gap),
            ai_readiness=int(readiness),
            ai_risk_signal=risk_score,
            ai_skill_recommendations_count=int(ai_skill_recs),
            ai_insights=ai_insights,
            ai_mode=ai_mode,
            endpoint="/analytics/succession",
        )

        candidates.append({
            "employee_id": record.employee_id,
            "name": metadata.get("full_name") or metadata.get("name") or record.employee_id,
            "department": department_name,
            "readiness_score": readiness,
            "next_role_readiness": next_role_readiness,
            "risk_score": risk_score,
            "skill_strengths": strengths,
            "skill_gaps": gaps,
            "unified_score": candidate_score.model_dump(),
            "metadata": metadata,
            "ai_metadata": {
                "mode": ai_analysis.get("ai_mode"),
                "provider": ai_analysis.get("ai_provider"),
                "gap_score": int(ai_gap),
                "readiness": int(readiness),
                "risk_signal": risk_score,
                "skill_recommendations": int(ai_skill_recs),
            },
        })

    candidates.sort(key=lambda item: item["next_role_readiness"], reverse=True)

    # Aggregate AI insights for department
    ai_mode = "featherless" if any(c.get("ai_metadata", {}).get("mode") in ("live", "featherless") for c in candidates) else "heuristic"
    aggregated_ai_insights = None
    if ai_mode == "featherless" and candidates:
        # Use first candidate's AI insights as representative
        first_candidate_ai = candidates[0].get("ai_metadata", {})
        if first_candidate_ai.get("mode") in ("live", "featherless"):
            # Reconstruct insights from aggregated scores
            aggregated_ai_insights = {
                "ai_readiness": int(mean(ai_readiness_scores)) if ai_readiness_scores else None,
                "ai_risk": int(mean(ai_risk_signals)) if ai_risk_signals else None,
                "ai_missing_skills": list(set([g for c in candidates for g in c.get("skill_gaps", [])]))[:10],
                "ai_strength_signals": list(set([s for c in candidates for s in c.get("skill_strengths", [])]))[:10],
                "ai_warning_signals": [],
            }
    
    department_score = compose_unified_score(
        skill_scores=ranking_dict(list(heatmap.keys())[:3]),
        gap_scores={"shortages": len(shortages) * 4},
        role_fit_score=80 - len(shortages) * 2,
        next_role_readiness=82 - len(shortages) * 2,
        risk_score=int(risk_scores.get("skill_concentration_risk", 30)),
        ai_gap_score=int(mean(ai_gap_scores)) if ai_gap_scores else None,
        ai_readiness=int(mean(ai_readiness_scores)) if ai_readiness_scores else None,
        ai_risk_signal=int(mean(ai_risk_signals)) if ai_risk_signals else None,
        ai_skill_recommendations_count=sum(ai_skill_recommendation_counts) if ai_skill_recommendation_counts else None,
        ai_insights=aggregated_ai_insights,
        ai_mode=ai_mode,
        endpoint="/analytics/succession",
    )

    pipeline_summary = {
        "ready_now": sum(1 for c in candidates if c["next_role_readiness"] >= 80),
        "ready_soon": sum(1 for c in candidates if 65 <= c["next_role_readiness"] < 80),
        "developing": sum(1 for c in candidates if c["next_role_readiness"] < 65),
    }
    pipeline_summary["narrative"] = (
        f"{pipeline_summary['ready_now']} ready-now, {pipeline_summary['ready_soon']} ready-soon, "
        f"{pipeline_summary['developing']} developing."
    )
    pipeline_summary["risk_outlook"] = _risk_level_from_score(department_score.risk_score)

    return {
        "candidate_count": len(candidates),
        "pipeline_summary": pipeline_summary,
        "unified_score": department_score.model_dump(),
        "candidates": candidates,
    }


def _risk_level_from_score(score: int) -> str:
    """Map numeric risk to semantic level."""
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"
