"""
Utility helpers to keep UnifiedScoreModel calculations consistent.
AI-driven scoring: Featherless outputs directly influence all scores.
"""

from __future__ import annotations

from statistics import mean
from typing import Dict, Optional, Sequence, Any

from swx_api.app.schemas.common_schemas import UnifiedScoreModel
from swx_api.core.middleware.logging_middleware import logger


def _clamp(value: float) -> int:
    return max(0, min(100, int(round(value))))


def extract_ai_insights(llm_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract AI insights from LLM analysis result.
    
    Args:
        llm_result: Dictionary from LLM analysis containing:
            - ai_readiness: int (0-100)
            - ai_risk_signal: int (0-100)
            - ai_gap_score: int (0-100)
            - missing_skills: List[str]
            - strengths: List[str]
            - analysis_summary: str (may contain warning signals)
    
    Returns:
        Dictionary with extracted AI insights:
        - ai_readiness: int
        - ai_risk: int
        - ai_missing_skills: List[str]
        - ai_strength_signals: List[str]
        - ai_warning_signals: List[str]
    """
    ai_readiness = int(llm_result.get("ai_readiness", llm_result.get("gap_score", 65)))
    ai_risk = int(llm_result.get("ai_risk_signal", max(0, 100 - ai_readiness)))
    ai_missing_skills = llm_result.get("missing_skills", [])
    ai_strength_signals = llm_result.get("strengths", [])
    
    # Extract warning signals from analysis summary
    ai_warning_signals = []
    summary = llm_result.get("analysis_summary", "").lower()
    warning_keywords = ["risk", "concern", "warning", "critical", "urgent", "gap", "missing", "lack"]
    if any(keyword in summary for keyword in warning_keywords):
        # Extract sentences with warnings
        sentences = summary.split(".")
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in warning_keywords):
                ai_warning_signals.append(sentence.strip())
    
    return {
        "ai_readiness": ai_readiness,
        "ai_risk": ai_risk,
        "ai_missing_skills": ai_missing_skills,
        "ai_strength_signals": ai_strength_signals,
        "ai_warning_signals": ai_warning_signals,
    }


def compose_unified_score(
    *,
    skill_scores: Dict[str, int],
    gap_scores: Dict[str, int],
    role_fit_score: int,
    next_role_readiness: int,
    risk_score: int,
    ai_gap_score: Optional[int] = None,
    ai_readiness: Optional[int] = None,
    ai_risk_signal: Optional[int] = None,
    ai_skill_recommendations_count: Optional[int] = None,
    ai_insights: Optional[Dict[str, Any]] = None,
    ai_mode: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> UnifiedScoreModel:
    """
    Compose a normalized UnifiedScoreModel with AI-driven scoring.
    
    AI insights directly influence all scores:
    - readiness: +15 if AI readiness > 75, -20 if < 50
    - risk: +25 if AI risk > 60, -30 if < 30
    - role_fit: +10 if AI indicates strong match
    - gaps: adjusted based on AI missing skills count
    
    Args:
        skill_scores: Base skill scores
        gap_scores: Base gap scores
        role_fit_score: Base role fit score
        next_role_readiness: Base readiness score
        risk_score: Base risk score
        ai_gap_score: AI gap score (legacy)
        ai_readiness: AI readiness score (legacy)
        ai_risk_signal: AI risk signal (legacy)
        ai_skill_recommendations_count: AI recommendations count
        ai_insights: Extracted AI insights from extract_ai_insights()
        ai_mode: "featherless" | "heuristic" | None
        endpoint: Endpoint name for logging
    """
    # Start with base scores
    base_avg_skill = mean(skill_scores.values()) if skill_scores else 70
    base_avg_gap = mean(gap_scores.values()) if gap_scores else 70
    base_role_fit = role_fit_score
    base_readiness = next_role_readiness
    base_risk = risk_score
    
    # Apply AI modifiers if AI insights are available
    ai_modifiers_applied = False
    if ai_insights:
        ai_readiness_val = ai_insights.get("ai_readiness")
        ai_risk_val = ai_insights.get("ai_risk")
        ai_missing_count = len(ai_insights.get("ai_missing_skills", []))
        ai_strength_count = len(ai_insights.get("ai_strength_signals", []))
        ai_warning_count = len(ai_insights.get("ai_warning_signals", []))
        
        # Modifier 1: Readiness adjustment
        if ai_readiness_val is not None:
            if ai_readiness_val > 75:
                base_readiness = _clamp(base_readiness + 15)
            elif ai_readiness_val < 50:
                base_readiness = _clamp(base_readiness - 20)
            else:
                # Use AI readiness directly if available
                base_readiness = ai_readiness_val
        
        # Modifier 2: Risk adjustment
        if ai_risk_val is not None:
            if ai_risk_val > 60:
                base_risk = _clamp(base_risk + 25)
            elif ai_risk_val < 30:
                base_risk = _clamp(max(0, base_risk - 30))
            else:
                # Use AI risk directly if available
                base_risk = ai_risk_val
        
        # Modifier 3: Role fit adjustment (if AI indicates strong match)
        if ai_strength_count >= 3 and ai_missing_count <= 2:
            base_role_fit = _clamp(base_role_fit + 10)
        
        # Modifier 4: Gap scores based on AI missing skills
        if ai_missing_count > 0:
            gap_adjustment = min(30, ai_missing_count * 5)
            base_avg_gap = _clamp(base_avg_gap - gap_adjustment)
            # Add gap entry for AI missing skills
            gap_scores = {**gap_scores, "ai_missing_skills": gap_adjustment}
        
        # Modifier 5: Warning signals increase risk
        if ai_warning_count > 0:
            base_risk = _clamp(base_risk + (ai_warning_count * 5))
        
        ai_modifiers_applied = True
    
    # Fallback to legacy AI fields if insights not provided
    if not ai_insights and (ai_readiness is not None or ai_risk_signal is not None):
        if ai_readiness is not None:
            if ai_readiness > 75:
                base_readiness = _clamp(base_readiness + 15)
            elif ai_readiness < 50:
                base_readiness = _clamp(base_readiness - 20)
            else:
                base_readiness = ai_readiness
        
        if ai_risk_signal is not None:
            if ai_risk_signal > 60:
                base_risk = _clamp(base_risk + 25)
            elif ai_risk_signal < 30:
                base_risk = _clamp(max(0, base_risk - 30))
            else:
                base_risk = ai_risk_signal
        
        ai_modifiers_applied = True
    
    # Calculate overall score with AI-adjusted values
    stability_bonus = 100 - base_risk
    overall = _clamp(
        (base_avg_skill * 0.4)
        + (base_avg_gap * 0.1)
        + (base_role_fit * 0.2)
        + (base_readiness * 0.2)
        + (stability_bonus * 0.1)
    )
    
    # Log AI scoring modifiers if applied
    if ai_modifiers_applied and endpoint:
        logger.info(f"[AI] Using Featherless scoring modifiers for {endpoint}")
    
    # Use AI values directly if available (overwrite heuristics)
    final_ai_readiness = ai_insights.get("ai_readiness") if ai_insights else ai_readiness
    final_ai_risk = ai_insights.get("ai_risk") if ai_insights else ai_risk_signal
    final_ai_gap = ai_gap_score
    
    return UnifiedScoreModel(
        overall_score=overall,
        skill_scores={k: _clamp(v) for k, v in skill_scores.items()},
        gap_scores={k: _clamp(v) for k, v in gap_scores.items()},
        role_fit_score=_clamp(base_role_fit),
        next_role_readiness=_clamp(base_readiness),
        risk_score=_clamp(base_risk),
        ai_gap_score=_clamp(final_ai_gap) if final_ai_gap is not None else None,
        ai_readiness=_clamp(final_ai_readiness) if final_ai_readiness is not None else None,
        ai_risk_signal=_clamp(final_ai_risk) if final_ai_risk is not None else None,
        ai_skill_recommendations_count=ai_skill_recommendations_count,
    )


def ranking_dict(items: Sequence[str], base: int = 85) -> Dict[str, int]:
    """Generate descending scores for ordered skill lists."""
    return {item: _clamp(base - idx * 3) for idx, item in enumerate(items)}

