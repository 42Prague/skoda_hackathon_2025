"""
AI Response Schemas
------------------
Pydantic schemas for all AI service responses.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AISkillExtraction(BaseModel):
    """Schema for skill extraction AI response."""
    extracted_skills: List[str] = Field(default_factory=list)
    normalized_skills: List[str] = Field(default_factory=list)
    proficiency_levels: Dict[str, str] = Field(default_factory=dict)
    ontology_matches: Dict[str, str] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AIQualificationNormalization(BaseModel):
    """Schema for qualification normalization AI response."""
    qualification_id: str = ""
    name_cz: str = ""
    name_en: str = ""
    type: str = ""
    mandatory_for_roles: List[str] = Field(default_factory=list)
    expiry_required: bool = False
    normalized: bool = False
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AIEmployeeSummary(BaseModel):
    """Schema for employee summary AI response."""
    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    development_areas: List[str] = Field(default_factory=list)
    readiness_score: int = Field(default=0, ge=0, le=100)
    next_role_readiness: str = ""
    recommended_actions: List[str] = Field(default_factory=list)
    risk_signals: List[str] = Field(default_factory=list)
    career_trajectory: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AITeamSummary(BaseModel):
    """Schema for team summary AI response."""
    summary: str = ""
    team_strengths: List[str] = Field(default_factory=list)
    critical_gaps: List[str] = Field(default_factory=list)
    health_score: int = Field(default=0, ge=0, le=100)
    risk_level: str = ""
    recommendations: List[str] = Field(default_factory=list)
    skill_distribution: Dict[str, int] = Field(default_factory=dict)
    readiness_breakdown: Dict[str, int] = Field(default_factory=dict)
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AIRoleFitSummary(BaseModel):
    """Schema for role fit AI response."""
    fit_score: int = Field(default=0, ge=0, le=100)
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    readiness_timeline: str = ""
    development_path: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendation: str = ""
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AISuccessionSummary(BaseModel):
    """Schema for succession analysis AI response."""
    pipeline_assessment: str = ""
    top_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    readiness_gaps: List[str] = Field(default_factory=list)
    vacancy_risk: int = Field(default=0, ge=0, le=100)
    pipeline_strength: int = Field(default=0, ge=0, le=100)
    development_priorities: List[str] = Field(default_factory=list)
    succession_timeline: str = ""
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AIForecastExplanation(BaseModel):
    """Schema for forecast explanation AI response."""
    explanation: str = ""
    key_trends: List[str] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    summary: str = ""
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AIRiskSignals(BaseModel):
    """Schema for risk signals AI response."""
    risk_signals: List[str] = Field(default_factory=list)
    risk_score: int = Field(default=0, ge=0, le=100)
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_recommendations: List[str] = Field(default_factory=list)
    priority: str = ""
    timeline: str = ""
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AICareerCoach(BaseModel):
    """Schema for career coach AI response."""
    career_assessment: str = ""
    career_paths: List[Dict[str, Any]] = Field(default_factory=list)
    development_plan: List[str] = Field(default_factory=list)
    recommended_training: List[str] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AITrainingPlan(BaseModel):
    """Schema for training plan AI response."""
    training_plan: str = ""
    recommended_courses: List[Dict[str, Any]] = Field(default_factory=list)
    skill_gaps_addressed: List[str] = Field(default_factory=list)
    estimated_duration: str = ""
    expected_outcomes: List[str] = Field(default_factory=list)
    next_courses: List[str] = Field(default_factory=list)
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"


class AIDepartmentComparison(BaseModel):
    """Schema for department comparison AI response."""
    comparison_summary: str = ""
    department1_strengths: List[str] = Field(default_factory=list)
    department2_strengths: List[str] = Field(default_factory=list)
    skill_overlap: List[str] = Field(default_factory=list)
    talent_transfer_opportunities: List[str] = Field(default_factory=list)
    risk_comparison: Dict[str, int] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    relative_performance: Dict[str, int] = Field(default_factory=dict)
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommended_actions: List[str] = Field(default_factory=list)
    detected_language: str = "en"
    ai_mode: str = "azure"

