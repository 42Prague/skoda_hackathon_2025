"""
Audit Log Schemas
-----------------
Pydantic schemas for audit log entries.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""
    
    event_type: str = Field(..., description="Type: 'ingestion', 'ai_call', 'db_write', 'error', 'api_call'")
    service_name: Optional[str] = Field(default=None, description="Name of service that generated the event")
    event_data: Dict[str, Any] = Field(..., description="Event data")
    user_id: Optional[str] = Field(default=None, description="User ID if applicable")
    ip_address: Optional[str] = Field(default=None, description="IP address if applicable")
    success: bool = Field(default=True, description="Whether the event was successful")


class AuditLogPublic(BaseModel):
    """Public schema for audit log entries."""
    
    id: UUID
    event_type: str
    service_name: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

