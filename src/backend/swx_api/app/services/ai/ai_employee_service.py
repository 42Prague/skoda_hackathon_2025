"""
AI Employee Service
-------------------
AI-powered employee analysis and summarization.
"""

from typing import Any, Dict, List, Optional

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AIEmployeeSummary
from swx_api.core.middleware.logging_middleware import logger


class AIEmployeeService:
    """AI service for employee analysis."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def generate_summary(
        self,
        employee_data: Dict[str, Any],
        skills: List[str],
        history: Optional[List[Dict[str, Any]]] = None,
        qualifications: Optional[List[Dict[str, Any]]] = None,
        language: str = None
    ) -> AIEmployeeSummary:
        """Generate executive employee summary."""
        schema = {
            "summary": str,
            "strengths": list,
            "development_areas": list,
            "readiness_score": int,
            "next_role_readiness": str,
            "recommended_actions": list,
            "risk_signals": list,
            "career_trajectory": str,
        }
        
        variables = {
            "employee_data": employee_data,
            "skills": skills,
            "history": history or [],
            "qualifications": qualifications or [],
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="employee_summary",
                variables=variables,
                schema=schema,
                language=language
            )
            
            # Verify Azure was used (AIOrchestrator always sets ai_mode="azure" on success)
            if result.get("ai_mode") != "azure":
                logger.error(f"AI employee summary did not use Azure, ai_mode={result.get('ai_mode')}")
                raise RuntimeError(f"AI employee summary must use Azure. Got ai_mode={result.get('ai_mode')}")
            
            # Verify result is not empty
            if not result or not result.get("summary"):
                logger.error("AI employee summary returned empty result")
                raise ValueError("AI employee summary returned empty result from Azure OpenAI")
            
            return AIEmployeeSummary(**result)
        except Exception as exc:
            logger.error(f"AI employee summary failed: {exc}", exc_info=True)
            # NO FALLBACK - raise exception
            raise RuntimeError(f"AI employee summary failed. Azure OpenAI is required: {exc}") from exc

