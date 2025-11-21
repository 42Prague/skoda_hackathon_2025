"""
AI Role Fit Service
-------------------
AI-powered role matching and fit analysis.
"""

from typing import Any, Dict, Optional

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AIRoleFitSummary
from swx_api.core.middleware.logging_middleware import logger


class AIRoleFitService:
    """AI service for role fit analysis."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def assess_fit(
        self,
        employee_data: Dict[str, Any],
        target_role: Dict[str, Any],
        requirements: Dict[str, Any],
        language: str = None
    ) -> AIRoleFitSummary:
        """Assess employee fit for target role."""
        schema = {
            "fit_score": int,
            "matching_skills": list,
            "missing_skills": list,
            "readiness_timeline": str,
            "development_path": list,
            "strengths": list,
            "gaps": list,
            "recommendation": str,
        }
        
        variables = {
            "employee_data": employee_data,
            "target_role": target_role,
            "requirements": requirements,
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="role_fit",
                variables=variables,
                schema=schema,
                language=language
            )
            
            return AIRoleFitSummary(**result)
        except Exception as exc:
            logger.error(f"AI role fit assessment failed: {exc}", exc_info=True)
            return AIRoleFitSummary(
                summary=f"Role fit analysis unavailable: {str(exc)}",
                ai_mode="fallback"
            )

