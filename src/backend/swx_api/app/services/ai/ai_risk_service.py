"""
AI Risk Service
--------------
AI-powered risk assessment and signal detection.
"""

from typing import Any, Dict, List, Optional

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AIRiskSignals
from swx_api.core.middleware.logging_middleware import logger


class AIRiskService:
    """AI service for risk assessment."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def assess_risks(
        self,
        metrics: Dict[str, Any],
        employee_data: Optional[Dict[str, Any]] = None,
        team_data: Optional[List[Dict[str, Any]]] = None,
        language: Optional[str] = None,
    ) -> AIRiskSignals:
        """Identify and explain risk signals."""
        schema = {
            "risk_signals": list,
            "risk_score": int,
            "risk_factors": list,
            "mitigation_recommendations": list,
            "priority": str,
            "timeline": str,
        }
        
        variables = {
            "employee_data": employee_data or {},
            "team_data": team_data or [],
            "metrics": metrics,
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="risk_signal",
                variables=variables,
                schema=schema,
                language=language
            )
            
            return AIRiskSignals(**result)
        except Exception as exc:
            logger.error(f"AI risk assessment failed: {exc}", exc_info=True)
            return AIRiskSignals(
                summary=f"Risk assessment unavailable: {str(exc)}",
                ai_mode="fallback"
            )

