"""
Leadership Narrative Service
----------------------------
AI-powered storytelling for leadership succession planning.
Generates McKinsey-style narratives analyzing succession pipelines.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.services.ai.ai_succession_service import AISuccessionService
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("leadership_narrative")


class LeadershipNarrativeService:
    """AI-powered leadership succession narrative service."""

    def __init__(
        self,
        employee_repo: EmployeeRepository,
        skill_repo: Any,  # SkillAnalysisRepository
    ):
        """
        Initialize leadership narrative service.

        Args:
            employee_repo: Employee repository
            skill_repo: Skill analysis repository
        """
        self.employee_repo = employee_repo
        self.skill_repo = skill_repo
        self.llm_config = LLMConfig.from_env()
        self.analytics_service = SkillAnalyticsService()
        self.ai_succession_service = AISuccessionService()

    async def generate_leadership_narrative(
        self,
        session: AsyncSession,
        department_name: str,
        succession_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate leadership succession narrative.

        Args:
            session: Async database session
            department_name: Department name
            succession_data: Succession radar data including candidates, pipeline summary, etc.

        Returns:
            Dictionary with narrative, leadership actions, risk summary, and successor candidates
        """
        # Extract key data from succession radar
        candidates = succession_data.get("candidates", [])
        pipeline_summary = succession_data.get("pipeline_summary", {})
        unified_score = succession_data.get("unified_score", {})
        
        # Get department analytics for additional context
        employee_records = await self.employee_repo.get_by_department(session, department_name)
        department_employees = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
                "metadata": emp.metadata or {},
            }
            for emp in employee_records
        ]
        
        department_analytics = await self.analytics_service.analyze_department(
            department_name, department_employees
        )

        # Build comprehensive prompt
        prompt = self._build_narrative_prompt(
            department_name=department_name,
            candidates=candidates,
            pipeline_summary=pipeline_summary,
            unified_score=unified_score,
            department_analytics=department_analytics,
        )

        # Define response schema
        schema = {
            "narrative": str,
            "leadership_actions": [
                {
                    "action": str,
                    "priority": str,
                    "timeline": str,
                    "impact": str,
                }
            ],
            "risk_summary": {
                "pipeline_strength": int,
                "key_risks": list,
                "vacancy_risk": int,
            },
            "successor_candidates": [
                {
                    "employee_id": str,
                    "name": str,
                    "readiness_score": int,
                    "strengths": list,
                    "development_areas": list,
                    "time_to_readiness": str,
                }
            ],
        }

        try:
            ai_result = await self.ai_succession_service.analyze_succession(
                department=department_name,
                candidates=candidates,
                pipeline_data={
                    "pipeline_summary": pipeline_summary,
                    "unified_score": unified_score,
                    "department_analytics": department_analytics,
                }
            )
            
            result = {
                "narrative": ai_result.pipeline_assessment,
                "leadership_actions": [
                    {
                        "action": priority,
                        "priority": "high" if idx < 2 else "medium",
                        "timeline": "6-12 months",
                        "impact": f"Addresses {priority.lower()}",
                    }
                    for idx, priority in enumerate(ai_result.development_priorities[:5])
                ],
                "risk_summary": {
                    "pipeline_strength": ai_result.pipeline_strength,
                    "key_risks": ai_result.readiness_gaps,
                    "vacancy_risk": ai_result.vacancy_risk,
                },
                "successor_candidates": [
                    {
                        "employee_id": cand.get("employee_id", ""),
                        "name": cand.get("name", cand.get("employee_id", "")),
                        "readiness_score": cand.get("readiness", 0),
                        "strengths": [],
                        "development_areas": [],
                        "time_to_readiness": cand.get("timeline", "6-12 months"),
                    }
                    for cand in ai_result.top_candidates
                ],
                "ai_mode": ai_result.ai_mode,
            }
            
            return result

        except Exception as exc:
            logger.error(f"Leadership narrative generation failed: {exc}", exc_info=True)
            # NO FALLBACK - raise exception if Azure fails
            raise RuntimeError(f"Leadership narrative generation failed. Azure OpenAI is required and not responding correctly: {exc}") from exc

    def _build_narrative_prompt(
        self,
        department_name: str,
        candidates: List[Dict[str, Any]],
        pipeline_summary: Dict[str, Any],
        unified_score: Dict[str, Any],
        department_analytics: Dict[str, Any],
    ) -> str:
        """Build comprehensive prompt for leadership narrative generation."""
        ready_now = pipeline_summary.get("ready_now", 0)
        ready_soon = pipeline_summary.get("ready_soon", 0)
        developing = pipeline_summary.get("developing", 0)
        risk_outlook = pipeline_summary.get("risk_outlook", "medium")
        
        overall_score = unified_score.get("overall_score", 70)
        risk_score = unified_score.get("risk_score", 30)
        readiness = unified_score.get("next_role_readiness", 70)
        
        # Top candidates
        top_candidates = sorted(
            candidates,
            key=lambda x: x.get("readiness_score", 0) or x.get("next_role_readiness", 0),
            reverse=True
        )[:5]
        
        candidate_summaries = []
        for cand in top_candidates:
            candidate_summaries.append(
                f"- {cand.get('name', cand.get('employee_id', 'Unknown'))}: "
                f"Readiness {cand.get('readiness_score', cand.get('next_role_readiness', 0))}/100, "
                f"Strengths: {', '.join(cand.get('skill_strengths', [])[:3])}, "
                f"Gaps: {', '.join(cand.get('skill_gaps', [])[:2])}"
            )
        
        # Department context
        skill_shortages = department_analytics.get("skill_shortages", [])
        team_skill_heatmap = department_analytics.get("team_skill_heatmap", {})
        
        prompt = f"""Analyze the leadership succession pipeline for the {department_name} department at Škoda AUTO.

Succession Pipeline Data:
- Ready Now: {ready_now} candidates
- Ready Soon: {ready_soon} candidates
- Developing: {developing} candidates
- Risk Outlook: {risk_outlook}
- Overall Score: {overall_score}/100
- Risk Score: {risk_score}/100
- Average Readiness: {readiness}/100

Top Candidates:
{chr(10).join(candidate_summaries) if candidate_summaries else 'No candidates identified'}

Department Context:
- Skill Shortages: {', '.join(skill_shortages[:5]) if skill_shortages else 'None identified'}
- Team Strengths: {', '.join(list(team_skill_heatmap.keys())[:5]) if team_skill_heatmap else 'Unknown'}

Generate a comprehensive leadership narrative that:

1. **Narrative** (3-4 paragraphs, McKinsey style):
   - Executive summary of succession pipeline health
   - Analysis of high-potential employees and their readiness
   - Risk assessment and shortage predictions
   - Strategic recommendations for leadership development
   - Write in a professional, data-driven, strategic consulting style

2. **Leadership Actions** (3-5 actions):
   - Specific, actionable recommendations
   - Priority (high, medium, low)
   - Timeline (e.g., "Q1 2025", "6 months", "Immediate")
   - Expected impact description

3. **Risk Summary**:
   - Pipeline strength score (0-100)
   - Key risks (list of risk descriptions)
   - Vacancy risk score (0-100) - likelihood of leadership gaps

4. **Successor Candidates** (top 3-5):
   - Employee ID and name
   - Readiness score
   - Key strengths
   - Development areas
   - Time to readiness (e.g., "Ready now", "6 months", "12-18 months")

Be strategic, specific, and actionable. Focus on business impact and leadership development.
"""

        return prompt

    def _fallback_narrative(
        self,
        department_name: str,
        candidates: List[Dict[str, Any]],
        pipeline_summary: Dict[str, Any],
        unified_score: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback narrative when AI fails."""
        ready_now = pipeline_summary.get("ready_now", 0)
        ready_soon = pipeline_summary.get("ready_soon", 0)
        risk_score = unified_score.get("risk_score", 30)
        
        top_candidates = sorted(
            candidates,
            key=lambda x: x.get("readiness_score", 0) or x.get("next_role_readiness", 0),
            reverse=True
        )[:3]
        
        pipeline_strength = min(100, (ready_now * 40) + (ready_soon * 20))
        vacancy_risk = max(0, 100 - pipeline_strength)
        
        return {
            "narrative": f"The {department_name} department succession pipeline shows {ready_now} candidates ready for leadership roles now, with {ready_soon} developing. The pipeline strength is {pipeline_strength}/100, indicating {'strong' if pipeline_strength > 70 else 'moderate' if pipeline_strength > 40 else 'weak'} succession readiness. Risk score of {risk_score}/100 suggests {'low' if risk_score < 30 else 'moderate' if risk_score < 60 else 'high'} leadership transition risk.",
            "leadership_actions": [
                {
                    "action": f"Accelerate development of {ready_soon} ready-soon candidates in {department_name}",
                    "priority": "high",
                    "timeline": "6 months",
                    "impact": "Strengthens pipeline and reduces vacancy risk",
                },
                {
                    "action": "Implement targeted leadership development programs",
                    "priority": "medium",
                    "timeline": "Q1 2025",
                    "impact": "Builds bench strength for future leadership needs",
                },
                {
                    "action": "Establish mentorship programs for developing candidates",
                    "priority": "medium",
                    "timeline": "3 months",
                    "impact": "Accelerates readiness and knowledge transfer",
                },
            ],
            "risk_summary": {
                "pipeline_strength": pipeline_strength,
                "key_risks": [
                    "Limited ready-now candidates" if ready_now < 2 else "Pipeline depth concerns",
                    f"Vacancy risk at {vacancy_risk}%",
                ],
                "vacancy_risk": vacancy_risk,
            },
            "successor_candidates": [
                {
                    "employee_id": cand.get("employee_id", "Unknown"),
                    "name": cand.get("name", cand.get("employee_id", "Unknown")),
                    "readiness_score": cand.get("readiness_score", cand.get("next_role_readiness", 60)),
                    "strengths": cand.get("skill_strengths", [])[:3],
                    "development_areas": cand.get("skill_gaps", [])[:2],
                    "time_to_readiness": "Ready now" if cand.get("readiness_score", 0) > 80 else "6-12 months",
                }
                for cand in top_candidates
            ],
            "ai_mode": "heuristic",
        }

