"""
Škoda Auto Database Models
---------------------------
SQLModel tables for Škoda-specific employee data structures.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Field, SQLModel, Column, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Text, Index

from swx_api.core.models.base import Base
from swx_api.app.models.skill_models import EmployeeRecord


class QualificationRecordBase(Base):
    """Base model for qualification records."""
    
    employee_id: str = Field(foreign_key="employee_record.employee_id", index=True)
    qualification_id: str = Field(index=True, max_length=255)
    qualification_name_cz: str = Field(max_length=500)
    qualification_name_en: str = Field(max_length=500)
    mandatory: bool = Field(default=False)
    obtained_date: Optional[datetime] = Field(default=None)
    expiry_date: Optional[datetime] = Field(default=None)
    status: str = Field(default="active", max_length=50)  # "active", "expired", "pending"
    fm_number: Optional[str] = Field(default=None, max_length=255)


class QualificationRecord(QualificationRecordBase, table=True):
    """Database model representing employee qualifications."""
    
    __tablename__ = "qualification_record"
    __table_args__ = (
        Index("ix_qualification_record_employee_id", "employee_id"),
        Index("ix_qualification_record_qualification_id", "qualification_id"),
        {"extend_existing": True}
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE


class JobFamilyRecordBase(Base):
    """Base model for job family records."""
    
    job_family_id: str = Field(unique=True, index=True, max_length=255)
    job_family_name_cz: str = Field(max_length=500)
    job_family_name_en: str = Field(max_length=500)
    required_qualifications: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    required_skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    preferred_skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))


class JobFamilyRecord(JobFamilyRecordBase, table=True):
    """Database model representing job families."""
    
    __tablename__ = "job_family_record"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE


class OrgHierarchyRecordBase(Base):
    """Base model for organizational hierarchy records."""
    
    employee_id: str = Field(foreign_key="employee_record.employee_id", index=True)
    level: int = Field(ge=1, le=4, index=True)
    hierarchy_path: str = Field(index=True, max_length=1000)
    hierarchy_name_cz: str = Field(max_length=500)
    hierarchy_name_en: str = Field(max_length=500)
    node_id: Optional[str] = Field(default=None, max_length=255)
    parent_node_id: Optional[str] = Field(default=None, max_length=255)
    short_code: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)


class OrgHierarchyRecord(OrgHierarchyRecordBase, table=True):
    """Database model representing organizational hierarchy."""
    
    __tablename__ = "org_hierarchy_record"
    __table_args__ = (
        Index("ix_org_hierarchy_record_employee_id", "employee_id"),
        Index("ix_org_hierarchy_record_level", "level"),
        Index("ix_org_hierarchy_record_path", "hierarchy_path"),
        {"extend_existing": True}
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE


class CourseCatalogRecordBase(Base):
    """Base model for course catalog records."""
    
    course_id: str = Field(unique=True, index=True, max_length=255)
    course_name_cz: str = Field(max_length=500)
    course_name_en: str = Field(max_length=500)
    provider: str = Field(max_length=255)
    duration_hours: Optional[float] = Field(default=None)
    skills_covered: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    qualifications_granted: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    skoda_academy: bool = Field(default=False)


class CourseCatalogRecord(CourseCatalogRecordBase, table=True):
    """Database model representing course catalog."""
    
    __tablename__ = "course_catalog_record"
    __table_args__ = {"extend_existing": True}
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE


class SkillMappingRecordBase(Base):
    """Base model for skill mapping records."""
    
    raw_skill_name: str = Field(index=True, max_length=500)
    normalized_skill_name: str = Field(index=True, max_length=500)
    language: str = Field(max_length=10)  # "cz", "en", "mixed"
    synonyms: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    canonical_skill_id: str = Field(index=True, max_length=255)


class SkillMappingRecord(SkillMappingRecordBase, table=True):
    """Database model representing skill mappings."""
    
    __tablename__ = "skill_mapping_record"
    __table_args__ = (
        Index("ix_skill_mapping_record_raw", "raw_skill_name"),
        Index("ix_skill_mapping_record_normalized", "normalized_skill_name"),
        Index("ix_skill_mapping_record_canonical", "canonical_skill_id"),
        {"extend_existing": True}
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE


class HistoricalEmployeeSnapshotBase(Base):
    """Base model for historical employee snapshots."""
    
    employee_id: str = Field(foreign_key="employee_record.employee_id", index=True)
    snapshot_date: datetime = Field(index=True)
    department: str = Field(max_length=255)
    job_family_id: Optional[str] = Field(default=None, max_length=255)
    org_hierarchy: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSONB))
    skills: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    qualifications: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))
    pers_profession_id: Optional[str] = Field(default=None, max_length=255)
    pers_organization_branch: Optional[str] = Field(default=None, max_length=255)


class HistoricalEmployeeSnapshot(HistoricalEmployeeSnapshotBase, table=True):
    """Database model representing historical employee snapshots."""
    
    __tablename__ = "historical_employee_snapshot"
    __table_args__ = (
        Index("ix_historical_snapshot_employee_id", "employee_id"),
        Index("ix_historical_snapshot_date", "snapshot_date"),
        Index("ix_historical_snapshot_employee_date", "employee_id", "snapshot_date"),
        {"extend_existing": True}
    )
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE

