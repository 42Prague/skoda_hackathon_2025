"""
Dataset Schemas
---------------
Pydantic schemas for dataset ingestion and management.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatasetRecordCreate(BaseModel):
    """Schema for creating a dataset record."""
    
    dataset_id: str = Field(..., description="Dataset identifier")
    metadata: Dict[str, Any] = Field(..., description="Dataset metadata")
    summary: Optional[Dict[str, Any]] = Field(default=None, description="Dataset summary")
    dq_score: Optional[int] = Field(default=None, ge=0, le=100, description="Data quality score (0-100)")


class DatasetRecordPublic(BaseModel):
    """Public schema for dataset records."""
    
    id: UUID
    dataset_id: str
    metadata: Dict[str, Any]
    summary: Optional[Dict[str, Any]] = None
    dq_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IngestionResponse(BaseModel):
    """Response schema for dataset ingestion."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dataset_id": "dataset_2025_q1",
                "filename": "skoda_powertrain.csv",
                "stored_path": "/data/raw/skoda_powertrain.csv",
                "normalized_path": "/data/normalized/skoda_powertrain.csv",
                "metadata": {"row_count": 145, "skill_fields": ["skills"]},
                "dq_report_path": "/data/processed/skoda_powertrain_dq_report.json",
                "summary_path": "/data/processed/skoda_powertrain_summary.json",
            }
        }
    )

    dataset_id: str
    filename: str
    stored_path: str
    normalized_path: str
    metadata: Dict[str, Any]
    dq_report_path: Optional[str] = None
    summary_path: str


class DatasetSummary(BaseModel):
    """Schema for dataset summary."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dataset_id": "dataset_2025_q1",
                "dataset_name": "skoda_powertrain",
                "row_count": 145,
                "column_count": 12,
                "skill_fields": ["skills", "certifications"],
                "data_quality_score": 92,
                "generated_at": "2025-11-17T09:00:00Z",
            }
        }
    )

    dataset_id: str
    dataset_name: str
    row_count: int
    column_count: int
    skill_fields: list[str]
    data_quality_score: int
    generated_at: str

