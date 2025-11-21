"""
Dataset Validators
------------------
Validation functions for dataset-related inputs.
"""

from pathlib import Path

from fastapi import HTTPException

from swx_api.app.services.ingestion_service import SUPPORTED_EXTENSIONS


def validate_dataset_id(dataset_id: str) -> str:
    """Validate dataset ID format."""
    if not dataset_id or not dataset_id.strip():
        raise HTTPException(status_code=400, detail="Dataset ID cannot be empty")
    
    if len(dataset_id) > 255:
        raise HTTPException(status_code=400, detail="Dataset ID must be 255 characters or less")
    
    return dataset_id.strip()


def validate_file_extension(filename: str) -> str:
    """Validate file extension is supported."""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    return suffix


def validate_file_size(file_size: int, max_size_mb: int = 100) -> int:
    """Validate file size."""
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {max_size_mb}MB"
        )
    
    return file_size

