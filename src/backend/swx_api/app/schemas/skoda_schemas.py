"""
Škoda Auto Schemas
------------------
Pydantic schemas for Škoda-specific API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QualificationRecordCreate(BaseModel):
    """Schema for creating a qualification record."""
    
    employee_id: str = Field(..., description="Employee identifier")
    qualification_id: str = Field(..., description="Qualification identifier")
    qualification_name_cz: str = Field(..., description="Qualification name in Czech")
    qualification_name_en: str = Field(..., description="Qualification name in English")
    mandatory: bool = Field(default=False, description="Whether qualification is mandatory")
    obtained_date: Optional[datetime] = Field(default=None, description="Date qualification was obtained")
    expiry_date: Optional[datetime] = Field(default=None, description="Date qualification expires")
    status: str = Field(default="active", description="Status: active, expired, pending")
    fm_number: Optional[str] = Field(default=None, description="FM catalogue number")


class QualificationRecordPublic(BaseModel):
    """Public schema for qualification records."""
    
    id: UUID
    employee_id: str
    qualification_id: str
    qualification_name_cz: str
    qualification_name_en: str
    mandatory: bool
    obtained_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: str
    fm_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class JobFamilyRecordCreate(BaseModel):
    """Schema for creating a job family record."""
    
    job_family_id: str = Field(..., description="Job family identifier")
    job_family_name_cz: str = Field(..., description="Job family name in Czech")
    job_family_name_en: str = Field(..., description="Job family name in English")
    required_qualifications: Optional[List[str]] = Field(default=None, description="Required qualification IDs")
    required_skills: Optional[List[str]] = Field(default=None, description="Required skills")
    preferred_skills: Optional[List[str]] = Field(default=None, description="Preferred skills")


class JobFamilyRecordPublic(BaseModel):
    """Public schema for job family records."""
    
    id: UUID
    job_family_id: str
    job_family_name_cz: str
    job_family_name_en: str
    required_qualifications: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrgHierarchyRecordCreate(BaseModel):
    """Schema for creating an org hierarchy record."""
    
    employee_id: str = Field(..., description="Employee identifier")
    level: int = Field(..., ge=1, le=4, description="Hierarchy level (1-4)")
    hierarchy_path: str = Field(..., description="Full hierarchy path")
    hierarchy_name_cz: str = Field(..., description="Hierarchy name in Czech")
    hierarchy_name_en: str = Field(..., description="Hierarchy name in English")
    node_id: Optional[str] = Field(default=None, description="Hierarchy node identifier")
    parent_node_id: Optional[str] = Field(default=None, description="Parent hierarchy node")
    short_code: Optional[str] = Field(default=None, description="Short hierarchy code")
    description: Optional[str] = Field(default=None, description="Hierarchy description")


class OrgHierarchyRecordPublic(BaseModel):
    """Public schema for org hierarchy records."""
    
    id: UUID
    employee_id: str
    level: int
    hierarchy_path: str
    hierarchy_name_cz: str
    hierarchy_name_en: str
    node_id: Optional[str] = None
    parent_node_id: Optional[str] = None
    short_code: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CourseCatalogRecordCreate(BaseModel):
    """Schema for creating a course catalog record."""
    
    course_id: str = Field(..., description="Course identifier")
    course_name_cz: str = Field(..., description="Course name in Czech")
    course_name_en: str = Field(..., description="Course name in English")
    provider: str = Field(..., description="Course provider")
    duration_hours: Optional[float] = Field(default=None, description="Course duration in hours")
    skills_covered: Optional[List[str]] = Field(default=None, description="Skills covered by course")
    qualifications_granted: Optional[List[str]] = Field(default=None, description="Qualifications granted")
    skoda_academy: bool = Field(default=False, description="Whether course is from Škoda Academy")


class CourseCatalogRecordPublic(BaseModel):
    """Public schema for course catalog records."""
    
    id: UUID
    course_id: str
    course_name_cz: str
    course_name_en: str
    provider: str
    duration_hours: Optional[float] = None
    skills_covered: Optional[List[str]] = None
    qualifications_granted: Optional[List[str]] = None
    skoda_academy: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SkillMappingRecordCreate(BaseModel):
    """Schema for creating a skill mapping record."""
    
    raw_skill_name: str = Field(..., description="Raw skill name from dataset")
    normalized_skill_name: str = Field(..., description="Normalized skill name")
    language: str = Field(..., description="Language: cz, en, mixed")
    synonyms: Optional[List[str]] = Field(default=None, description="List of synonyms")
    canonical_skill_id: str = Field(..., description="Canonical skill identifier")


class SkillMappingRecordPublic(BaseModel):
    """Public schema for skill mapping records."""
    
    id: UUID
    raw_skill_name: str
    normalized_skill_name: str
    language: str
    synonyms: Optional[List[str]] = None
    canonical_skill_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HistoricalEmployeeSnapshotCreate(BaseModel):
    """Schema for creating a historical employee snapshot."""
    
    employee_id: str = Field(..., description="Employee identifier")
    snapshot_date: datetime = Field(..., description="Snapshot date")
    department: str = Field(..., description="Department at snapshot time")
    job_family_id: Optional[str] = Field(default=None, description="Job family ID at snapshot time")
    org_hierarchy: Optional[Dict[str, str]] = Field(default=None, description="Org hierarchy at snapshot time")
    skills: Optional[List[str]] = Field(default=None, description="Skills at snapshot time")
    qualifications: Optional[List[str]] = Field(default=None, description="Qualifications at snapshot time")
    pers_profession_id: Optional[str] = Field(default=None, description="Profession ID at snapshot time")
    pers_organization_branch: Optional[str] = Field(default=None, description="Organization branch at snapshot time")


class HistoricalEmployeeSnapshotPublic(BaseModel):
    """Public schema for historical employee snapshots."""
    
    id: UUID
    employee_id: str
    snapshot_date: datetime
    department: str
    job_family_id: Optional[str] = None
    org_hierarchy: Optional[Dict[str, str]] = None
    skills: Optional[List[str]] = None
    qualifications: Optional[List[str]] = None
    pers_profession_id: Optional[str] = None
    pers_organization_branch: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SkodaEmployeeRecordPublic(BaseModel):
    """Extended employee record with Škoda-specific fields."""
    
    id: UUID
    employee_id: str
    personal_number: Optional[str] = None
    department: str
    persstat_start_month_abc: Optional[str] = None
    pers_organization_branch: Optional[str] = None
    pers_profession_id: Optional[str] = None
    pers_profession_name: Optional[str] = None
    pers_job_family_id: Optional[str] = None
    s1_org_hierarchy: Optional[str] = None
    s2_org_hierarchy: Optional[str] = None
    s3_org_hierarchy: Optional[str] = None
    s4_org_hierarchy: Optional[str] = None
    ob_codes: Optional[Dict[str, Any]] = None
    education_branch_id: Optional[str] = None
    education_branch_name: Optional[str] = None
    education_branch_group_id: Optional[str] = None
    education_branch_group_name: Optional[str] = None
    education_category_id: Optional[str] = None
    education_category_name: Optional[str] = None
    field_of_study_id: Optional[str] = None
    field_of_study_name: Optional[str] = None
    field_of_study_code: Optional[str] = None
    coordinator_group_id: Optional[str] = None
    planned_profession_id: Optional[str] = None
    planned_profession_name: Optional[str] = None
    planned_position_id: Optional[str] = None
    planned_position_name: Optional[str] = None
    hr_contact_name: Optional[str] = None
    skills: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

