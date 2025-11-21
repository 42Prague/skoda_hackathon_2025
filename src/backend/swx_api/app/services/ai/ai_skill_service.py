"""
AI Skill Service
---------------
AI-powered skill extraction and normalization.
"""

from typing import Any, Dict, List

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AISkillExtraction
from swx_api.core.middleware.logging_middleware import logger


class AISkillService:
    """AI service for skill extraction and normalization."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def extract_skills(
        self,
        employee_data: Dict[str, Any],
        language: str = None
    ) -> AISkillExtraction:
        """Extract and normalize skills from employee data."""
        schema = {
            "extracted_skills": list,
            "normalized_skills": list,
            "proficiency_levels": dict,
            "ontology_matches": dict,
            "confidence_scores": dict,
        }
        
        variables = {
            "employee_data": employee_data
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="skill_extraction",
                variables=variables,
                schema=schema,
                language=language
            )
            
            return AISkillExtraction(**result)
        except Exception as exc:
            logger.error(f"AI skill extraction failed: {exc}", exc_info=True)
            return AISkillExtraction(
                summary=f"Skill extraction unavailable: {str(exc)}",
                ai_mode="fallback"
            )

