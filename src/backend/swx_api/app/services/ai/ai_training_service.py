"""
AI Training Service
------------------
AI-powered training recommendations.
"""

from typing import Any, Dict, List, Optional

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AITrainingPlan
from swx_api.core.middleware.logging_middleware import logger


class AITrainingService:
    """AI service for training recommendations."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def recommend_training(
        self,
        employee_data: Dict[str, Any],
        skill_gaps: List[str],
        career_goals: Optional[List[str]] = None,
        available_courses: Optional[List[Dict[str, Any]]] = None,
        language: str = None
    ) -> AITrainingPlan:
        """Recommend training plan for employee."""
        schema = {
            "training_plan": str,
            "recommended_courses": list,
            "skill_gaps_addressed": list,
            "estimated_duration": str,
            "expected_outcomes": list,
            "next_courses": list,
        }
        
        variables = {
            "employee_data": employee_data,
            "skill_gaps": skill_gaps,
            "career_goals": career_goals or [],
            "available_courses": available_courses or [],
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="training_recommendation",
                variables=variables,
                schema=schema,
                language=language
            )
            
            return AITrainingPlan(**result)
        except Exception as exc:
            logger.error(f"AI training recommendation failed: {exc}", exc_info=True)
            return AITrainingPlan(
                training_plan=f"Training recommendation unavailable: {str(exc)}",
                ai_mode="fallback"
            )

