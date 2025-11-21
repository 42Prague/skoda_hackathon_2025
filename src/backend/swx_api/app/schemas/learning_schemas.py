"""
Learning History Schemas
------------------------
Pydantic schemas for learning history records.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LearningHistoryCreate(BaseModel):
    """Schema for creating a learning history record."""
    
    employee_id: str = Field(..., description="Employee identifier")
    course_name: str = Field(..., description="Name of the course")
    provider: Optional[str] = Field(default=None, description="Course provider")
    course_type: Optional[str] = Field(default=None, description="Course type/category")
    content_id: Optional[str] = Field(default=None, description="External content identifier")
    content_url: Optional[str] = Field(default=None, description="URL to the content")
    start_date: Optional[datetime] = Field(default=None, description="Course start date")
    end_date: Optional[datetime] = Field(default=None, description="Course end date")
    hours: Optional[float] = Field(default=None, ge=0, description="Total hours spent")
    verified_minutes: Optional[int] = Field(default=None, ge=0, description="Verified learning minutes")
    estimated_minutes: Optional[int] = Field(default=None, ge=0, description="Estimated learning minutes")
    verified: Optional[bool] = Field(default=None, description="Completion verified flag")
    completion_points: Optional[float] = Field(default=None, description="Gamified completion points")
    user_rating: Optional[float] = Field(default=None, description="User rating 0-5")
    completion_status: str = Field(default="in_progress", description="Status: 'completed', 'in_progress', 'cancelled'")
    skills_covered: Optional[List[str]] = Field(default=None, description="List of skills covered")
    certificate_url: Optional[str] = Field(default=None, description="URL to certificate")


class LearningHistoryUpdate(BaseModel):
    """Schema for updating a learning history record."""
    
    course_name: Optional[str] = Field(default=None, description="Name of the course")
    provider: Optional[str] = Field(default=None, description="Course provider")
    course_type: Optional[str] = Field(default=None, description="Course type/category")
    content_id: Optional[str] = Field(default=None, description="External content identifier")
    content_url: Optional[str] = Field(default=None, description="URL to the content")
    start_date: Optional[datetime] = Field(default=None, description="Course start date")
    end_date: Optional[datetime] = Field(default=None, description="Course end date")
    hours: Optional[float] = Field(default=None, ge=0, description="Total hours spent")
    verified_minutes: Optional[int] = Field(default=None, ge=0, description="Verified learning minutes")
    estimated_minutes: Optional[int] = Field(default=None, ge=0, description="Estimated learning minutes")
    verified: Optional[bool] = Field(default=None, description="Completion verified flag")
    completion_points: Optional[float] = Field(default=None, description="Gamified completion points")
    user_rating: Optional[float] = Field(default=None, description="User rating 0-5")
    completion_status: Optional[str] = Field(default=None, description="Status: 'completed', 'in_progress', 'cancelled'")
    skills_covered: Optional[List[str]] = Field(default=None, description="List of skills covered")
    certificate_url: Optional[str] = Field(default=None, description="URL to certificate")


class LearningHistoryPublic(BaseModel):
    """Public schema for learning history records."""
    
    id: UUID
    employee_id: str
    course_name: str
    provider: Optional[str] = None
    course_type: Optional[str] = None
    content_id: Optional[str] = None
    content_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    hours: Optional[float] = None
    verified_minutes: Optional[int] = None
    estimated_minutes: Optional[int] = None
    verified: Optional[bool] = None
    completion_points: Optional[float] = None
    user_rating: Optional[float] = None
    completion_status: str
    skills_covered: Optional[List[str]] = None
    certificate_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

