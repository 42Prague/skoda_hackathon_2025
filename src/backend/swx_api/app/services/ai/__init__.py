"""
AI Services Package
-------------------
All AI-powered business services.
"""

from swx_api.app.services.ai.ai_skill_service import AISkillService
from swx_api.app.services.ai.ai_qualification_service import AIQualificationService
from swx_api.app.services.ai.ai_employee_service import AIEmployeeService
from swx_api.app.services.ai.ai_team_service import AITeamService
from swx_api.app.services.ai.ai_role_fit_service import AIRoleFitService
from swx_api.app.services.ai.ai_succession_service import AISuccessionService
from swx_api.app.services.ai.ai_forecast_service import AIForecastService
from swx_api.app.services.ai.ai_training_service import AITrainingService
from swx_api.app.services.ai.ai_risk_service import AIRiskService
from swx_api.app.services.ai.ai_compare_service import AICompareService
from swx_api.app.services.ai.ai_what_if_service import AIWhatIfService

__all__ = [
    "AISkillService",
    "AIQualificationService",
    "AIEmployeeService",
    "AITeamService",
    "AIRoleFitService",
    "AISuccessionService",
    "AIForecastService",
    "AITrainingService",
    "AIRiskService",
    "AICompareService",
    "AIWhatIfService",
]

