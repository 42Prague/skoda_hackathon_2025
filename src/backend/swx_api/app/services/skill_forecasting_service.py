"""
Async Skill Forecasting Engine (AI-Powered)
-------------------------------------------
Predicts skill demand 3-12 months ahead, identifies emerging/declining skills,
and generates trend curves using async LLM client.
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import aiofiles

from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.ingestion_service import paths
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("skill_forecasting")


class SkillForecastingService:
    """Async AI-powered skill forecasting service."""
    
    def __init__(self):
        self.llm_config = LLMConfig.from_env()
        self.analysis_dir = paths.analysis_dir
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
    
    def forecast_skills(
        self,
        all_employees: List[Dict[str, Any]],
        forecast_horizon: str = "6m",
        use_historical: bool = True
    ) -> Dict[str, Any]:
        """
        Forecast skill demand (sync/async compatible).
        
        Can be called from sync or async contexts. In sync contexts, automatically
        runs the async implementation.
        """
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            raise RuntimeError("Cannot call sync wrapper from async context - use await forecast_skills_async()")
        except RuntimeError as e:
            if "Cannot call sync wrapper" in str(e):
                raise
            # No event loop running, run in sync mode
            import asyncio
            return asyncio.run(self._forecast_skills_async(all_employees, forecast_horizon, use_historical))

    async def forecast_skills_async(
        self,
        all_employees: List[Dict[str, Any]],
        forecast_horizon: str = "6m",
        use_historical: bool = True
    ) -> Dict[str, Any]:
        """Async version of forecast_skills - use this in async contexts."""
        return await self._forecast_skills_async(all_employees, forecast_horizon, use_historical)

    async def _forecast_skills_async(
        self,
        all_employees: List[Dict[str, Any]],
        forecast_horizon: str = "6m",
        use_historical: bool = True
    ) -> Dict[str, Any]:
        """
        Forecast skill demand and trends.
        
        Args:
            all_employees: List of employee records
            forecast_horizon: "3m", "6m", or "12m"
            use_historical: Whether to use historical data if available
            
        Returns:
            Dictionary with:
            - forecast_horizon: Forecast period
            - emerging_skills: List of emerging skills
            - declining_skills: List of declining skills
            - predicted_trend_curve: List of trend data points
            - confidence_score: Confidence in predictions (0-100)
        """
        try:
            # Parse horizon
            months = self._parse_horizon(forecast_horizon)
            
            # Get historical data if available (async file I/O)
            historical_data = None
            if use_historical:
                historical_data = await self._load_historical_data()
            
            # Generate baseline from current data
            baseline = self._generate_baseline(all_employees)
            
            # Prepare data for LLM
            forecast_prompt_data = {
                "current_skills": baseline["skill_frequency"],
                "historical_trends": historical_data or {},
                "forecast_months": months,
                "total_employees": len(all_employees),
            }
            
            # Get AI-powered forecast (async)
            ai_forecast = await self._get_ai_forecast(forecast_prompt_data, months)
            
            # Generate trend curve
            trend_curve = self._generate_trend_curve(
                baseline,
                ai_forecast,
                months
            )
            
            # Combine results
            result = {
                "forecast_horizon": forecast_horizon,
                "emerging_skills": ai_forecast.get("emerging_skills", []),
                "declining_skills": ai_forecast.get("declining_skills", []),
                "predicted_trend_curve": trend_curve,
                "confidence_score": ai_forecast.get("confidence_score", 70),
                "forecasted_at": datetime.utcnow().isoformat(),
            }
            
            # Save forecast (async)
            await self._save_forecast(result, forecast_horizon)
            
            return result
            
        except Exception as e:
            logger.error(f"Error forecasting skills: {e}", exc_info=True)
            # Fallback to rule-based forecast
            return self._fallback_forecast(all_employees, forecast_horizon)
    
    def _parse_horizon(self, horizon: str) -> int:
        """Parse forecast horizon string to months."""
        horizon = horizon.lower().strip()
        if horizon.endswith("m"):
            try:
                return int(horizon[:-1])
            except ValueError:
                pass
        # Default to 6 months
        return 6
    
    def _generate_baseline(
        self,
        all_employees: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate baseline skill frequency from current data."""
        skill_counter: Counter = Counter()
        department_skills: Dict[str, List[str]] = defaultdict(list)
        
        for emp in all_employees:
            skills = emp.get("skills", [])
            skill_counter.update(skills)
            
            dept = emp.get("department", "Unknown")
            department_skills[dept].extend(skills)
        
        # Calculate frequencies
        total_employees = len(all_employees)
        skill_frequency = {
            skill: {
                "count": count,
                "frequency": count / total_employees if total_employees > 0 else 0,
                "departments": list(set(
                    dept for dept, dept_skills in department_skills.items()
                    if skill in dept_skills
                ))
            }
            for skill, count in skill_counter.items()
        }
        
        return {
            "skill_frequency": skill_frequency,
            "total_employees": total_employees,
            "total_unique_skills": len(skill_counter),
            "department_distribution": {
                dept: len(set(skills)) for dept, skills in department_skills.items()
            }
        }
    
    async def _load_historical_data(self) -> Optional[Dict[str, Any]]:
        """Load historical skill data if available (async)."""
        # Check for historical analysis files
        historical_files = sorted(
            self.analysis_dir.glob("skill_trends_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if historical_files:
            try:
                async with aiofiles.open(historical_files[0], "r", encoding="utf-8") as f:
                    content = await f.read()
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"Failed to load historical data: {e}")
        
        return None
    
    async def _get_ai_forecast(
        self,
        data: Dict[str, Any],
        months: int
    ) -> Dict[str, Any]:
        """Get AI-powered forecast from LLM with async support."""
        prompt = self._build_forecast_prompt(data, months)
        
        schema = {
            "emerging_skills": list,
            "declining_skills": list,
            "confidence_score": int,
            "key_insights": list
        }
        
        try:
            # Use async LLM client
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert workforce planning and skill trend analyst.",
                    temperature=0.7,
                    max_tokens=3000
                )
            return self._validate_forecast_result(result)
            
        except Exception as e:
            logger.warning(f"AI forecast failed, using fallback: {e}")
            return self._fallback_forecast_logic(data, months)
    
    def _build_forecast_prompt(
        self,
        data: Dict[str, Any],
        months: int
    ) -> str:
        """Build prompt for skill forecasting."""
        current_skills = data.get("current_skills", {})
        historical = data.get("historical_trends", {})
        total_employees = data.get("total_employees", 0)
        
        # Format top skills
        top_skills = sorted(
            current_skills.items(),
            key=lambda x: x[1].get("count", 0) if isinstance(x[1], dict) else x[1],
            reverse=True
        )[:30]
        
        prompt = f"""Analyze skill trends and forecast demand for the next {months} months.

Current Skill Landscape:
- Total Employees: {total_employees}
- Top Skills (frequency):
"""
        
        for skill, info in top_skills[:15]:
            if isinstance(info, dict):
                count = info.get("count", 0)
                freq = info.get("frequency", 0) * 100
                depts = info.get("departments", [])
                prompt += f"  - {skill}: {count} employees ({freq:.1f}%), departments: {', '.join(depts[:3])}\n"
            else:
                prompt += f"  - {skill}: {info}\n"
        
        if historical:
            prompt += f"\nHistorical Trends Available: Yes\n"
        else:
            prompt += f"\nHistorical Trends Available: No (using synthetic baseline)\n"
        
        prompt += f"""
Based on industry trends, technology evolution, and organizational patterns, predict:

1. Emerging Skills: Skills that will gain importance in the next {months} months
2. Declining Skills: Skills that will become less relevant
3. Trend Direction: For each major skill, predict growth/decline/stable

Provide a JSON response with this structure:
{{
  "emerging_skills": [
    {{
      "skill": "skill name",
      "current_frequency": 0.15,
      "predicted_frequency": 0.25,
      "growth_rate": 0.67,
      "reason": "brief explanation"
    }}
  ],
  "declining_skills": [
    {{
      "skill": "skill name",
      "current_frequency": 0.20,
      "predicted_frequency": 0.12,
      "decline_rate": -0.40,
      "reason": "brief explanation"
    }}
  ],
  "confidence_score": 75,
  "key_insights": ["insight 1", "insight 2"]
}}

Focus on realistic predictions based on:
- Technology trends (AI, cloud, automation)
- Industry standards
- Organizational growth patterns
- Skill interdependencies

Response (JSON only):"""
        
        return prompt
    
    def _validate_forecast_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize forecast result."""
        return {
            "emerging_skills": result.get("emerging_skills", []),
            "declining_skills": result.get("declining_skills", []),
            "confidence_score": int(result.get("confidence_score", 70)),
            "key_insights": result.get("key_insights", []),
        }
    
    def _fallback_forecast_logic(
        self,
        data: Dict[str, Any],
        months: int
    ) -> Dict[str, Any]:
        """Fallback rule-based forecast when AI is unavailable."""
        current_skills = data.get("current_skills", {})
        
        # Sort skills by frequency
        sorted_skills = sorted(
            current_skills.items(),
            key=lambda x: x[1].get("count", 0) if isinstance(x[1], dict) else x[1],
            reverse=True
        )
        
        # Emerging: top 20% of skills with moderate frequency
        emerging_count = max(3, len(sorted_skills) // 5)
        emerging_skills = []
        for skill, info in sorted_skills[:emerging_count]:
            if isinstance(info, dict):
                freq = info.get("frequency", 0)
                if 0.1 <= freq <= 0.4:  # Moderate frequency
                    emerging_skills.append({
                        "skill": skill,
                        "current_frequency": freq,
                        "predicted_frequency": min(1.0, freq * 1.3),
                        "growth_rate": 0.30,
                        "reason": "Based on current adoption patterns"
                    })
        
        # Declining: bottom 20% of skills
        declining_count = max(2, len(sorted_skills) // 5)
        declining_skills = []
        for skill, info in sorted_skills[-declining_count:]:
            if isinstance(info, dict):
                freq = info.get("frequency", 0)
                if freq < 0.1:  # Low frequency
                    declining_skills.append({
                        "skill": skill,
                        "current_frequency": freq,
                        "predicted_frequency": max(0.0, freq * 0.7),
                        "decline_rate": -0.30,
                        "reason": "Low adoption, likely to decline"
                    })
        
        return {
            "emerging_skills": emerging_skills[:10],
            "declining_skills": declining_skills[:10],
            "confidence_score": 60,
            "key_insights": ["Forecast based on current frequency patterns"]
        }
    
    def _generate_trend_curve(
        self,
        baseline: Dict[str, Any],
        forecast: Dict[str, Any],
        months: int
    ) -> List[Dict[str, Any]]:
        """Generate trend curve data points."""
        curve = []
        base_date = datetime.utcnow()
        
        # Get top skills to track
        skill_freq = baseline.get("skill_frequency", {})
        top_skills = sorted(
            skill_freq.items(),
            key=lambda x: x[1].get("count", 0) if isinstance(x[1], dict) else x[1],
            reverse=True
        )[:20]
        
        # Generate monthly data points
        for month_offset in range(0, months + 1):
            date = base_date + timedelta(days=30 * month_offset)
            
            for skill, info in top_skills:
                if isinstance(info, dict):
                    current_freq = info.get("frequency", 0)
                else:
                    current_freq = info
                
                # Predict future frequency based on forecast
                predicted_freq = current_freq
                
                # Check if skill is in emerging/declining lists
                for emerging in forecast.get("emerging_skills", []):
                    if emerging.get("skill") == skill:
                        growth_rate = emerging.get("growth_rate", 0)
                        predicted_freq = current_freq * (1 + growth_rate * (month_offset / months))
                        break
                
                for declining in forecast.get("declining_skills", []):
                    if declining.get("skill") == skill:
                        decline_rate = abs(declining.get("decline_rate", 0))
                        predicted_freq = current_freq * (1 - decline_rate * (month_offset / months))
                        break
                
                curve.append({
                    "date": date.isoformat(),
                    "skill": skill,
                    "value": round(predicted_freq * 100, 2)  # Percentage
                })
        
        return curve
    
    async def _save_forecast(self, forecast: Dict[str, Any], horizon: str) -> Path:
        """Save forecast to file (async)."""
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"skill_forecast_{horizon}_{timestamp}.json"
        forecast_path = self.analysis_dir / filename
        
        async with aiofiles.open(forecast_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(forecast, ensure_ascii=False, indent=2))
        
        logger.info(f"Saved forecast to {forecast_path}")
        return forecast_path
    
    def _fallback_forecast(
        self,
        all_employees: List[Dict[str, Any]],
        forecast_horizon: str
    ) -> Dict[str, Any]:
        """Fallback forecast when main method fails."""
        months = self._parse_horizon(forecast_horizon)
        baseline = self._generate_baseline(all_employees)
        forecast = self._fallback_forecast_logic(
            {"current_skills": baseline["skill_frequency"]},
            months
        )
        trend_curve = self._generate_trend_curve(baseline, forecast, months)
        
        return {
            "forecast_horizon": forecast_horizon,
            "emerging_skills": forecast.get("emerging_skills", []),
            "declining_skills": forecast.get("declining_skills", []),
            "predicted_trend_curve": trend_curve,
            "confidence_score": 50,
            "forecasted_at": datetime.utcnow().isoformat(),
            "fallback": True
        }
