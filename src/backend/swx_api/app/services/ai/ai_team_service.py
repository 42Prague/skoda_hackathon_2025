"""
AI Team Service
---------------
AI-powered team health analysis.
"""

from typing import Any, Dict, List

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AITeamSummary
from swx_api.core.middleware.logging_middleware import logger


class AITeamService:
    """AI service for team analysis."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def generate_summary(
        self,
        team_data: List[Dict[str, Any]],
        department: str,
        skill_coverage: Dict[str, int],
        risk_indicators: Dict[str, Any],
        language: str = None
    ) -> AITeamSummary:
        """Generate executive team health summary."""
        schema = {
            "summary": str,
            "team_strengths": list,
            "critical_gaps": list,
            "health_score": int,
            "risk_level": str,
            "recommendations": list,
            "skill_distribution": dict,
            "readiness_breakdown": dict,
        }
        
        variables = {
            "team_data": team_data,
            "department": department,
            "skill_coverage": skill_coverage,
            "risk_indicators": risk_indicators,
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="team_summary",
                variables=variables,
                schema=schema,
                language=language
            )
            
            # Verify Azure was used
            if result.get("ai_mode") != "azure":
                logger.error(f"AI team summary did not use Azure, ai_mode={result.get('ai_mode')}")
                raise RuntimeError(f"AI team summary must use Azure. Got ai_mode={result.get('ai_mode')}")
            
            return AITeamSummary(**result)
        except Exception as exc:
            logger.error(f"AI team summary failed: {exc}", exc_info=True)
            # NO FALLBACK - raise exception
            raise RuntimeError(f"AI team summary failed. Azure OpenAI is required: {exc}") from exc

