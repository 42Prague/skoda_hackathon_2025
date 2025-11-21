"""
AI Qualification Service
------------------------
AI-powered qualification normalization.
"""

from typing import Any, Dict

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AIQualificationNormalization
from swx_api.core.middleware.logging_middleware import logger


class AIQualificationService:
    """AI service for qualification normalization."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def normalize_qualification(
        self,
        qualification_data: Dict[str, Any],
        language: str = None
    ) -> AIQualificationNormalization:
        """Normalize qualification name and extract metadata."""
        schema = {
            "qualification_id": str,
            "name_cz": str,
            "name_en": str,
            "type": str,
            "mandatory_for_roles": list,
            "expiry_required": bool,
            "normalized": bool,
        }
        
        variables = {
            "qualification_data": qualification_data
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="qualification_normalization",
                variables=variables,
                schema=schema,
                language=language
            )
            
            return AIQualificationNormalization(**result)
        except Exception as exc:
            logger.error(f"AI qualification normalization failed: {exc}", exc_info=True)
            return AIQualificationNormalization(
                summary=f"Qualification normalization unavailable: {str(exc)}",
                ai_mode="fallback"
            )

