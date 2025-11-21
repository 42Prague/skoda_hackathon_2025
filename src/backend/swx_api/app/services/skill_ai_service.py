"""
Async AI Skill Analysis Engine
-------------------------------
Uses async LLM client to analyze employee skills, detect gaps,
and generate development paths.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.repositories.skill_repository import SkillAnalysisRepository
from swx_api.app.models.skill_models import SkillAnalysisRecord
from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.ai.ai_employee_service import AIEmployeeService
from swx_api.app.utils.scoring import compose_unified_score, ranking_dict
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("skill_ai")


class SkillAIService:
    """Async AI-powered skill analysis service."""
    
    def __init__(
        self, 
        employee_repo: EmployeeRepository,
        skill_repo: SkillAnalysisRepository
    ):
        """
        Initialize service with repositories.
        
        Args:
            employee_repo: Employee repository
            skill_repo: Skill analysis repository
        """
        self.employee_repo = employee_repo
        self.skill_repo = skill_repo
        self.llm_config = LLMConfig.from_env()
        self.provider = self.llm_config.provider
        self.ai_employee_service = AIEmployeeService()
    
    async def analyze_employee(
        self,
        session: AsyncSession,
        employee_id: str,
        employee_data: Dict[str, Any],
        role_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze employee skills using AI.
        
        Args:
            session: Async database session
            employee_id: Employee identifier
            employee_data: Employee data including skills, department, etc.
            role_requirements: Optional role requirements for comparison
            
        Returns:
            Analysis result with:
            - current_skills: List of current skills
            - missing_skills: List of missing skills
            - gap_score: Integer 0-100
            - strengths: List of strengths
            - recommended_roles: List of recommended roles
            - development_path: List of development steps
            - analysis_summary: Text summary
        """
        try:
            llm_employee_data = {
                "employee_id": employee_id,
                "department": employee_data.get("department", "Unknown"),
                "skills": employee_data.get("skills", []),
                "experience_years": employee_data.get("experience_years"),
                "current_role": employee_data.get("current_role"),
            }

            async with LLMClient(self.llm_config) as llm:
                analysis = await llm.analyze_skills(llm_employee_data, role_requirements)

            analysis["employee_id"] = employee_id
            enriched = self._decorate_analysis(analysis, mode="live")

            try:
                record = SkillAnalysisRecord(
                    employee_id=employee_id,
                    analysis_json=enriched,
                    recommendations_json=enriched.get("recommended_roles"),
                )
                await self.skill_repo.create(session, record)
            except Exception as db_error:
                logger.warning(f"Database insert failed: {db_error}")

            return enriched

        except Exception as exc:
            logger.error(f"Error analyzing employee {employee_id}: {exc}", exc_info=True)
            fallback = self._fallback_analysis(employee_data, role_requirements)
            fallback["employee_id"] = employee_id
            return self._decorate_analysis(
                fallback,
                mode="heuristic_fallback",
                error=str(exc),
            )
    
    def detect_skill_gaps(
        self,
        current_skills: List[str],
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Detect skill gaps between current and required skills.
        
        Args:
            current_skills: List of current skills
            required_skills: List of required skills
            
        Returns:
            Gap analysis with missing skills and gap score
        """
        current_set = set(s.lower() for s in current_skills)
        required_set = set(s.lower() for s in required_skills)
        
        missing_skills = [s for s in required_skills if s.lower() not in current_set]
        
        if not required_skills:
            gap_score = 100
        else:
            gap_score = int((len(required_skills) - len(missing_skills)) / len(required_skills) * 100)
        
        return {
            "missing_skills": missing_skills,
            "gap_score": gap_score,
            "coverage": len(required_skills) - len(missing_skills),
            "total_required": len(required_skills),
        }
    
    def detect_strengths(
        self,
        employee_data: Dict[str, Any],
        department_data: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Detect employee strengths.
        
        Args:
            employee_data: Employee data
            department_data: Optional department-wide data for comparison
            
        Returns:
            List of identified strengths
        """
        skills = employee_data.get("skills", [])
        
        if not skills:
            return []
        
        # If department data available, compare
        if department_data:
            dept_avg_skills = department_data.get("average_skills_count", 0)
            if len(skills) > dept_avg_skills * 1.2:
                return skills[:5]  # Top skills as strengths
        
        # Otherwise, return top skills
        return skills[:5]
    
    def generate_development_path(
        self,
        current_skills: List[str],
        target_skills: List[str],
        time_horizon: str = "6 months"
    ) -> List[str]:
        """
        Generate development path to acquire target skills.
        
        Args:
            current_skills: Current skills
            target_skills: Target skills to acquire
            time_horizon: Time frame for development
            
        Returns:
            List of development steps
        """
        missing = [s for s in target_skills if s.lower() not in [c.lower() for c in current_skills]]
        
        if not missing:
            return ["All target skills already acquired. Focus on mastery and specialization."]
        
        steps = []
        for i, skill in enumerate(missing[:10], 1):  # Limit to 10 skills
            steps.append(f"Step {i}: Learn {skill} - Recommended training and practice")
        
        return steps
    
    def predict_role_readiness(
        self,
        employee_data: Dict[str, Any],
        target_role: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict readiness for a target role.
        
        Args:
            employee_data: Employee data
            target_role: Target role requirements
            
        Returns:
            Readiness assessment with score and recommendations
        """
        current_skills = employee_data.get("skills", [])
        required_skills = target_role.get("required_skills", [])
        preferred_skills = target_role.get("preferred_skills", [])
        
        gap_analysis = self.detect_skill_gaps(current_skills, required_skills)
        
        # Check preferred skills
        preferred_gap = self.detect_skill_gaps(current_skills, preferred_skills)
        
        # Calculate readiness score
        required_score = gap_analysis["gap_score"]
        preferred_score = preferred_gap["gap_score"]
        readiness_score = int((required_score * 0.7 + preferred_score * 0.3))
        
        return {
            "role_fit_score": readiness_score,
            "readiness_score": readiness_score,
            "required_skills_match": gap_analysis["coverage"],
            "preferred_skills_match": preferred_gap["coverage"],
            "missing_required": gap_analysis["missing_skills"],
            "missing_preferred": preferred_gap["missing_skills"],
            "recommendation": self._get_readiness_recommendation(readiness_score),
        }
    
    def propose_promotions(
        self,
        employee_data: Dict[str, Any],
        available_roles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Propose suitable promotions or lateral moves.
        
        Args:
            employee_data: Employee data
            available_roles: List of available roles
            
        Returns:
            List of proposed roles with readiness scores
        """
        proposals = []
        
        for role in available_roles:
            readiness = self.predict_role_readiness(employee_data, role)
            if readiness["readiness_score"] >= 60:  # Threshold for proposal
                proposals.append({
                    "role": role.get("title", "Unknown"),
                    "department": role.get("department", "Unknown"),
                    "readiness_score": readiness["readiness_score"],
                    "missing_skills": readiness["missing_required"],
                    "recommendation": readiness["recommendation"],
                })
        
        # Sort by readiness score
        proposals.sort(key=lambda x: x["readiness_score"], reverse=True)
        
        return proposals
    
    def _fallback_analysis(
        self,
        employee_data: Dict[str, Any],
        role_requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fallback analysis when LLM is unavailable."""
        current_skills = employee_data.get("skills", [])
        required_skills = role_requirements.get("required_skills", []) if role_requirements else []
        
        gap_analysis = self.detect_skill_gaps(current_skills, required_skills)
        strengths = self.detect_strengths(employee_data)
        
        return {
            "current_skills": current_skills,
            "missing_skills": gap_analysis["missing_skills"],
            "gap_score": gap_analysis["gap_score"],
            "strengths": strengths,
            "recommended_roles": [],
            "development_path": self.generate_development_path(current_skills, required_skills),
            "analysis_summary": f"Employee has {len(current_skills)} skills. Gap score: {gap_analysis['gap_score']}/100.",
        }
    
    def _decorate_analysis(
        self,
        analysis: Dict[str, Any],
        *,
        mode: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Attach AI metadata to an analysis payload."""
        ai_gap = int(analysis.get("ai_gap_score", analysis.get("gap_score", 65)))
        ai_readiness = int(analysis.get("ai_readiness", ai_gap))
        ai_risk = int(analysis.get("ai_risk_signal", max(0, 100 - ai_readiness)))
        ai_skill_recs = int(
            analysis.get(
                "ai_skill_recommendations_count",
                len(analysis.get("missing_skills", [])),
            )
        )

        analysis["gap_score"] = int(analysis.get("gap_score", ai_gap))
        analysis["ai_gap_score"] = ai_gap
        analysis["ai_readiness"] = ai_readiness
        analysis["ai_risk_signal"] = ai_risk
        analysis["ai_skill_recommendations_count"] = ai_skill_recs
        analysis["ai_mode"] = mode
        analysis["ai_provider"] = self.provider
        analysis["ai_used"] = mode == "live"
        analysis["ai_alive_status"] = "LIVE" if mode == "live" else "HEURISTIC"
        if mode != "live" and error:
            analysis["error"] = error
        return analysis

    @classmethod
    async def generate_department_narrative(
        cls,
        department_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate department narrative using Featherless."""
        llm_config = LLMConfig.from_env()
        schema = {
            "department": str,
            "narrative": str,
            "insights": list,
            "risks": list,
            "strengths": list,
            "shortages": list,
            "readiness_summary": str,
            "succession_summary": str,
            "numeric_references": list,
            "risk_level": str,
            "risk_score": int,
        }

        analytics = department_metrics.get("department_analytics", {})
        succession = department_metrics.get("succession_snapshot", {})
        dept_name = department_metrics.get("department_name", "Unknown")
        prompt = cls._build_narrative_prompt(dept_name, analytics, succession)

        try:
            async with LLMClient(llm_config) as llm:
                narrative = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an executive coach summarizing department readiness.",
                    temperature=0.4,
                    max_tokens=900,
                )
            narrative["ai_mode"] = "live"
            narrative["ai_provider"] = llm_config.provider
            narrative["ai_used"] = True
            narrative["generated_at"] = datetime.utcnow().isoformat()
            return narrative
        except Exception as exc:
            fallback = cls._fallback_department_narrative(department_metrics)
            fallback.update(
                {
                    "ai_mode": "heuristic",
                    "ai_provider": llm_config.provider,
                    "ai_used": False,
                    "error": str(exc),
                }
            )
            return fallback

    @staticmethod
    def _build_narrative_prompt(
        department_name: str,
        analytics: Dict[str, Any],
        succession_snapshot: Dict[str, Any],
    ) -> str:
        heatmap = analytics.get("team_skill_heatmap", {})
        shortages = analytics.get("skill_shortages", [])
        risk_scores = analytics.get("risk_scores", {})

        unified = succession_snapshot.get("unified_score", {})
        pipeline = succession_snapshot.get("pipeline_summary", {})

        return f"""Department: {department_name}
Skill strengths (top 3): {list(heatmap.keys())[:3]}
Skill shortages (top 3): {shortages[:3]}
Risk scores: {risk_scores}
Succession unified score: {unified}
Pipeline summary: {pipeline}

Produce JSON with:
- department
- narrative (3 sentences referencing numeric values)
- insights (list of department-specific insights)
- risks (list with risk label + numeric reference)
- strengths (top differentiators)
- shortages (top shortages)
- readiness_summary (mention readiness and numeric references)
- succession_summary (pipeline summary text)
- numeric_references (list of strings citing metrics)
- risk_level (low, medium, high)
- risk_score (0-100 numeric).
Avoid repetition between departments by referencing their unique values."""

    @staticmethod
    def _fallback_department_narrative(department_metrics: Dict[str, Any]) -> Dict[str, Any]:
        department_name = department_metrics.get("department_name", "Unknown")
        analytics = department_metrics.get("department_analytics", {})
        succession_snapshot = department_metrics.get("succession_snapshot", {})

        heatmap = analytics.get("team_skill_heatmap", {})
        strengths = list(heatmap.keys())[:3] or ["core capabilities"]
        shortages = analytics.get("skill_shortages", [])[:3] or ["emerging capabilities"]
        risk_score = int(analytics.get("risk_scores", {}).get("skill_concentration_risk", 30))
        risk_level = SkillAIService._risk_level_from_score(risk_score)

        dept_score = succession_snapshot.get("unified_score", {})
        readiness_value = dept_score.get("next_role_readiness", 70)
        pipeline = succession_snapshot.get("pipeline_summary", {})

        strengths_text = ", ".join(strengths)
        shortage_text = ", ".join(shortages)

        narrative = (
            f"{department_name} demonstrates strength in {strengths_text}. "
            f"Coverage gaps remain in {shortage_text}. "
            f"Risk posture is {risk_level} ({risk_score}/100) with readiness at {readiness_value}/100."
        )
        readiness_summary = (
            f"Department readiness holds at {readiness_value}/100 with {pipeline.get('ready_now', 0)} ready-now leaders."
        )

        narrative_score = compose_unified_score(
            skill_scores=ranking_dict(strengths),
            gap_scores=ranking_dict(shortages or ["coverage gap"], base=65),
            role_fit_score=readiness_value,
            next_role_readiness=readiness_value,
            risk_score=risk_score,
        )

        return {
            "department": department_name,
            "strengths": strengths,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "narrative": narrative,
            "insights": [f"{department_name} strengths: {strengths_text}"],
            "risks": [f"{risk_level} risk at {risk_score}/100"],
            "shortages": shortages,
            "readiness_summary": readiness_summary,
            "succession_summary": pipeline.get("narrative", "Pipeline status unavailable."),
            "numeric_references": [
                f"risk_score={risk_score}",
                f"readiness={readiness_value}",
                f"ready_now={pipeline.get('ready_now', 0)}",
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "unified_score": narrative_score.model_dump(),
        }

    @staticmethod
    def _risk_level_from_score(score: int) -> str:
        if score >= 70:
            return "high"
        if score >= 40:
            return "medium"
        return "low"
    
    def _get_readiness_recommendation(self, score: int) -> str:
        """Get text recommendation based on readiness score."""
        if score >= 90:
            return "Highly ready for this role. Consider immediate promotion."
        elif score >= 75:
            return "Ready for this role with minor skill development."
        elif score >= 60:
            return "Moderately ready. Focus on missing skills before promotion."
        elif score >= 40:
            return "Not yet ready. Significant skill development needed."
        else:
            return "Not ready. Consider alternative development paths."
