"""
Career Coach Service
--------------------
AI-powered conversational assistant for Škoda employees.
Provides personalized career guidance, skill recommendations, and readiness assessments.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.skill_ai_service import SkillAIService
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.services.skill_recommendations_service import SkillRecommendationsService
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("career_coach")


class CareerCoachService:
    """AI-powered career coaching service with conversational interface."""

    def __init__(
        self,
        employee_repo: EmployeeRepository,
        skill_repo: Any,  # SkillAnalysisRepository
    ):
        """
        Initialize career coach service.

        Args:
            employee_repo: Employee repository
            skill_repo: Skill analysis repository
        """
        self.employee_repo = employee_repo
        self.skill_repo = skill_repo
        self.llm_config = LLMConfig.from_env()
        self.ai_service = SkillAIService(employee_repo, skill_repo)
        self.analytics_service = SkillAnalyticsService()
        self.recommendations_service = SkillRecommendationsService(employee_repo, skill_repo)

    async def run_chat(
        self,
        session: AsyncSession,
        user_message: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run career coaching chat conversation.

        Args:
            session: Async database session
            user_message: User's message/question
            context: Context including employee_id, skills, career_goals, department

        Returns:
            Dictionary with assistant response and summary
        """
        employee_id = context.get("employee_id")
        skills = context.get("skills", [])
        career_goals = context.get("career_goals", "")
        department = context.get("department", "Unknown")

        # Gather comprehensive context
        employee_data = await self._gather_employee_context(
            session, employee_id, skills, department
        )

        # Get analytics and recommendations
        analytics = await self._get_employee_analytics(session, employee_data)
        recommendations = await self._get_recommendations(session, employee_data)
        succession_data = await self._get_succession_data(session, employee_data, department)

        # Build comprehensive prompt
        prompt = self._build_chat_prompt(
            user_message=user_message,
            employee_data=employee_data,
            analytics=analytics,
            recommendations=recommendations,
            succession_data=succession_data,
            career_goals=career_goals,
        )

        # Define response schema
        schema = {
            "assistant": str,
            "summary": {
                "next_role": str,
                "readiness_score": int,
                "time_to_readiness_months": int,
                "risk_score": int,
                "recommended_skills": list,
                "recommended_training": list,
            },
        }

        try:
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are a friendly, supportive career coach for Škoda employees. Provide personalized, actionable advice.",
                    temperature=0.7,
                    max_tokens=1500,
                )

            # Force Azure mode - check if result is valid
            if result and (result.get("assistant") or result.get("summary")):
                result["ai_mode"] = "azure"
                return result
            else:
                logger.warning(f"Career coach chat returned empty/invalid result, retrying...")
                # Retry once more
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are a friendly, supportive career coach for Škoda employees. Provide personalized, actionable advice.",
                    temperature=0.7,
                    max_tokens=1500,
                )
                if result and (result.get("assistant") or result.get("summary")):
                    result["ai_mode"] = "azure"
                    return result

        except Exception as exc:
            logger.error(f"Career coach chat failed (retrying): {exc}", exc_info=True)
            # Retry once more before raising exception
            try:
                async with LLMClient(self.llm_config) as llm:
                    result = await llm.call_llm(
                        prompt=prompt,
                        schema=schema,
                        system_message="You are a friendly, supportive career coach for Škoda employees. Provide personalized, actionable advice.",
                        temperature=0.7,
                        max_tokens=1500,
                    )
                    if result and (result.get("assistant") or result.get("summary")):
                        result["ai_mode"] = "azure"
                        return result
            except Exception as retry_exc:
                logger.error(f"Career coach chat retry also failed: {retry_exc}")
                # NO FALLBACK - raise exception if Azure fails after retries
                raise RuntimeError(f"Career coach chat failed after retries. Azure OpenAI is required and not responding correctly: {retry_exc}") from retry_exc
        
        # If we get here, the first attempt failed but retry succeeded
        # This should not happen, but just in case:
        logger.error(f"Career coach chat failed after retries - Azure OpenAI required")
        raise RuntimeError(f"Career coach chat failed after retries. Azure OpenAI is required and not responding correctly: {exc}") from exc

    async def _gather_employee_context(
        self,
        session: AsyncSession,
        employee_id: Optional[str],
        skills: List[str],
        department: str,
    ) -> Dict[str, Any]:
        """Gather employee context from database or provided data."""
        employee_data = {
            "employee_id": employee_id or "anonymous",
            "department": department,
            "skills": skills,
            "metadata": {},
        }

        if employee_id:
            try:
                employee_record = await self.employee_repo.get_by_employee_id(session, employee_id)
                if employee_record:
                    employee_data.update({
                        "employee_id": employee_record.employee_id,
                        "department": employee_record.department,
                        "skills": employee_record.skills or skills,
                        "metadata": employee_record.metadata or {},
                    })
            except Exception as e:
                logger.warning(f"Could not load employee {employee_id}: {e}")

        return employee_data

    async def _get_employee_analytics(
        self, session: AsyncSession, employee_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get employee analytics."""
        try:
            analytics = await self.analytics_service.analyze_employee(
                employee_data["employee_id"],
                employee_data,
            )
            return analytics
        except Exception as e:
            logger.warning(f"Analytics failed: {e}")
            return {}

    async def _get_recommendations(
        self, session: AsyncSession, employee_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get skill recommendations."""
        try:
            result = await self.recommendations_service.recommend_skills(
                session,
                employee_data,
                None,
            )
            return result
        except Exception as e:
            logger.warning(f"Recommendations failed: {e}")
            return {"items": []}

    async def _get_succession_data(
        self, session: AsyncSession, employee_data: Dict[str, Any], department: str
    ) -> Dict[str, Any]:
        """Get succession pipeline data for department."""
        try:
            dept_employees = await self.employee_repo.get_by_department(session, department)
            if not dept_employees:
                return {}

            dept_data = [
                {
                    "employee_id": emp.employee_id,
                    "department": emp.department,
                    "skills": emp.skills or [],
                    "metadata": emp.metadata or {},
                }
                for emp in dept_employees
            ]

            dept_analytics = await self.analytics_service.analyze_department(
                department, dept_data
            )
            return dept_analytics
        except Exception as e:
            logger.warning(f"Succession data failed: {e}")
            return {}

    def _build_chat_prompt(
        self,
        user_message: str,
        employee_data: Dict[str, Any],
        analytics: Dict[str, Any],
        recommendations: Dict[str, Any],
        succession_data: Dict[str, Any],
        career_goals: str,
    ) -> str:
        """Build comprehensive prompt for career coaching chat."""
        employee_id = employee_data.get("employee_id", "Employee")
        department = employee_data.get("department", "Unknown")
        skills = employee_data.get("skills", [])

        # Extract key metrics
        readiness_score = analytics.get("readiness_score", 70)
        stagnation = analytics.get("stagnation_detected", False)
        skill_diversity = analytics.get("skill_level_stats", {}).get("skill_diversity", 0)

        # Get recommendations
        rec_items = recommendations.get("items", [])
        recommended_skills = [r.get("skill", "") for r in rec_items[:5] if r.get("skill")]

        # Department context
        dept_heatmap = succession_data.get("team_skill_heatmap", {})
        dept_shortages = succession_data.get("skill_shortages", [])

        prompt = f"""You are a career coach helping a Škoda employee with their career development.

Employee Profile:
- ID: {employee_id}
- Department: {department}
- Current Skills: {', '.join(skills) if skills else 'None listed'}
- Career Goals: {career_goals if career_goals else 'Not specified'}

Current Analytics:
- Readiness Score: {readiness_score}/100
- Skill Diversity: {skill_diversity:.1f}
- Stagnation Risk: {'Yes' if stagnation else 'No'}

Recommended Skills: {', '.join(recommended_skills) if recommended_skills else 'None'}

Department Context:
- Team Strengths: {', '.join(list(dept_heatmap.keys())[:5]) if dept_heatmap else 'Unknown'}
- Skill Shortages: {', '.join(dept_shortages[:5]) if dept_shortages else 'None'}

User Question: {user_message}

Please provide:
1. A conversational, supportive response addressing their question
2. Inferred strengths based on their skills and analytics
3. Identified skill gaps
4. Proposed next role suggestion
5. Estimated readiness score (0-100)
6. Time to readiness in months
7. Risk score (0-100) - higher means more risk
8. Recommended skills to develop
9. Recommended training paths
10. Any warnings or risks to be aware of
11. Personalized coaching advice

Be encouraging, specific, and actionable. Reference their actual skills and department context.
"""

        return prompt

    def _fallback_response(
        self,
        user_message: str,
        employee_data: Dict[str, Any],
        analytics: Dict[str, Any],
        recommendations: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback response when AI fails."""
        skills = employee_data.get("skills", [])
        readiness = analytics.get("readiness_score", 70)
        rec_items = recommendations.get("items", [])
        recommended_skills = [r.get("skill") for r in rec_items[:5]]

        return {
            "assistant": f"Thank you for your question: '{user_message}'. Based on your profile, I can see you have skills in {', '.join(skills[:3]) if skills else 'various areas'}. Your current readiness score is {readiness}/100. I recommend focusing on developing: {', '.join(recommended_skills[:3]) if recommended_skills else 'additional skills'}.",
            "summary": {
                "next_role": "Senior role in your department",
                "readiness_score": readiness,
                "time_to_readiness_months": max(6, 12 - (readiness // 10)),
                "risk_score": max(0, 100 - readiness),
                "recommended_skills": recommended_skills[:5],
                "recommended_training": [
                    f"Training for {skill}" for skill in recommended_skills[:3]
                ],
            },
            "ai_mode": "heuristic",
        }

