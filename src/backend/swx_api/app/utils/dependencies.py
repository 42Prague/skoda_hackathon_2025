"""
Dependencies Module
------------------
FastAPI dependency injection helpers for async repositories and services.
"""

from typing import Annotated

from fastapi import Depends

from swx_api.app.repositories.audit_repository import AuditRepository
from swx_api.app.repositories.dataset_repository import DatasetRepository
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.repositories.learning_history_repository import LearningHistoryRepository
from swx_api.app.repositories.skill_repository import SkillAnalysisRepository
from swx_api.core.database.db import AsyncSessionDep


def get_employee_repository() -> EmployeeRepository:
    """Get employee repository instance."""
    return EmployeeRepository()


def get_skill_repository() -> SkillAnalysisRepository:
    """Get skill analysis repository instance."""
    return SkillAnalysisRepository()


def get_dataset_repository() -> DatasetRepository:
    """Get dataset repository instance."""
    return DatasetRepository()


def get_learning_history_repository() -> LearningHistoryRepository:
    """Get learning history repository instance."""
    return LearningHistoryRepository()


def get_audit_repository() -> AuditRepository:
    """Get audit repository instance."""
    return AuditRepository()


# Type aliases for dependency injection
EmployeeRepoDep = Annotated[EmployeeRepository, Depends(get_employee_repository)]
SkillRepoDep = Annotated[SkillAnalysisRepository, Depends(get_skill_repository)]
DatasetRepoDep = Annotated[DatasetRepository, Depends(get_dataset_repository)]
LearningHistoryRepoDep = Annotated[LearningHistoryRepository, Depends(get_learning_history_repository)]
AuditRepoDep = Annotated[AuditRepository, Depends(get_audit_repository)]
AuditLogRepoDep = Annotated[AuditRepository, Depends(get_audit_repository)]  # Alias for consistency
