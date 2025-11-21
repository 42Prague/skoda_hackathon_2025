"""
Training Plan Service
---------------------
AI-powered personalized training plan generator for Škoda employees.
Creates comprehensive weekly plans, course recommendations, and skill progression maps.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.skill_ai_service import SkillAIService
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.services.skill_recommendations_service import SkillRecommendationsService
from swx_api.app.services.ai.ai_training_service import AITrainingService
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("training_plan")


class TrainingPlanService:
    """AI-powered training plan generation service."""

    def __init__(
        self,
        employee_repo: EmployeeRepository,
        skill_repo: Any,  # SkillAnalysisRepository
    ):
        """
        Initialize training plan service.

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
        self.ai_training_service = AITrainingService()

    async def generate_training_plan(
        self,
        session: AsyncSession,
        employee_id: Optional[str],
        skills: List[str],
        gaps: List[str],
        desired_role: str,
    ) -> Dict[str, Any]:
        """
        Generate personalized training plan.

        Args:
            session: Async database session
            employee_id: Employee identifier (optional)
            skills: Current skills list
            gaps: Skill gaps to address
            desired_role: Target role for training

        Returns:
            Dictionary with comprehensive training plan
        """
        # Gather employee context
        employee_data = await self._gather_employee_context(
            session, employee_id, skills
        )

        # Get analytics and recommendations
        analytics = await self._get_employee_analytics(session, employee_data)
        recommendations = await self._get_recommendations(session, employee_data, gaps)
        
        # Get role readiness assessment
        role_readiness = await self._assess_role_readiness(
            session, employee_data, desired_role
        )

        # Build comprehensive prompt
        prompt = self._build_training_plan_prompt(
            employee_data=employee_data,
            skills=skills,
            gaps=gaps,
            desired_role=desired_role,
            analytics=analytics,
            recommendations=recommendations,
            role_readiness=role_readiness,
        )

        # Define response schema
        schema = {
            "plan_overview": str,
            "weekly_breakdown": [
                {
                    "week": int,
                    "focus_skills": list,
                    "courses": list,
                    "practice_tasks": list,
                    "milestones": list,
                }
            ],
            "courses": [
                {
                    "name": str,
                    "provider": str,
                    "duration_hours": int,
                    "type": str,
                    "priority": str,
                    "skoda_academy": bool,
                }
            ],
            "skill_progression_map": [
                {
                    "skill": str,
                    "current_level": str,
                    "target_level": str,
                    "weeks_to_master": int,
                    "dependencies": list,
                }
            ],
            "mentors": [
                {
                    "name": str,
                    "expertise": list,
                    "availability": str,
                    "recommended_for": list,
                }
            ],
            "risks": [
                {
                    "risk": str,
                    "severity": str,
                    "mitigation": str,
                }
            ],
            "time_to_readiness": int,
            "internal_modules": [
                {
                    "module": str,
                    "department": str,
                    "duration": str,
                    "prerequisites": list,
                }
            ],
            "practice_tasks": [
                {
                    "task": str,
                    "skill": str,
                    "difficulty": str,
                    "estimated_hours": int,
                }
            ],
        }

        try:
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert learning and development specialist for Škoda AUTO. Create detailed, actionable training plans.",
                    temperature=0.6,
                    max_tokens=2500,
                )

            # Force Azure mode - check if result is valid
            if result and (result.get("plan_overview") or result.get("weekly_breakdown")):
                result["ai_mode"] = "azure"
                return result
            else:
                logger.warning(f"Training plan returned empty/invalid result, retrying...")
                # Retry once more
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert learning and development specialist for Škoda AUTO. Create detailed, actionable training plans.",
                    temperature=0.6,
                    max_tokens=2500,
                )
                if result and (result.get("plan_overview") or result.get("weekly_breakdown")):
                    result["ai_mode"] = "azure"
                    return result

        except Exception as exc:
            logger.error(f"Training plan generation failed (retrying): {exc}", exc_info=True)
            # Retry once more before raising exception
            try:
                async with LLMClient(self.llm_config) as llm:
                    result = await llm.call_llm(
                        prompt=prompt,
                        schema=schema,
                        system_message="You are an expert learning and development specialist for Škoda AUTO. Create detailed, actionable training plans.",
                        temperature=0.6,
                        max_tokens=2500,
                    )
                    if result and (result.get("plan_overview") or result.get("weekly_breakdown")):
                        result["ai_mode"] = "azure"
                        return result
            except Exception as retry_exc:
                logger.error(f"Training plan retry also failed: {retry_exc}")
                # NO FALLBACK - raise exception if Azure fails after retries
                raise RuntimeError(f"Training plan generation failed after retries. Azure OpenAI is required and not responding correctly: {retry_exc}") from retry_exc
        
        # If we get here, the first attempt failed but retry succeeded
        # This should not happen, but just in case:
        logger.error(f"Training plan generation failed after retries - Azure OpenAI required")
        raise RuntimeError(f"Training plan generation failed after retries. Azure OpenAI is required and not responding correctly: {exc}") from exc

    async def _gather_employee_context(
        self,
        session: AsyncSession,
        employee_id: Optional[str],
        skills: List[str],
    ) -> Dict[str, Any]:
        """Gather employee context from database or provided data."""
        employee_data = {
            "employee_id": employee_id or "anonymous",
            "skills": skills,
            "metadata": {},
        }

        if employee_id:
            try:
                employee_record = await self.employee_repo.get_by_employee_id(
                    session, employee_id
                )
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
        self,
        session: AsyncSession,
        employee_data: Dict[str, Any],
        gaps: List[str],
    ) -> Dict[str, Any]:
        """Get skill recommendations."""
        try:
            result = await self.recommendations_service.recommend_skills(
                session,
                employee_data,
                None,
            )
            # Enhance with gap-focused recommendations
            if gaps:
                gap_recs = [
                    {"skill": gap, "priority": "high", "reason": "Identified gap"}
                    for gap in gaps
                ]
                result["items"].extend(gap_recs)
            return result
        except Exception as e:
            logger.warning(f"Recommendations failed: {e}")
            return {"items": []}

    async def _assess_role_readiness(
        self,
        session: AsyncSession,
        employee_data: Dict[str, Any],
        desired_role: str,
    ) -> Dict[str, Any]:
        """Assess readiness for desired role."""
        try:
            role_requirements = {
                "title": desired_role,
                "required_skills": employee_data.get("skills", []),
            }
            # Use analyze_employee with role requirements
            analysis = await self.ai_service.analyze_employee(
                session,
                employee_data["employee_id"],
                employee_data,
                role_requirements,
            )
            return {
                "readiness_score": analysis.get("ai_readiness", 60),
                "role_fit_score": analysis.get("role_fit_score", 60),
            }
        except Exception as e:
            logger.warning(f"Role readiness assessment failed: {e}")
            return {"readiness_score": 60, "role_fit_score": 60}

    def _build_training_plan_prompt(
        self,
        employee_data: Dict[str, Any],
        skills: List[str],
        gaps: List[str],
        desired_role: str,
        analytics: Dict[str, Any],
        recommendations: Dict[str, Any],
        role_readiness: Dict[str, Any],
    ) -> str:
        """Build comprehensive prompt for training plan generation."""
        employee_id = employee_data.get("employee_id", "Employee")
        department = employee_data.get("department", "Unknown")
        current_skills = skills or employee_data.get("skills", [])

        readiness_score = role_readiness.get("readiness_score", 60)
        skill_diversity = analytics.get("skill_level_stats", {}).get("skill_diversity", 0)
        rec_items = recommendations.get("items", [])
        recommended_skills = [r.get("skill", "") for r in rec_items[:10] if r.get("skill")]

        prompt = f"""Generate a comprehensive, personalized training plan for a Škoda employee.

Employee Profile:
- ID: {employee_id}
- Department: {department}
- Current Skills: {', '.join(current_skills) if current_skills else 'None listed'}
- Skill Gaps: {', '.join(gaps) if gaps else 'None specified'}
- Desired Role: {desired_role}

Current Assessment:
- Readiness Score: {readiness_score}/100
- Skill Diversity: {skill_diversity:.1f}
- Recommended Skills: {', '.join(recommended_skills) if recommended_skills else 'None'}

Create a detailed training plan that includes:

1. Plan Overview: 2-3 paragraph summary of the training journey
2. Weekly Breakdown: 12-16 weeks of structured learning
   - Week number
   - Focus skills for that week
   - Courses to complete
   - Practice tasks
   - Milestones to achieve

3. Courses: Mix of external and internal courses
   - Course name
   - Provider (e.g., "Škoda Academy", "Coursera", "Udemy", "Internal")
   - Duration in hours
   - Type (e.g., "Online", "In-person", "Workshop", "Self-paced")
   - Priority (high, medium, low)
   - Whether it's a Škoda Academy module (boolean)

4. Skill Progression Map: How each skill develops over time
   - Skill name
   - Current level (beginner, intermediate, advanced)
   - Target level
   - Weeks to master
   - Dependencies (other skills needed first)

5. Mentors: Recommended internal mentors
   - Name (can be generic like "Senior Engineer in Battery Systems")
   - Expertise areas
   - Availability (e.g., "Weekly 1-on-1", "Monthly check-in")
   - Recommended for (which skills/areas)

6. Risks: Potential challenges and mitigations
   - Risk description
   - Severity (high, medium, low)
   - Mitigation strategy

7. Time to Readiness: Estimated weeks/months to reach desired role readiness

8. Internal Modules: Škoda Academy specific modules
   - Module name
   - Department offering it
   - Duration
   - Prerequisites

9. Practice Tasks: Hands-on projects and exercises
   - Task description
   - Related skill
   - Difficulty (beginner, intermediate, advanced)
   - Estimated hours

Make the plan realistic, actionable, and tailored to Škoda's automotive industry context.
Focus on practical skills that will help the employee succeed in {desired_role}.
"""

        return prompt

    def _fallback_training_plan(
        self,
        skills: List[str],
        gaps: List[str],
        desired_role: str,
        analytics: Dict[str, Any],
        recommendations: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback training plan when AI fails."""
        readiness = analytics.get("readiness_score", 60)
        weeks_needed = max(12, 24 - (readiness // 5))

        return {
            "plan_overview": f"This training plan will help you progress toward {desired_role}. Focus on developing {', '.join(gaps[:3]) if gaps else 'key skills'} over the next {weeks_needed} weeks.",
            "weekly_breakdown": [
                {
                    "week": i + 1,
                    "focus_skills": gaps[:2] if gaps else ["Core skills"],
                    "courses": [f"Course {i + 1}"],
                    "practice_tasks": [f"Practice task {i + 1}"],
                    "milestones": [f"Week {i + 1} milestone"],
                }
                for i in range(min(12, weeks_needed))
            ],
            "courses": [
                {
                    "name": f"Training for {gap}",
                    "provider": "Škoda Academy",
                    "duration_hours": 20,
                    "type": "Online",
                    "priority": "high",
                    "skoda_academy": True,
                }
                for gap in gaps[:5]
            ],
            "skill_progression_map": [
                {
                    "skill": gap,
                    "current_level": "beginner",
                    "target_level": "intermediate",
                    "weeks_to_master": 4,
                    "dependencies": [],
                }
                for gap in gaps[:5]
            ],
            "mentors": [
                {
                    "name": f"Senior {desired_role}",
                    "expertise": gaps[:3] if gaps else ["General"],
                    "availability": "Monthly check-in",
                    "recommended_for": gaps[:2] if gaps else ["Core skills"],
                }
            ],
            "risks": [
                {
                    "risk": "Time management",
                    "severity": "medium",
                    "mitigation": "Schedule dedicated learning time each week",
                }
            ],
            "time_to_readiness": weeks_needed,
            "internal_modules": [
                {
                    "module": f"{desired_role} Fundamentals",
                    "department": "Learning & Development",
                    "duration": "4 weeks",
                    "prerequisites": skills[:2] if skills else [],
                }
            ],
            "practice_tasks": [
                {
                    "task": f"Practice {gap}",
                    "skill": gap,
                    "difficulty": "intermediate",
                    "estimated_hours": 10,
                }
                for gap in gaps[:5]
            ],
            "ai_mode": "heuristic",
        }

