"""
Async What-If Simulation Engine
--------------------------------
Simulates scenarios like department changes, training completion,
and skill requirement changes to predict impacts using async services.
"""

import json
import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("scenario_simulation")


class ScenarioSimulationService:
    """Async service for simulating organizational scenarios."""
    
    def __init__(self):
        self.llm_config = LLMConfig.from_env()
        self.analytics_service = SkillAnalyticsService()
    
    def simulate_scenario(
        self,
        scenario_type: str,
        scenario_params: Dict[str, Any],
        current_state: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simulate a what-if scenario (sync/async compatible).
        
        Can be called from sync or async contexts. In sync contexts, automatically
        runs the async implementation.
        """
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            raise RuntimeError("Cannot call sync wrapper from async context - use await simulate_scenario_async()")
        except RuntimeError as e:
            if "Cannot call sync wrapper" in str(e):
                raise
            # No event loop running, run in sync mode
            import asyncio
            return asyncio.run(self._simulate_scenario_async(scenario_type, scenario_params, current_state))

    async def simulate_scenario_async(
        self,
        scenario_type: str,
        scenario_params: Dict[str, Any],
        current_state: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Async version of simulate_scenario - use this in async contexts."""
        return await self._simulate_scenario_async(scenario_type, scenario_params, current_state)

    async def _simulate_scenario_async(
        self,
        scenario_type: str,
        scenario_params: Dict[str, Any],
        current_state: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Simulate a what-if scenario.
        
        Args:
            scenario_type: Type of scenario ("employee_loss", "training_completion", "skill_mandatory")
            scenario_params: Scenario-specific parameters
            current_state: Current employee state
            
        Returns:
            Dictionary with:
            - impact_predictions: Predicted impacts
            - new_risk_scores: Updated risk scores
            - changed_heatmaps: Updated skill heatmaps
            - affected_departments: List of affected departments
            - recommendations: Mitigation recommendations
        """
        try:
            # Create simulated state
            simulated_state = self._apply_scenario(current_state, scenario_type, scenario_params)
            
            # Compute impacts (async)
            impacts = await self._compute_impacts(current_state, simulated_state, scenario_type)
            
            # Get AI-powered predictions (async)
            ai_predictions = await self._get_ai_predictions(
                scenario_type,
                scenario_params,
                current_state,
                simulated_state,
                impacts
            )
            
            # Calculate new risk scores (async)
            new_risk_scores = await self._calculate_risk_scores(simulated_state)
            
            # Generate updated heatmaps (async)
            changed_heatmaps = await self._generate_heatmaps(simulated_state)
            
            # Identify affected departments
            affected_departments = self._identify_affected_departments(
                current_state,
                simulated_state
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                scenario_type,
                impacts,
                new_risk_scores
            )
            
            return {
                "scenario_type": scenario_type,
                "scenario_params": scenario_params,
                "impact_predictions": impacts,
                "ai_insights": ai_predictions,
                "new_risk_scores": new_risk_scores,
                "changed_heatmaps": changed_heatmaps,
                "affected_departments": affected_departments,
                "recommendations": recommendations,
                "simulated_at": json.dumps({"$date": None}),
            }
            
        except Exception as e:
            logger.error(f"Error simulating scenario: {e}", exc_info=True)
            return {
                "scenario_type": scenario_type,
                "error": str(e),
                "impact_predictions": {},
                "new_risk_scores": {},
                "changed_heatmaps": {}
            }
    
    def _apply_scenario(
        self,
        current_state: List[Dict[str, Any]],
        scenario_type: str,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply scenario to current state to create simulated state."""
        simulated_state = [emp.copy() for emp in current_state]
        
        if scenario_type == "employee_loss":
            # Remove employees
            employee_ids = params.get("employee_ids", [])
            simulated_state = [
                emp for emp in simulated_state
                if emp.get("employee_id") not in employee_ids
            ]
        
        elif scenario_type == "training_completion":
            # Add skills to employees who complete training
            training_skill = params.get("skill")
            employee_ids = params.get("employee_ids", [])
            
            for emp in simulated_state:
                if emp.get("employee_id") in employee_ids:
                    skills = emp.get("skills", [])
                    if training_skill not in skills:
                        skills.append(training_skill)
                    emp["skills"] = skills
        
        elif scenario_type == "skill_mandatory":
            # Mark skill as mandatory (affects risk calculations)
            mandatory_skill = params.get("skill")
            # This affects analysis, not the state itself
            pass
        
        return simulated_state
    
    async def _compute_impacts(
        self,
        current_state: List[Dict[str, Any]],
        simulated_state: List[Dict[str, Any]],
        scenario_type: str
    ) -> Dict[str, Any]:
        """Compute impacts of the scenario."""
        # Current analytics (async)
        current_analytics = await self.analytics_service.analyze_global(current_state)
        
        # Simulated analytics (async)
        simulated_analytics = await self.analytics_service.analyze_global(simulated_state)
        
        # Calculate differences
        current_freq = current_analytics.get("skill_frequency", {})
        simulated_freq = simulated_analytics.get("skill_frequency", {})
        
        skill_impacts = {}
        for skill in set(list(current_freq.keys()) + list(simulated_freq.keys())):
            current_count = current_freq.get(skill, 0)
            simulated_count = simulated_freq.get(skill, 0)
            change = simulated_count - current_count
            change_pct = (change / current_count * 100) if current_count > 0 else 0
            
            skill_impacts[skill] = {
                "current_count": current_count,
                "simulated_count": simulated_count,
                "change": change,
                "change_percentage": round(change_pct, 2)
            }
        
        # Department impacts
        current_depts = defaultdict(int)
        simulated_depts = defaultdict(int)
        
        for emp in current_state:
            dept = emp.get("department", "Unknown")
            current_depts[dept] += 1
        
        for emp in simulated_state:
            dept = emp.get("department", "Unknown")
            simulated_depts[dept] += 1
        
        dept_impacts = {}
        for dept in set(list(current_depts.keys()) + list(simulated_depts.keys())):
            current_size = current_depts.get(dept, 0)
            simulated_size = simulated_depts.get(dept, 0)
            change = simulated_size - current_size
            
            dept_impacts[dept] = {
                "current_size": current_size,
                "simulated_size": simulated_size,
                "change": change,
                "change_percentage": round((change / current_size * 100) if current_size > 0 else 0, 2)
            }
        
        return {
            "employee_count_change": len(simulated_state) - len(current_state),
            "skill_impacts": skill_impacts,
            "department_impacts": dept_impacts,
            "total_skills_affected": len([s for s in skill_impacts.values() if s["change"] != 0])
        }
    
    async def _get_ai_predictions(
        self,
        scenario_type: str,
        params: Dict[str, Any],
        current_state: List[Dict[str, Any]],
        simulated_state: List[Dict[str, Any]],
        impacts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get AI-powered predictions for the scenario with async support."""
        try:
            prompt = self._build_simulation_prompt(
                scenario_type,
                params,
                impacts
            )
            
            schema = {
                "summary": str,
                "key_risks": list,
                "mitigation_strategies": list,
                "timeline_impact": str,
                "resource_requirements": list
            }
            
            # Use async LLM client
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert organizational analyst.",
                    temperature=0.7,
                    max_tokens=2000
                )
            
            return result
        except Exception as e:
            logger.warning(f"AI predictions failed: {e}")
        
        # Fallback
        return {
            "summary": f"Scenario {scenario_type} simulated",
            "key_risks": ["Risk assessment pending"],
            "mitigation_strategies": ["Review impacts and plan mitigation"],
            "timeline_impact": "To be determined",
            "resource_requirements": []
        }
    
    def _build_simulation_prompt(
        self,
        scenario_type: str,
        params: Dict[str, Any],
        impacts: Dict[str, Any]
    ) -> str:
        """Build prompt for scenario simulation."""
        return f"""Analyze the impact of a simulated organizational scenario.

Scenario Type: {scenario_type}
Parameters: {json.dumps(params, indent=2)}

Impacts:
- Employee Count Change: {impacts.get('employee_count_change', 0)}
- Skills Affected: {impacts.get('total_skills_affected', 0)}
- Department Changes: {len(impacts.get('department_impacts', {}))}

Provide analysis with:
{{
  "summary": "brief impact summary",
  "key_risks": ["risk 1", "risk 2"],
  "mitigation_strategies": ["strategy 1", "strategy 2"],
  "timeline_impact": "estimated timeline impact",
  "resource_requirements": ["resource 1", "resource 2"]
}}

Response (JSON only):"""
    
    async def _calculate_risk_scores(
        self,
        simulated_state: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate risk scores for simulated state."""
        # Group by department
        department_data = defaultdict(list)
        for emp in simulated_state:
            dept = emp.get("department", "Unknown")
            department_data[dept].append(emp)
        
        risk_scores = {}
        for dept, employees in department_data.items():
            dept_analytics = await self.analytics_service.analyze_department(dept, employees)
            risk_scores[dept] = dept_analytics.get("risk_scores", {})
        
        # Global risk
        global_analytics = await self.analytics_service.analyze_global(simulated_state)
        risk_scores["global"] = {
            "skill_gap_risk": len(global_analytics.get("skill_gaps", [])) * 5,
            "retention_risk": 30 if len(simulated_state) < 50 else 20
        }
        
        return risk_scores
    
    async def _generate_heatmaps(
        self,
        simulated_state: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate updated skill heatmaps."""
        # Group by department
        department_data = defaultdict(list)
        for emp in simulated_state:
            dept = emp.get("department", "Unknown")
            department_data[dept].append(emp)
        
        heatmaps = {}
        for dept, employees in department_data.items():
            dept_analytics = await self.analytics_service.analyze_department(dept, employees)
            heatmaps[dept] = dept_analytics.get("team_skill_heatmap", {})
        
        # Global heatmap
        global_analytics = await self.analytics_service.analyze_global(simulated_state)
        heatmaps["global"] = global_analytics.get("skill_frequency", {})
        
        return heatmaps
    
    def _identify_affected_departments(
        self,
        current_state: List[Dict[str, Any]],
        simulated_state: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify departments affected by the scenario."""
        current_depts = defaultdict(int)
        simulated_depts = defaultdict(int)
        
        for emp in current_state:
            dept = emp.get("department", "Unknown")
            current_depts[dept] += 1
        
        for emp in simulated_state:
            dept = emp.get("department", "Unknown")
            simulated_depts[dept] += 1
        
        affected = []
        for dept in set(list(current_depts.keys()) + list(simulated_depts.keys())):
            current_size = current_depts.get(dept, 0)
            simulated_size = simulated_depts.get(dept, 0)
            
            if current_size != simulated_size:
                affected.append({
                    "department": dept,
                    "current_size": current_size,
                    "simulated_size": simulated_size,
                    "change": simulated_size - current_size,
                    "impact_level": "high" if abs(simulated_size - current_size) >= 3 else "medium"
                })
        
        return affected
    
    def _generate_recommendations(
        self,
        scenario_type: str,
        impacts: Dict[str, Any],
        risk_scores: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate mitigation recommendations."""
        recommendations = []
        
        if scenario_type == "employee_loss":
            employee_loss = abs(impacts.get("employee_count_change", 0))
            if employee_loss > 0:
                recommendations.append({
                    "type": "hiring",
                    "priority": "high",
                    "action": f"Consider hiring {employee_loss} replacement(s)",
                    "reason": "Employee loss creates skill gaps"
                })
                
                recommendations.append({
                    "type": "knowledge_transfer",
                    "priority": "high",
                    "action": "Initiate knowledge transfer sessions",
                    "reason": "Preserve institutional knowledge"
                })
        
        elif scenario_type == "training_completion":
            recommendations.append({
                "type": "deployment",
                "priority": "medium",
                "action": "Deploy newly trained employees to relevant projects",
                "reason": "Maximize ROI on training investment"
            })
        
        # Risk-based recommendations
        for dept, risks in risk_scores.items():
            if isinstance(risks, dict):
                skill_gap_risk = risks.get("skill_gap_risk", 0)
                if skill_gap_risk > 50:
                    recommendations.append({
                        "type": "training",
                        "priority": "high",
                        "action": f"Address skill gaps in {dept}",
                        "reason": f"High skill gap risk: {skill_gap_risk}"
                    })
        
        return recommendations
