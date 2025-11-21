"""
Predictive Analytics Service
-----------------------------
ARIMA forecasting, linear regression fallback, skill demand projections.
"""

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.models.skoda_models import HistoricalEmployeeSnapshot
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.core.middleware.logging_middleware import logger

try:
    from statsmodels.tsa.arima.model import ARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available. ARIMA forecasting will use fallback.")

try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Linear regression will use fallback.")


class PredictiveAnalyticsService:
    """Predictive analytics service for skill demand forecasting."""
    
    def __init__(self, employee_repo: Optional[EmployeeRepository] = None):
        self.employee_repo = employee_repo
    
    async def forecast_skill_demand(
        self,
        skill: str,
        historical_snapshots: List[Dict[str, Any]],
        forecast_months: int = 6
    ) -> Dict[str, Any]:
        """Forecast skill demand using time-series analysis."""
        time_series = self._extract_skill_frequency_over_time(skill, historical_snapshots)
        
        if len(time_series) < 3:
            return {
                "skill": skill,
                "current_demand": time_series[-1] if time_series else 0,
                "forecasted_demand": time_series[-1] if time_series else 0,
                "confidence": 30,
                "method": "insufficient_data"
            }
        
        if len(time_series) >= 12 and STATSMODELS_AVAILABLE:
            try:
                forecast = self._arima_forecast(time_series, forecast_months)
                method = "arima"
                confidence = min(90, 50 + len(time_series) * 2)
            except Exception as e:
                logger.warning(f"ARIMA forecast failed for {skill}: {e}")
                forecast = self._linear_regression_forecast(time_series, forecast_months)
                method = "linear_regression_fallback"
                confidence = 60
        else:
            forecast = self._linear_regression_forecast(time_series, forecast_months)
            method = "linear_regression"
            confidence = 50 + len(time_series) * 3
        
        return {
            "skill": skill,
            "current_demand": time_series[-1] if time_series else 0,
            "forecasted_demand": forecast[-1] if forecast else time_series[-1] if time_series else 0,
            "forecast_series": forecast,
            "confidence": min(100, confidence),
            "method": method
        }
    
    def _extract_skill_frequency_over_time(
        self,
        skill: str,
        historical_snapshots: List[Dict[str, Any]]
    ) -> List[float]:
        """Extract skill frequency over time."""
        skill_lower = skill.lower()
        
        monthly_counts: Dict[str, int] = defaultdict(int)
        monthly_totals: Dict[str, int] = defaultdict(int)
        
        for snapshot in historical_snapshots:
            snapshot_date = snapshot.get("snapshot_date")
            if isinstance(snapshot_date, str):
                snapshot_date = datetime.fromisoformat(snapshot_date.replace("Z", "+00:00"))
            elif not isinstance(snapshot_date, datetime):
                continue
            
            month_key = snapshot_date.strftime("%Y-%m")
            monthly_totals[month_key] += 1
            
            skills = snapshot.get("skills", [])
            if skills and any(skill_lower in str(s).lower() for s in skills):
                monthly_counts[month_key] += 1
        
        sorted_months = sorted(monthly_totals.keys())
        frequencies = []
        
        for month in sorted_months:
            count = monthly_counts.get(month, 0)
            total = monthly_totals.get(month, 1)
            frequency = count / total if total > 0 else 0.0
            frequencies.append(frequency)
        
        return frequencies
    
    def _arima_forecast(self, time_series: List[float], forecast_months: int) -> List[float]:
        """ARIMA forecasting."""
        if not STATSMODELS_AVAILABLE:
            return self._linear_regression_forecast(time_series, forecast_months)
        
        try:
            series_array = np.array(time_series)
            model = ARIMA(series_array, order=(1, 1, 1))
            fitted = model.fit()
            forecast = fitted.forecast(steps=forecast_months)
            return forecast.tolist()
        except Exception as e:
            logger.warning(f"ARIMA forecast error: {e}")
            return self._linear_regression_forecast(time_series, forecast_months)
    
    def _linear_regression_forecast(self, time_series: List[float], forecast_months: int) -> List[float]:
        """Linear regression forecasting."""
        if len(time_series) < 2:
            last_value = time_series[-1] if time_series else 0.0
            return [last_value] * forecast_months
        
        if SKLEARN_AVAILABLE:
            try:
                X = np.array(range(len(time_series))).reshape(-1, 1)
                y = np.array(time_series)
                model = LinearRegression().fit(X, y)
                future_X = np.array(range(len(time_series), len(time_series) + forecast_months)).reshape(-1, 1)
                forecast = model.predict(future_X)
                return [max(0.0, float(f)) for f in forecast.tolist()]
            except Exception as e:
                logger.warning(f"Linear regression forecast error: {e}")
        
        slope = self._calculate_slope(time_series)
        last_value = time_series[-1]
        forecast = []
        
        for i in range(1, forecast_months + 1):
            predicted = last_value + (slope * i)
            forecast.append(max(0.0, predicted))
        
        return forecast
    
    def _calculate_slope(self, time_series: List[float]) -> float:
        """Calculate slope of time series."""
        if len(time_series) < 2:
            return 0.0
        
        n = len(time_series)
        x_sum = sum(range(n))
        y_sum = sum(time_series)
        xy_sum = sum(i * time_series[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        denominator = n * x2_sum - x_sum * x_sum
        if denominator == 0:
            return 0.0
        
        slope = (n * xy_sum - x_sum * y_sum) / denominator
        return slope
    
    def skill_frequency_slope(self, time_series: List[float]) -> float:
        """Calculate skill frequency slope (trend)."""
        return self._calculate_slope(time_series)
    
    async def estimate_supply_shortage(
        self,
        session: AsyncSession,
        department: str,
        skill: str,
        forecast_months: int = 6,
        historical_snapshots: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Estimate supply vs shortage for a skill in a department."""
        if not self.employee_repo:
            raise ValueError("Employee repository required for supply estimation")
        
        employees = await self.employee_repo.get_by_department(session, department)
        
        current_supply = 0
        education_distribution: Counter = Counter()
        readiness_distribution: Counter = Counter()
        for emp in employees:
            skills = emp.skills or []
            if skill.lower() in [s.lower() for s in skills]:
                current_supply += 1
            metadata = emp.meta_data or {}
            education_name = metadata.get("education", {}).get("education_category_name") if metadata.get("education") else None
            if education_name:
                education_distribution[education_name] += 1
            planned_position = getattr(emp, "planned_position_name", None) or metadata.get("planned_position_name")
            if planned_position:
                readiness_distribution[planned_position] += 1
        
        if historical_snapshots:
            demand_forecast = await self.forecast_skill_demand(skill, historical_snapshots, forecast_months)
            forecasted_demand_count = int(demand_forecast.get("forecasted_demand", 0) * len(employees))
        else:
            forecasted_demand_count = current_supply
        
        shortage = max(0, forecasted_demand_count - current_supply)
        shortage_percentage = (shortage / forecasted_demand_count * 100) if forecasted_demand_count > 0 else 0.0
        
        return {
            "department": department,
            "skill": skill,
            "current_supply": current_supply,
            "forecasted_demand": forecasted_demand_count,
            "shortage": shortage,
            "shortage_percentage": round(shortage_percentage, 2),
            "forecast_months": forecast_months,
            "education_distribution": dict(education_distribution),
            "planned_role_distribution": dict(readiness_distribution),
        }
    
    async def estimate_department_shortages(
        self,
        session: AsyncSession,
        department: str,
        forecast_months: int = 6,
        historical_snapshots: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Estimate shortages for all skills in a department."""
        if not self.employee_repo:
            raise ValueError("Employee repository required")
        
        employees = await self.employee_repo.get_by_department(session, department)
        
        skill_counter = Counter()
        for emp in employees:
            skills = emp.skills or []
            if skills:
                skill_counter.update(skills)
        
        top_skills = [skill for skill, _ in skill_counter.most_common(20)]
        
        shortages = []
        for skill in top_skills:
            shortage = await self.estimate_supply_shortage(
                session,
                department,
                skill,
                forecast_months,
                historical_snapshots
            )
            shortages.append(shortage)
        
        shortages.sort(key=lambda x: x["shortage_percentage"], reverse=True)
        return shortages

