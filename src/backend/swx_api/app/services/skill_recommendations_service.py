"""
Async Recommendation Engine
---------------------------
Hybrid rule-based + LLM-based recommendation system for skills,
training paths, and career development.
All methods are async.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.services.skill_ai_service import SkillAIService
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("skill_recommendations")


class SkillRecommendationsService:
    """Async recommendation service combining rule-based and LLM-based logic."""
    
    def __init__(
        self,
        employee_repo: EmployeeRepository,
        skill_repo: Any  # SkillAnalysisRepository
    ):
        """
        Initialize service with repositories.
        
        Args:
            employee_repo: Employee repository
            skill_repo: Skill analysis repository
        """
        self.employee_repo = employee_repo
        self.skill_repo = skill_repo
        self.ai_service = SkillAIService(employee_repo, skill_repo)
    
    async def recommend_skills(
        self,
        session: AsyncSession,
        employee_data: Dict[str, Any],
        department_data: Optional[Dict[str, Any]] = None,
        global_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommend skills for an employee.
        
        Args:
            session: Async database session
            employee_data: Employee data
            department_data: Optional department-wide data
            global_data: Optional global skill data
            
        Returns:
            List of skill recommendations with priority and reasoning
        """
        recommendations = []
        current_skills = set(s.lower() for s in employee_data.get("skills", []))
        
        # Rule-based: Recommend complementary skills
        complementary_skills = self._get_complementary_skills(employee_data)
        for skill in complementary_skills:
            if skill.lower() not in current_skills:
                recommendations.append({
                    "skill": skill,
                    "priority": "high",
                    "reason": "Complementary to current skills",
                    "source": "rule-based",
                })
        
        # Rule-based: Recommend department-common skills
        if department_data:
            dept_common = department_data.get("common_skills", [])
            for skill in dept_common[:5]:  # Top 5
                if skill.lower() not in current_skills:
                    recommendations.append({
                        "skill": skill,
                        "priority": "medium",
                        "reason": "Commonly used in your department",
                        "source": "rule-based",
                    })
        
        ai_recommendations, ai_analysis = await self._get_ai_skill_recommendations(
            session,
            employee_data
        )
        ai_mode = ai_analysis.get("ai_mode", "heuristic_fallback")
        ai_used = ai_mode == "live"

        for rank, skill in enumerate(ai_recommendations):
            if skill.lower() in current_skills:
                continue
            recommendations.append({
                "skill": skill,
                "priority": "high",
                "reason": "AI-identified capability gap",
                "source": "llm-based",
                "ai_rank": rank,
            })
        
        # Deduplicate and sort
        unique_recommendations: List[Dict[str, Any]] = []
        seen: Dict[str, Dict[str, Any]] = {}
        for rec in recommendations:
            skill_lower = rec["skill"].lower()
            if skill_lower in seen:
                if rec.get("source") == "llm-based":
                    seen[skill_lower] = rec
                continue
            seen[skill_lower] = rec
        unique_recommendations = sorted(
            seen.values(),
            key=lambda item: (0 if item.get("source") == "llm-based" else 1, item.get("ai_rank", 99)),
        )
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        unique_recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        ai_skill_recs = ai_analysis.get("ai_skill_recommendations_count", len(ai_recommendations))

        return {
            "items": unique_recommendations[:10],
            "ai_used": ai_used,
            "ai_mode": ai_mode,
            "ai_metrics": {
                "ai_gap_score": ai_analysis.get("ai_gap_score"),
                "ai_readiness": ai_analysis.get("ai_readiness"),
                "ai_risk_signal": ai_analysis.get("ai_risk_signal"),
                "ai_skill_recommendations_count": ai_skill_recs,
            },
        }
    
    async def recommend_training_path(
        self,
        employee_data: Dict[str, Any],
        target_skills: List[str]
    ) -> Dict[str, Any]:
        """
        Recommend training path to acquire target skills.
        
        Args:
            employee_data: Employee data
            target_skills: List of target skills
            
        Returns:
            Training path with steps, timeline, and resources
        """
        current_skills = employee_data.get("skills", [])
        
        # Generate development path (sync method is OK)
        development_steps = self.ai_service.generate_development_path(
            current_skills,
            target_skills,
            time_horizon="6 months"
        )
        
        # Estimate timeline
        timeline = self._estimate_timeline(len(target_skills))
        
        # Suggest resources (placeholder - can be enhanced)
        resources = self._suggest_resources(target_skills)
        
        return {
            "target_skills": target_skills,
            "steps": development_steps,
            "timeline": timeline,
            "resources": resources,
            "estimated_completion": self._estimate_completion_date(timeline),
        }
    
    async def recommend_next_role(
        self,
        employee_data: Dict[str, Any],
        available_roles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Recommend next role for employee.
        
        Args:
            employee_data: Employee data
            available_roles: List of available roles
            
        Returns:
            List of recommended roles with readiness scores
        """
        # Use AI service to propose promotions (sync method is OK)
        proposals = self.ai_service.propose_promotions(employee_data, available_roles)
        
        return proposals
    
    async def recommend_department_interventions(
        self,
        department_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Recommend department-wide interventions.
        
        Args:
            department_data: Department analytics data
            
        Returns:
            List of recommended interventions
        """
        interventions = []
        
        skill_shortages = department_data.get("skill_shortages", [])
        if skill_shortages:
            interventions.append({
                "type": "training_program",
                "priority": "high",
                "description": f"Organize training for {len(skill_shortages)} missing skills",
                "skills": skill_shortages[:5],
                "recommended_action": "Schedule department-wide training sessions",
            })
        
        risk_scores = department_data.get("risk_scores", {})
        if risk_scores.get("knowledge_concentration_risk", 0) > 70:
            interventions.append({
                "type": "knowledge_sharing",
                "priority": "high",
                "description": "High knowledge concentration risk detected",
                "recommended_action": "Implement knowledge sharing sessions and documentation",
            })
        
        if risk_scores.get("retention_risk", 0) > 60:
            interventions.append({
                "type": "retention_strategy",
                "priority": "medium",
                "description": "High retention risk detected",
                "recommended_action": "Review compensation and career development opportunities",
            })
        
        return interventions
    
    def _get_complementary_skills(self, employee_data: Dict[str, Any]) -> List[str]:
        """Get complementary skills based on current skills (rule-based)."""
        current_skills = [s.lower() for s in employee_data.get("skills", [])]
        complementary_map = {
            "python": ["sql", "data analysis", "machine learning"],
            "javascript": ["typescript", "react", "node.js"],
            "java": ["spring", "microservices", "docker"],
            "project management": ["agile", "scrum", "stakeholder management"],
            "data analysis": ["python", "sql", "statistics"],
        }
        
        complementary = []
        for skill in current_skills:
            if skill in complementary_map:
                complementary.extend(complementary_map[skill])
        
        return list(set(complementary))
    
    async def _get_ai_skill_recommendations(
        self,
        session: AsyncSession,
        employee_data: Dict[str, Any]
    ) -> tuple[List[str], Dict[str, Any]]:
        """Get AI-based skill recommendations using async service."""
        try:
            analysis = await self.ai_service.analyze_employee(
                session,
                employee_data.get("employee_id", "unknown"),
                employee_data
            )
            return analysis.get("missing_skills", [])[:5], analysis
        except Exception as exc:
            logger.error(f"AI skill recommendation failure: {exc}")
            fallback = {
                "missing_skills": [],
                "ai_mode": "heuristic_fallback",
                "ai_provider": self.ai_service.provider,
                "error": str(exc),
            }
            return [], fallback
    
    def _estimate_timeline(self, skill_count: int) -> Dict[str, Any]:
        """Estimate timeline for acquiring skills."""
        # Rough estimate: 2-3 months per skill
        months = skill_count * 2.5
        return {
            "estimated_months": int(months),
            "estimated_weeks": int(months * 4),
        }
    
    def _suggest_resources(self, skills: List[str]) -> List[Dict[str, Any]]:
        """Suggest learning resources for skills."""
        resources = []
        for skill in skills[:5]:  # Limit to 5
            resources.append({
                "skill": skill,
                "resource_type": "online_course",
                "suggested_platforms": ["Coursera", "Udemy", "LinkedIn Learning"],
            })
        return resources
    
    def _estimate_completion_date(self, timeline: Dict[str, Any]) -> str:
        """Estimate completion date based on timeline."""
        from datetime import datetime, timedelta
        months = timeline.get("estimated_months", 6)
        completion = datetime.utcnow() + timedelta(days=months * 30)
        return completion.isoformat()
