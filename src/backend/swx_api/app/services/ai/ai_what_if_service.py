"""
AI What-If Service
-----------------
AI-powered scenario simulation and impact analysis.
"""

from typing import Any, Dict, List, Optional

from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.schemas.ai_schemas import AIEmployeeSummary, AITeamSummary
from swx_api.core.middleware.logging_middleware import logger


class AIWhatIfService:
    """AI service for what-if scenario analysis."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def simulate_scenario(
        self,
        scenario_type: str,
        base_data: Dict[str, Any],
        changes: Dict[str, Any],
        language: str = None
    ) -> Dict[str, Any]:
        """
        Simulate what-if scenario and analyze impact.
        
        Scenario types:
        - remove_employee
        - add_skill
        - remove_skill
        - complete_course
        - move_department
        """
        schema = {
            "impact_summary": str,
            "before_metrics": dict,
            "after_metrics": dict,
            "impact_score": int,
            "recommendations": list,
            "risks": list,
            "opportunities": list,
        }
        
        variables = {
            "scenario_type": scenario_type,
            "base_data": base_data,
            "changes": changes,
        }
        
        try:
            prompt = self._build_what_if_prompt(scenario_type, base_data, changes)
            
            result = await self.orchestrator.run(
                prompt_name="employee_summary",
                variables={"employee_data": prompt},
                schema=schema,
                language=language
            )
            
            # Verify Azure was used
            if result.get("ai_mode") != "azure":
                logger.error(f"AI what-if simulation did not use Azure, ai_mode={result.get('ai_mode')}")
                raise RuntimeError(f"AI what-if simulation must use Azure. Got ai_mode={result.get('ai_mode')}")
            
            return result
        except Exception as exc:
            logger.error(f"AI what-if simulation failed: {exc}", exc_info=True)
            # NO FALLBACK - raise exception
            raise RuntimeError(f"AI what-if simulation failed. Azure OpenAI is required: {exc}") from exc
    
    def _build_what_if_prompt(
        self,
        scenario_type: str,
        base_data: Dict[str, Any],
        changes: Dict[str, Any]
    ) -> str:
        """Build what-if scenario prompt."""
        scenarios = {
            "remove_employee": f"Simulate removing employee {changes.get('employee_id')} from {base_data.get('department')}",
            "add_skill": f"Simulate adding skill {changes.get('skill')} to employee {changes.get('employee_id')}",
            "remove_skill": f"Simulate removing skill {changes.get('skill')} from employee {changes.get('employee_id')}",
            "complete_course": f"Simulate employee {changes.get('employee_id')} completing course {changes.get('course')}",
            "move_department": f"Simulate moving employee {changes.get('employee_id')} from {base_data.get('department')} to {changes.get('new_department')}",
        }
        
        return scenarios.get(scenario_type, f"Simulate scenario: {scenario_type}")

