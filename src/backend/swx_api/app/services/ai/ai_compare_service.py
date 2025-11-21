"""
AI Compare Service
-----------------
AI-powered department comparison.
"""

from typing import Any, Dict

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AIDepartmentComparison
from swx_api.core.middleware.logging_middleware import logger


class AICompareService:
    """AI service for department comparison."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def compare_departments(
        self,
        department1_data: Dict[str, Any],
        department2_data: Dict[str, Any],
        metrics: Dict[str, Any],
        language: str = None
    ) -> AIDepartmentComparison:
        """Compare two departments and provide insights."""
        schema = {
            "comparison_summary": str,
            "department1_strengths": list,
            "department2_strengths": list,
            "skill_overlap": list,
            "talent_transfer_opportunities": list,
            "risk_comparison": dict,
            "recommendations": list,
            "relative_performance": dict,
        }
        
        variables = {
            "department1_data": department1_data,
            "department2_data": department2_data,
            "metrics": metrics,
        }
        
        try:
            result = await self.orchestrator.run(
                prompt_name="department_compare",
                variables=variables,
                schema=schema,
                language=language
            )
            
            # Verify Azure mode is set
            if result and result.get("ai_mode") == "azure":
                return AIDepartmentComparison(**result)
            else:
                # Retry once if Azure didn't work
                logger.warning(f"AI department comparison didn't use Azure, retrying...")
                result = await self.orchestrator.run(
                    prompt_name="department_compare",
                    variables=variables,
                    schema=schema,
                    language=language
                )
                if result and result.get("ai_mode") == "azure":
                    return AIDepartmentComparison(**result)
                
                # NO FALLBACK - raise exception if Azure not used after retry
                logger.error(f"AI department comparison failed to use Azure after retry, ai_mode={result.get('ai_mode')}")
                raise RuntimeError(f"AI department comparison must use Azure. Got ai_mode={result.get('ai_mode')}")
            
        except Exception as exc:
            logger.error(f"AI department comparison failed: {exc}, retrying...", exc_info=True)
            # Retry once more
            try:
                result = await self.orchestrator.run(
                    prompt_name="department_compare",
                    variables=variables,
                    schema=schema,
                    language=language
                )
                # Verify Azure was used
                if result.get("ai_mode") != "azure":
                    raise RuntimeError(f"AI department comparison must use Azure. Got ai_mode={result.get('ai_mode')}")
                return AIDepartmentComparison(**result)
            except Exception as retry_exc:
                logger.error(f"AI department comparison retry also failed: {retry_exc}")
                # NO FALLBACK - raise exception
                raise RuntimeError(f"AI department comparison failed after retries. Azure OpenAI is required: {retry_exc}") from retry_exc

