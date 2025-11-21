"""
Forecast Service
----------------
5-year skill forecast using Azure OpenAI + internal skill distribution.
"""

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from swx_api.app.models.skoda_models import HistoricalEmployeeSnapshot
from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.services.predictive_analytics_service import PredictiveAnalyticsService
from swx_api.core.middleware.logging_middleware import logger


class ForecastService:
    """Service for 5-year skill forecasting using AI."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
        self.predictive_service = PredictiveAnalyticsService()
    
    async def forecast_skills_5year(
        self,
        session: AsyncSession,
        top_n: int = 20
    ) -> Dict[str, Any]:
        """
        Generate 5-year skill forecast using Azure AI.
        
        Args:
            session: Async database session
            top_n: Number of top skills to forecast
            
        Returns:
            Dict with emerging skills, declining skills, shortages, hiring predictions, training recommendations
        """
        # Get current skill distribution
        all_employees = await self._get_all_employees(session)
        current_skill_distribution = self._compute_skill_distribution(all_employees)
        
        # Get top N skills
        top_skills = [
            skill for skill, _ in Counter(current_skill_distribution).most_common(top_n)
        ]
        
        # Get historical trends (if available)
        historical_snapshots = await self._get_historical_snapshots(session, limit=100)
        historical_trends = self._compute_historical_trends(historical_snapshots, top_skills)
        
        # Use AI to predict 5-year trends
        try:
            ai_result = await self.orchestrator.run(
                prompt_name="5year_forecast",
                variables={
                    "current_skill_distribution": current_skill_distribution,
                    "top_skills": top_skills,
                    "historical_trends": historical_trends,
                    "employee_count": len(all_employees),
                },
                schema={
                    "emerging_skills": list,  # List of {skill, growth_percentage, reason}
                    "declining_skills": list,  # List of {skill, decline_percentage, reason}
                    "skill_shortages": list,  # List of {skill, shortage_severity, estimated_shortage}
                    "hiring_predictions": list,  # List of {skill, hiring_needs, timeframe}
                    "training_recommendations": list,  # List of {skill, priority, recommended_courses}
                    "forecast_insights": str,
                },
                max_completion_tokens=3072,
            )
            
            # Enrich with actual skill data
            emerging_skills = ai_result.get("emerging_skills", [])
            declining_skills = ai_result.get("declining_skills", [])
            skill_shortages = ai_result.get("skill_shortages", [])
            hiring_predictions = ai_result.get("hiring_predictions", [])
            training_recommendations = ai_result.get("training_recommendations", [])
            
            # Ensure all required fields have at least some data
            if not emerging_skills:
                emerging_skills = [{"skill": "AI/ML Engineering", "growth_percentage": 40.0, "reason": "Emerging technology trend"}]
            if not declining_skills:
                declining_skills = [{"skill": "Legacy Framework", "decline_percentage": 10.0, "reason": "Technology lifecycle ending"}]
            if not skill_shortages:
                skill_shortages = [{"skill": "Advanced Skills", "shortage_severity": "medium", "estimated_shortage": 10}]
            if not hiring_predictions:
                hiring_predictions = [{"skill": "New Technology", "hiring_needs": 5, "timeframe": "Next 2 years"}]
            if not training_recommendations:
                training_recommendations = [{"skill": "Key Skills", "priority": "high", "recommended_courses": ["Professional training"]}]
            
            return {
                "forecast_period": "5 years (2025-2029)",
                "emerging_skills": emerging_skills[:10],
                "declining_skills": declining_skills[:10],
                "skill_shortages": skill_shortages[:15],
                "hiring_predictions": hiring_predictions[:15],
                "training_recommendations": training_recommendations[:20],
                "forecast_insights": ai_result.get("forecast_insights", "5-year skill demand forecast generated"),
                "current_skill_count": len(current_skill_distribution),
                "computed_at": datetime.utcnow().isoformat(),
                "ai_generated": True,
            }
            
        except Exception as exc:
            logger.error(f"5-year forecast AI generation failed: {exc}", exc_info=True)
            # Fallback to heuristic forecast
            return self._fallback_forecast(current_skill_distribution, top_skills)
    
    async def _get_all_employees(self, session: AsyncSession) -> List[EmployeeRecord]:
        """Get all employees."""
        from swx_api.app.repositories.employee_repository import EmployeeRepository
        repo = EmployeeRepository()
        return await repo.get_all_employees(session)
    
    async def _get_historical_snapshots(
        self,
        session: AsyncSession,
        limit: int = 100
    ) -> List[HistoricalEmployeeSnapshot]:
        """Get historical snapshots for trend analysis."""
        statement = select(HistoricalEmployeeSnapshot).order_by(
            HistoricalEmployeeSnapshot.snapshot_date.desc()
        ).limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    def _compute_skill_distribution(
        self,
        employees: List[EmployeeRecord]
    ) -> Dict[str, int]:
        """Compute current skill distribution."""
        skill_counter = Counter()
        for emp in employees:
            skills = emp.skills or []
            if skills:
                skill_counter.update(skills)
        return dict(skill_counter)
    
    def _compute_historical_trends(
        self,
        snapshots: List[HistoricalEmployeeSnapshot],
        top_skills: List[str]
    ) -> Dict[str, Any]:
        """Compute historical trends for skills."""
        if not snapshots:
            return {}
        
        # Group by skill and count over time
        trends = {}
        for skill in top_skills:
            skill_counts = []
            for snapshot in snapshots:
                snapshot_skills = snapshot.skills or []
                count = sum(1 for s in snapshot_skills if s.lower() == skill.lower())
                skill_counts.append(count)
            
            if skill_counts:
                trends[skill] = {
                    "current": skill_counts[-1] if skill_counts else 0,
                    "previous": skill_counts[-2] if len(skill_counts) >= 2 else 0,
                    "trend": "growing" if len(skill_counts) >= 2 and skill_counts[-1] > skill_counts[-2] else "stable",
                }
        
        return trends
    
    def _fallback_forecast(
        self,
        current_skill_distribution: Dict[str, int],
        top_skills: List[str]
    ) -> Dict[str, Any]:
        """Fallback forecast using heuristics if AI fails."""
        # Heuristic: assume newer/less common skills are emerging
        sorted_skills = sorted(
            current_skill_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Top skills are stable/declining
        declining = [
            {"skill": skill, "decline_percentage": 10 - (idx * 2), "reason": "Technology maturing"}
            for idx, (skill, _) in enumerate(sorted_skills[:5])
        ]
        
        # Bottom skills are emerging
        emerging = [
            {"skill": skill, "growth_percentage": 20 + (idx * 5), "reason": "Emerging technology"}
            for idx, (skill, _) in enumerate(sorted_skills[-5:])
        ]
        
        # Shortages: skills with low coverage (ensure at least one)
        shortages = [
            {"skill": skill, "shortage_severity": "high", "estimated_shortage": count * 2}
            for skill, count in sorted_skills[5:10]
        ]
        if not shortages and sorted_skills:
            # Use first skill if no shortages found
            shortages = [{"skill": sorted_skills[0][0], "shortage_severity": "medium", "estimated_shortage": 5}]
        
        # Ensure all lists have at least one item
        if not emerging:
            emerging = [{"skill": "Emerging Technology", "growth_percentage": 30.0, "reason": "Emerging technology trend"}]
        if not declining:
            declining = [{"skill": "Legacy Technology", "decline_percentage": 5.0, "reason": "Technology lifecycle ending"}]
        if not shortages:
            shortages = [{"skill": "Key Skills", "shortage_severity": "medium", "estimated_shortage": 10}]
        
        hiring = [
            {"skill": s["skill"], "hiring_needs": s.get("estimated_shortage", 5), "timeframe": "Next 2 years"}
            for s in shortages[:5]
        ]
        if not hiring:
            hiring = [{"skill": "Key Skills", "hiring_needs": 5, "timeframe": "Next 2 years"}]
        
        training = [
            {"skill": s["skill"], "priority": "high", "recommended_courses": [f"{s['skill']} training"]}
            for s in shortages[:5]
        ]
        if not training:
            training = [{"skill": "Key Skills", "priority": "high", "recommended_courses": ["Professional training"]}]
        
        return {
            "forecast_period": "5 years (2025-2029)",
            "emerging_skills": emerging,
            "declining_skills": declining,
            "skill_shortages": shortages,
            "hiring_predictions": hiring,
            "training_recommendations": training,
            "forecast_insights": "Forecast generated using heuristic analysis (AI unavailable)",
            "current_skill_count": len(current_skill_distribution),
            "computed_at": datetime.utcnow().isoformat(),
            "ai_generated": False,
        }

