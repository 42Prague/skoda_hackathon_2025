"""
Škoda Scoring Engine
--------------------
Scoring with qualification, role-family similarity, learning effort, skill freshness, org hierarchy weighting.
"""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from swx_api.app.schemas.common_schemas import UnifiedScoreModel
from swx_api.core.middleware.logging_middleware import logger


def _clamp(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _to_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            sanitized = value.replace("Z", "+00:00") if value.endswith("Z") else value
            return datetime.fromisoformat(sanitized)
        except ValueError:
            return None
    return None


def calculate_qualification_score(
    employee_qualifications: List[Dict[str, Any]],
    required_qualifications: List[str],
    current_date: Optional[datetime] = None
) -> int:
    """Calculate qualification score (0-100)."""
    if not required_qualifications:
        return 100
    
    if not employee_qualifications:
        return 0
    
    current_date = current_date or datetime.utcnow()
    filtered_quals = []
    for qual in employee_qualifications:
        expiry = _to_datetime(qual.get("expiry_date"))
        status = qual.get("status", "active")
        if status != "active" and (not expiry or expiry < current_date):
            continue
        if expiry and expiry < current_date:
            continue
        filtered_quals.append(qual)
    
    employee_qual_ids = {q.get("qualification_id") for q in filtered_quals}
    required_set = set(required_qualifications)
    
    matched = len(employee_qual_ids & required_set)
    score = int((matched / len(required_set)) * 100) if required_set else 100
    
    fm_bonus = sum(1 for q in filtered_quals if q.get("fm_number"))
    return _clamp(score + min(10, fm_bonus * 2))


def calculate_role_family_similarity(
    employee_job_family_id: Optional[str],
    target_job_family_id: Optional[str]
) -> int:
    """Calculate role-family similarity score (0-100)."""
    if not target_job_family_id:
        return 70
    
    if not employee_job_family_id:
        return 30
    
    if employee_job_family_id == target_job_family_id:
        return 100
    
    employee_prefix = employee_job_family_id.split("_")[0] if "_" in employee_job_family_id else employee_job_family_id
    target_prefix = target_job_family_id.split("_")[0] if "_" in target_job_family_id else target_job_family_id
    
    if employee_prefix == target_prefix:
        return 75
    
    return 40


def calculate_learning_effort_score(
    course_history: List[Dict[str, Any]],
    historical_snapshots: List[Dict[str, Any]],
    years_back: int = 12
) -> int:
    """Calculate learning effort score based on 12 years of history."""
    if not course_history and not historical_snapshots:
        return 30
    
    cutoff_date = datetime.now() - timedelta(days=years_back * 365)
    
    completed_courses = [
        c for c in course_history
        if c.get("completion_status") == "completed"
    ]
    
    total_hours = sum(c.get("hours", 0) for c in completed_courses if c.get("hours"))
    verified_minutes = sum(c.get("verified_minutes", 0) or 0 for c in completed_courses)
    estimated_minutes = sum(c.get("estimated_minutes", 0) or 0 for c in completed_courses)
    verified_hours = (verified_minutes / 60.0) if verified_minutes else 0.0
    estimated_hours = (estimated_minutes / 60.0) if estimated_minutes else 0.0
    
    if historical_snapshots:
        skill_growth = _calculate_skill_growth(historical_snapshots, cutoff_date)
    else:
        skill_growth = 0
    
    hours_score = min(100, int((total_hours + verified_hours + estimated_hours) / 10))
    growth_score = min(100, skill_growth * 10)
    rating_average = 0.0
    rated_courses = [c for c in completed_courses if c.get("user_rating")]
    if rated_courses:
        rating_average = sum(c.get("user_rating", 0) for c in rated_courses) / len(rated_courses)
    rating_bonus = min(10, rating_average * 2)
    verified_bonus = min(20, verified_hours * 2)
    
    score = (hours_score * 0.45) + (growth_score * 0.25) + rating_bonus + verified_bonus
    
    return _clamp(score)


def _calculate_skill_growth(historical_snapshots: List[Dict[str, Any]], cutoff_date: datetime) -> float:
    """Calculate skill growth over time."""
    if len(historical_snapshots) < 2:
        return 0.0
    
    sorted_snapshots = sorted(
        historical_snapshots,
        key=lambda s: s.get("snapshot_date", datetime.min) if isinstance(s.get("snapshot_date"), datetime) else datetime.min
    )
    
    filtered_snapshots = [
        s for s in sorted_snapshots
        if isinstance(s.get("snapshot_date"), datetime) and s.get("snapshot_date") >= cutoff_date
    ]
    
    if len(filtered_snapshots) < 2:
        return 0.0
    
    first_skills = len(filtered_snapshots[0].get("skills", []))
    last_skills = len(filtered_snapshots[-1].get("skills", []))
    
    if first_skills == 0:
        return 1.0 if last_skills > 0 else 0.0
    
    growth = (last_skills - first_skills) / first_skills
    return max(0.0, min(1.0, growth))


def calculate_skill_freshness_score(
    skills: List[str],
    course_history: List[Dict[str, Any]]
) -> int:
    """Calculate skill freshness score (decay over time)."""
    if not skills:
        return 0
    
    if not course_history:
        return 50
    
    skill_freshness_scores = []
    
    for skill in skills:
        skill_lower = skill.lower()
        
        relevant_courses = []
        for course in course_history:
            covered = course.get("skills_covered") or []
            if covered and skill_lower in [s.lower() for s in covered]:
                relevant_courses.append(course)
            elif not covered and course.get("course_name") and skill_lower in course.get("course_name", "").lower():
                relevant_courses.append(course)
        
        if not relevant_courses:
            skill_freshness_scores.append(30)
            continue
        
        def _course_end_dt(course: Dict[str, Any]) -> Optional[datetime]:
            end_value = course.get("end_date")
            if isinstance(end_value, datetime):
                return end_value
            return _to_datetime(end_value)
        
        most_recent = max(
            relevant_courses,
            key=lambda c: _course_end_dt(c) or datetime.min
        )
        
        end_date = _course_end_dt(most_recent)
        if not end_date:
            skill_freshness_scores.append(30)
            continue
        
        days_since = (datetime.now() - end_date).days
        
        if days_since < 90:
            freshness = 1.0
        elif days_since > 730:
            freshness = 0.0
        else:
            freshness = math.exp(-(days_since - 90) / 365)
        
        skill_freshness_scores.append(freshness * 100)
    
    avg_freshness = sum(skill_freshness_scores) / len(skill_freshness_scores) if skill_freshness_scores else 30
    
    return _clamp(avg_freshness)


def calculate_org_hierarchy_weight(
    org_hierarchy: Dict[str, str]
) -> int:
    """Calculate org hierarchy importance weight (0-100)."""
    if not org_hierarchy:
        return 50
    
    levels_filled = sum(1 for i in range(1, 5) if org_hierarchy.get(f"level_{i}"))
    node_id = org_hierarchy.get("node_id")
    leadership_bonus = 10 if node_id and org_hierarchy.get("parent_node_id") else 0
    
    if levels_filled == 4:
        return _clamp(100 + leadership_bonus)
    elif levels_filled == 3:
        return _clamp(80 + leadership_bonus)
    elif levels_filled == 2:
        return _clamp(60 + leadership_bonus)
    elif levels_filled == 1:
        return _clamp(40 + leadership_bonus)
    else:
        return 20


def calculate_career_progression_score(
    historical_snapshots: List[Dict[str, Any]]
) -> int:
    """Calculate career progression score from historical data."""
    if len(historical_snapshots) < 2:
        return 50
    
    sorted_snapshots = sorted(
        historical_snapshots,
        key=lambda s: s.get("snapshot_date", datetime.min) if isinstance(s.get("snapshot_date"), datetime) else datetime.min
    )
    
    promotions = 0
    job_changes = 0
    
    for i in range(1, len(sorted_snapshots)):
        prev = sorted_snapshots[i - 1]
        curr = sorted_snapshots[i]
        
        prev_job_family = prev.get("job_family_id")
        curr_job_family = curr.get("job_family_id")
        
        if prev_job_family != curr_job_family:
            job_changes += 1
            
            prev_skills = len(prev.get("skills", []))
            curr_skills = len(curr.get("skills", []))
            
            if curr_skills > prev_skills:
                promotions += 1
    
    if len(sorted_snapshots) < 2:
        progression_score = 50
    else:
        change_rate = job_changes / (len(sorted_snapshots) - 1)
        promotion_rate = promotions / max(1, job_changes)
        
        progression_score = (change_rate * 30) + (promotion_rate * 70)
    
    return _clamp(progression_score)


def compose_skoda_unified_score(
    employee: Dict[str, Any],
    role_requirements: Dict[str, Any],
    historical_snapshots: List[Dict[str, Any]],
    base_unified_score: Optional[UnifiedScoreModel] = None
) -> UnifiedScoreModel:
    """Compose unified score with Škoda-specific fields."""
    employee_qualifications = employee.get("qualifications", [])
    required_qualifications = role_requirements.get("mandatory_qualifications", [])
    qualification_score = calculate_qualification_score(employee_qualifications, required_qualifications)
    
    employee_job_family_id = employee.get("pers_job_family_id")
    target_job_family_id = role_requirements.get("job_family_id")
    role_family_score = calculate_role_family_similarity(employee_job_family_id, target_job_family_id)
    
    course_history = employee.get("course_history", [])
    learning_effort_score = calculate_learning_effort_score(course_history, historical_snapshots)
    
    skills = employee.get("skills", [])
    skill_freshness_score = calculate_skill_freshness_score(skills, course_history)
    
    org_hierarchy = employee.get("metadata", {}).get("org_hierarchy", {})
    org_hierarchy_weight = calculate_org_hierarchy_weight(org_hierarchy)
    
    career_progression_score = calculate_career_progression_score(historical_snapshots)
    education_alignment = calculate_education_alignment_score(employee, role_requirements)
    planned_role_alignment = calculate_planned_role_alignment(employee, role_requirements)
    
    if base_unified_score:
        base_overall = base_unified_score.overall_score
        base_role_fit = base_unified_score.role_fit_score
        base_readiness = base_unified_score.next_role_readiness
        base_risk = base_unified_score.risk_score
    else:
        base_overall = 70
        base_role_fit = 70
        base_readiness = 70
        base_risk = 30
    
    overall = _clamp(
        (qualification_score * 0.18) +
        (role_family_score * 0.12) +
        (learning_effort_score * 0.14) +
        (skill_freshness_score * 0.15) +
        (org_hierarchy_weight * 0.08) +
        (career_progression_score * 0.13) +
        (education_alignment * 0.1) +
        (planned_role_alignment * 0.1)
    )
    
    role_fit_adjusted = _clamp((base_role_fit * 0.6) + (role_family_score * 0.25) + (planned_role_alignment * 0.15))
    readiness_adjusted = _clamp((base_readiness * 0.5) + (learning_effort_score * 0.3) + (education_alignment * 0.2))
    risk_adjusted = _clamp(base_risk - (education_alignment * 0.1) - (planned_role_alignment * 0.1))
    
    return UnifiedScoreModel(
        overall_score=overall,
        skill_scores=base_unified_score.skill_scores if base_unified_score else {},
        gap_scores={
            **(base_unified_score.gap_scores if base_unified_score else {}),
            "qualification_gap": _clamp(100 - qualification_score),
            "skill_freshness_gap": _clamp(100 - skill_freshness_score),
            "education_gap": _clamp(100 - education_alignment),
            "planned_role_gap": _clamp(100 - planned_role_alignment),
        },
        role_fit_score=role_fit_adjusted,
        next_role_readiness=readiness_adjusted,
        risk_score=risk_adjusted,
        ai_gap_score=base_unified_score.ai_gap_score if base_unified_score else None,
        ai_readiness=base_unified_score.ai_readiness if base_unified_score else None,
        ai_risk_signal=base_unified_score.ai_risk_signal if base_unified_score else None,
        ai_skill_recommendations_count=base_unified_score.ai_skill_recommendations_count if base_unified_score else None,
        ai_mode=base_unified_score.ai_mode if base_unified_score else None
    )


def calculate_education_alignment_score(
    employee: Dict[str, Any],
    role_requirements: Dict[str, Any]
) -> int:
    """Score alignment between employee education and role expectations."""
    employee_category = employee.get("education_category_id")
    required_category = role_requirements.get("education_category_id")
    if not required_category:
        return 70 if employee_category else 50
    if employee_category == required_category:
        return 95
    employee_branch = employee.get("education_branch_id")
    required_branch = role_requirements.get("education_branch_id")
    if employee_branch and required_branch and employee_branch == required_branch:
        return 85
    return 60


def calculate_planned_role_alignment(
    employee: Dict[str, Any],
    role_requirements: Dict[str, Any]
) -> int:
    """Score whether planned role/profession matches desired role."""
    planned_position_id = employee.get("planned_position_id")
    target_position_id = role_requirements.get("planned_position_id")
    if not target_position_id:
        return 70
    if planned_position_id == target_position_id:
        return 100
    planned_profession = employee.get("planned_profession_id")
    target_profession = role_requirements.get("planned_profession_id")
    if planned_profession and target_profession and planned_profession == target_profession:
        return 85
    return 55

