"""
AI Forecast Service
-------------------
AI-powered forecast explanation and insights.
"""

from typing import Any, Dict, List, Optional

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AIForecastExplanation
from swx_api.core.middleware.logging_middleware import logger


class AIForecastService:
    """AI service for forecast explanation."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def explain_forecast(
        self,
        forecast_data: Dict[str, Any],
        historical_trend: Optional[List[float]] = None,
        method: str = "arima",
        language: str = None
    ) -> AIForecastExplanation:
        """Explain skill demand forecast in executive terms."""
        schema = {
            "explanation": str,
            "key_trends": list,
            "insights": list,
            "confidence": int,
            "recommendations": list,
            "risk_factors": list,
            "opportunities": list,
        }
        
        variables = {
            "forecast_data": forecast_data,
            "historical_trend": historical_trend or [],
            "method": method,
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="forecast_explainer",
                variables=variables,
                schema=schema,
                language=language
            )
            
            return AIForecastExplanation(**result)
        except Exception as exc:
            logger.error(f"AI forecast explanation failed: {exc}", exc_info=True)
            return AIForecastExplanation(
                explanation=f"Forecast explanation unavailable: {str(exc)}",
                ai_mode="fallback"
            )

