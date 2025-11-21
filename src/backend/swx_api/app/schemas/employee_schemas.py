"""
Employee Schemas
----------------
Pydantic schemas for employee-related API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EmployeeRecordCreate(BaseModel):
    """Schema for creating an employee record."""
    
    employee_id: str = Field(..., description="Employee identifier")
    department: str = Field(..., description="Department name")
    skills: Optional[List[str]] = Field(default=None, description="List of skills")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class EmployeeRecordUpdate(BaseModel):
    """Schema for updating an employee record."""
    
    department: Optional[str] = Field(default=None, description="Department name")
    skills: Optional[List[str]] = Field(default=None, description="List of skills")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class EmployeeRecordPublic(BaseModel):
    """Public schema for employee records."""
    
    id: UUID
    employee_id: str
    department: str
    skills: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

