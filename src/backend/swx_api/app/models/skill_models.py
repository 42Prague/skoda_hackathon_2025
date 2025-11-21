"""
Skill Coach Database Models
----------------------------
SQLModel tables for skill coach functionality.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Text

from swx_api.core.models.base import Base


class EmployeeRecordBase(Base):
    """Base model for employee records."""
    
    employee_id: str = Field(unique=True, index=True, max_length=255)
    department: str = Field(index=True, max_length=255)
    skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    personal_number: Optional[str] = Field(default=None, index=True, max_length=255)
    persstat_start_month_abc: Optional[str] = Field(default=None, max_length=50)
    pers_organization_branch: Optional[str] = Field(default=None, max_length=255)
    pers_profession_id: Optional[str] = Field(default=None, max_length=255)
    pers_profession_name: Optional[str] = Field(default=None, max_length=255)
    pers_job_family_id: Optional[str] = Field(default=None, index=True, max_length=255)
    s1_org_hierarchy: Optional[str] = Field(default=None, max_length=500)
    s2_org_hierarchy: Optional[str] = Field(default=None, max_length=500)
    s3_org_hierarchy: Optional[str] = Field(default=None, max_length=500)
    s4_org_hierarchy: Optional[str] = Field(default=None, max_length=500)
    ob_codes: Optional[Dict[str, Optional[str]]] = Field(
        default=None, sa_column=Column(JSONB), description="Škoda OB1-OB8 metadata"
    )
    education_branch_id: Optional[str] = Field(default=None, max_length=255)
    education_branch_name: Optional[str] = Field(default=None, max_length=255)
    education_branch_group_id: Optional[str] = Field(default=None, max_length=255)
    education_branch_group_name: Optional[str] = Field(default=None, max_length=255)
    education_category_id: Optional[str] = Field(default=None, max_length=255)
    education_category_name: Optional[str] = Field(default=None, max_length=255)
    field_of_study_id: Optional[str] = Field(default=None, max_length=255)
    field_of_study_name: Optional[str] = Field(default=None, max_length=255)
    field_of_study_code: Optional[str] = Field(default=None, max_length=255)
    coordinator_group_id: Optional[str] = Field(default=None, max_length=255)
    planned_profession_id: Optional[str] = Field(default=None, max_length=255)
    planned_profession_name: Optional[str] = Field(default=None, max_length=255)
    planned_position_id: Optional[str] = Field(default=None, max_length=255)
    planned_position_name: Optional[str] = Field(default=None, max_length=255)
    hr_contact_name: Optional[str] = Field(default=None, max_length=255)


class EmployeeRecord(EmployeeRecordBase, table=True):
    """
    Database model representing an employee record.
    
    Attributes:
        id: Unique record identifier
        employee_id: Employee identifier
        department: Department name
        skills: List of skills (JSONB)
        metadata: Additional metadata (JSONB)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "employee_record"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    # JSONB field defined here to avoid SQLModel type inference issues in base class
    # Note: Database column is 'metadata', using alias to access it as 'metadata' in Python
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column("metadata", JSONB), alias="metadata")


class SkillAnalysisRecordBase(Base):
    """Base model for skill analysis records."""
    
    employee_id: str = Field(foreign_key="employee_record.employee_id", index=True)


class SkillAnalysisRecord(SkillAnalysisRecordBase, table=True):
    """
    Database model representing a skill analysis record.
    
    Attributes:
        id: Unique record identifier
        employee_id: Foreign key to employee record
        analysis_json: Analysis results (JSONB)
        recommendations_json: Recommendations (JSONB)
        created_at: Creation timestamp
    """
    
    __tablename__ = "skill_analysis_record"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    # JSONB fields defined here to avoid SQLModel type inference issues
    analysis_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    recommendations_json: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSONB))


class DatasetRecordBase(Base):
    """Base model for dataset records."""
    
    dataset_id: str = Field(unique=True, index=True, max_length=255)
    dq_score: Optional[int] = Field(default=None)


class DatasetRecord(DatasetRecordBase, table=True):
    """
    Database model representing a dataset record.
    
    Attributes:
        id: Unique record identifier
        dataset_id: Dataset identifier
        metadata: Dataset metadata (JSONB)
        summary: Dataset summary (JSONB)
        dq_score: Data quality score (0-100)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "dataset_record"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    # JSONB fields defined here to avoid SQLModel type inference issues
    # Note: Database column is 'metadata', using alias to access it as 'metadata' in Python
    meta_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSONB), alias="metadata")
    summary: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSONB))


# Note: Pydantic schemas have been moved to swx_api.app.schemas
# Import them from there instead of this file


# Learning History Models

class LearningHistoryBase(Base):
    """Base model for learning history records."""
    
    employee_id: str = Field(foreign_key="employee_record.employee_id", index=True)
    course_name: str = Field(max_length=255)
    provider: Optional[str] = Field(default=None, max_length=255)
    content_id: Optional[str] = Field(default=None, max_length=255)
    content_url: Optional[str] = Field(default=None, max_length=500)
    course_type: Optional[str] = Field(default=None, max_length=255)
    start_date: Optional[datetime] = Field(default=None)
    end_date: Optional[datetime] = Field(default=None)
    hours: Optional[float] = Field(default=None)
    verified_minutes: Optional[int] = Field(default=None)
    estimated_minutes: Optional[int] = Field(default=None)
    verified: Optional[bool] = Field(default=None)
    completion_points: Optional[float] = Field(default=None)
    user_rating: Optional[float] = Field(default=None)
    completion_status: str = Field(default="in_progress", max_length=50)  # "completed", "in_progress", "cancelled"
    skills_covered: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    certificate_url: Optional[str] = Field(default=None, max_length=500)


class LearningHistory(LearningHistoryBase, table=True):
    """
    Database model representing employee learning history.
    
    Attributes:
        id: Unique record identifier
        employee_id: Foreign key to employee record
        course_name: Name of the course
        provider: Course provider
        start_date: Course start date
        end_date: Course end date
        hours: Total hours spent
        completion_status: Status of completion
        skills_covered: List of skills covered (JSONB)
        certificate_url: URL to certificate
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "learning_history"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE


# Note: LearningHistory schemas moved to swx_api.app.schemas.learning_schemas


# Audit Log Models

class AuditLogBase(Base):
    """Base model for audit log records."""
    
    event_type: str = Field(index=True, max_length=50)  # "ingestion", "ai_call", "db_write", "error", "api_call"
    service_name: Optional[str] = Field(default=None, max_length=255)
    user_id: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=50)
    success: bool = Field(default=True)


class AuditLog(AuditLogBase, table=True):
    """
    Database model representing an audit log entry.
    
    Attributes:
        id: Unique record identifier
        event_type: Type of event
        service_name: Name of service that generated the event
        event_data: Event data (JSONB)
        user_id: User ID if applicable
        ip_address: IP address if applicable
        success: Whether the event was successful
        created_at: Creation timestamp
    """
    
    __tablename__ = "audit_log"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    # JSONB field defined here to avoid SQLModel type inference issues
    event_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))


# Note: AuditLog schemas moved to swx_api.app.schemas.audit_schemas

# ---------------------------------------------------------------------------
# Backwards-compatible imports for Pydantic schemas
# ---------------------------------------------------------------------------
try:
    from swx_api.app.schemas.employee_schemas import (
        EmployeeRecordCreate,
        EmployeeRecordUpdate,
        EmployeeRecordPublic,
    )
    from swx_api.app.schemas.skill_schemas import (
        SkillAnalysisCreate,
        SkillAnalysisPublic,
    )
    from swx_api.app.schemas.dataset_schemas import (
        DatasetRecordCreate,
        DatasetRecordPublic,
    )
    from swx_api.app.schemas.learning_schemas import (
        LearningHistoryCreate,
        LearningHistoryUpdate,
        LearningHistoryPublic,
    )
except ImportError:  # pragma: no cover - schema imports not required at runtime
    EmployeeRecordCreate = EmployeeRecordUpdate = EmployeeRecordPublic = None  # type: ignore
    SkillAnalysisCreate = SkillAnalysisPublic = None  # type: ignore
    DatasetRecordCreate = DatasetRecordPublic = None  # type: ignore
    LearningHistoryCreate = LearningHistoryUpdate = LearningHistoryPublic = None  # type: ignore

