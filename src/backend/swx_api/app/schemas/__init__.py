"""
Schemas Module
--------------
Pydantic request/response models for API endpoints.
"""

from swx_api.app.schemas.employee_schemas import (
    EmployeeRecordCreate,
    EmployeeRecordUpdate,
    EmployeeRecordPublic,
)
from swx_api.app.schemas.skill_schemas import (
    SkillAnalysisCreate,
    SkillAnalysisPublic,
    SkillAnalysisRequest,
    SkillForecastingRequest,
    RoleFitRequest,
    ScenarioSimulationRequest,
    MentorRecommendationRequest,
)
from swx_api.app.schemas.dataset_schemas import (
    DatasetRecordCreate,
    DatasetRecordPublic,
    IngestionResponse,
    DatasetSummary,
)
from swx_api.app.schemas.learning_schemas import (
    LearningHistoryCreate,
    LearningHistoryUpdate,
    LearningHistoryPublic,
)
from swx_api.app.schemas.audit_schemas import (
    AuditLogCreate,
    AuditLogPublic,
)
from swx_api.app.schemas.ontology_schemas import (
    OntologyResponse,
)
from swx_api.app.schemas.recommendations_schemas import (
    RecommendationsResponse,
    TrainingPathRequest,
    NextRoleRequest,
)
from swx_api.app.schemas.dashboard_schemas import (
    DashboardOverviewResponse,
    SkillMapResponse,
    SkillHeatmapResponse,
    SkillTrendsResponse,
    InstantOverviewResponse,
)
from swx_api.app.schemas.common_schemas import (
    UnifiedScoreModel,
    ErrorResponse,
)

__all__ = [
    # Employee schemas
    "EmployeeRecordCreate",
    "EmployeeRecordUpdate",
    "EmployeeRecordPublic",
    # Skill schemas
    "SkillAnalysisCreate",
    "SkillAnalysisPublic",
    "SkillAnalysisRequest",
    "SkillForecastingRequest",
    "RoleFitRequest",
    "ScenarioSimulationRequest",
    "MentorRecommendationRequest",
    # Dataset schemas
    "DatasetRecordCreate",
    "DatasetRecordPublic",
    "IngestionResponse",
    "DatasetSummary",
    # Learning schemas
    "LearningHistoryCreate",
    "LearningHistoryUpdate",
    "LearningHistoryPublic",
    # Audit schemas
    "AuditLogCreate",
    "AuditLogPublic",
    # Ontology schemas
    "OntologyResponse",
    # Recommendations schemas
    "RecommendationsResponse",
    "TrainingPathRequest",
    "NextRoleRequest",
    # Dashboard schemas
    "DashboardOverviewResponse",
    "SkillMapResponse",
    "SkillHeatmapResponse",
    "SkillTrendsResponse",
    "InstantOverviewResponse",
    # Common schemas
    "UnifiedScoreModel",
    "ErrorResponse",
]

