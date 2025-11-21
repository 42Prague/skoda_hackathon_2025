"""
Skill Coach Ingestion Routes (Controllers)
-------------------------------------------
API endpoints for data ingestion - interface layer only.
All business logic and DB access handled by services and repositories.
"""

import io
import logging
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Query
from fastapi.responses import StreamingResponse

from swx_api.app.schemas.common_schemas import ErrorResponse
from swx_api.app.services.dataset_ingestion_service import DatasetIngestionService
from swx_api.app.services.employee_ingestion_service import EmployeeIngestionService
from swx_api.app.services.ingestion_service import SUPPORTED_EXTENSIONS, paths, timestamped_filename
from swx_api.app.utils.cache import global_cache
from swx_api.app.utils.dependencies import DatasetRepoDep, EmployeeRepoDep
from swx_api.app.utils.unified_response import unified_success, unified_error
from swx_api.app.validators.dataset_validators import validate_file_extension
from swx_api.core.database.db import AsyncSessionDep
from swx_api.utils.demo_dataset import generate_demo_dataset

logger = logging.getLogger("skill_ingestion_route")

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    500: {"model": ErrorResponse, "description": "Server error"},
}

router = APIRouter(prefix="/ingestion")


def save_upload(upload_file: UploadFile) -> Path:
    """Save uploaded file to raw directory."""
    filename = Path(upload_file.filename or "uploaded")
    sanitized = filename.name.replace(" ", "_")
    stored_name = timestamped_filename(sanitized)
    stored_path = paths.raw_dir / stored_name

    with stored_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return stored_path


@router.post("/ingest", responses=ERROR_RESPONSES)
async def ingest_dataset(
    session: AsyncSessionDep,
    dataset_repo: DatasetRepoDep,
    file: UploadFile = File(...),
):
    """
    Ingest a dataset file.
    
    Supports: CSV, Excel, JSON, TXT, DOCX
    """
    try:
        # Validate file extension
        suffix = Path(file.filename or "").suffix.lower()
        validate_file_extension(file.filename or "")
        
        # Save uploaded file
        stored_path = save_upload(file)
        
        try:
            # Use async service for business logic and DB operations
            ingestion_service = DatasetIngestionService(dataset_repo)
            result = await ingestion_service.ingest_file(
                session,
                str(stored_path), 
                file.filename or stored_path.name
            )
            
            response = unified_success(
                data=result,
                message="Dataset ingested successfully"
            )
            global_cache.invalidate()
            return response
        except Exception as exc:
            stored_path.unlink(missing_ok=True)
            raise
        finally:
            file.file.close()
    except ValueError as exc:
        return unified_error(
            error_type="ValidationError",
            message=str(exc),
            status_code=400
        )
    except Exception as exc:
        logger.error(f"Ingestion error: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Ingestion failed: {str(exc)}",
            status_code=500
        )


@router.get("/datasets", responses=ERROR_RESPONSES)
async def get_datasets(
    session: AsyncSessionDep,
    dataset_repo: DatasetRepoDep
):
    """List all ingested datasets."""
    try:
        # Use async service for business logic and DB operations
        ingestion_service = DatasetIngestionService(dataset_repo)
        datasets = await ingestion_service.list_datasets(session)
        
        return unified_success(
            data=datasets,
            message="Datasets retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error listing datasets: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to list datasets: {str(exc)}",
            status_code=500
        )


@router.post("/load-employees/{dataset_id}", responses=ERROR_RESPONSES)
async def load_employees_from_ingested_dataset(
    dataset_id: str,
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    employee_id_column: str = "employee_id",
    department_column: str = "department",
    skills_column: Optional[str] = None,
    update_existing: bool = True,
):
    """
    Load employee records from an ingested dataset into the database.
    
    Args:
        dataset_id: Dataset ID (filename without extension)
        session: Async database session
        employee_id_column: Column name for employee ID
        department_column: Column name for department
        skills_column: Optional column name for skills
        update_existing: If True, update existing employee records; if False, skip them
    """
    try:
        # Use async service for business logic and DB operations
        employee_service = EmployeeIngestionService(employee_repo)
        result = await employee_service.load_employees_from_dataset(
            session,
            dataset_id=dataset_id,
            employee_id_column=employee_id_column,
            department_column=department_column,
            skills_column=skills_column,
            update_existing=update_existing
        )
        
        response = unified_success(
            data=result,
            message=f"Loaded {result['total_loaded']} employees from dataset"
        )
        global_cache.invalidate()
        return response
    except ValueError as exc:
        error_type = "NotFound" if "not found" in str(exc).lower() else "ValidationError"
        return unified_error(
            error_type=error_type,
            message=str(exc),
            status_code=404 if error_type == "NotFound" else 400
        )
    except Exception as exc:
        logger.error(f"Error loading employees: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to load employees: {str(exc)}",
            status_code=500
        )


@router.post("/load-historical-data", responses=ERROR_RESPONSES)
async def load_historical_data(
    session: AsyncSessionDep,
    employee_repo: EmployeeRepoDep,
    base_path: str,
    years: list = Query(..., description="List of years to load (e.g., 2013,2014,2015)")
):
    """Load 12 years of historical employee data."""
    try:
        from pathlib import Path
        from swx_api.app.services.historical_data_loader import HistoricalDataLoader
        
        loader = HistoricalDataLoader()
        result = await loader.load_historical_data(Path(base_path), years)
        saved_count = await loader.save_historical_snapshots(session, result)
        
        return unified_success(
            data={
                "total_snapshots": len(result),
                "saved": saved_count,
                "failed": len(result) - saved_count
            },
            message=f"Loaded {saved_count} historical snapshots"
        )
    except Exception as exc:
        logger.error(f"Error loading historical data: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to load historical data: {str(exc)}",
            status_code=500
        )


@router.get("/demo-dataset", responses=ERROR_RESPONSES)
async def download_demo_dataset(employee_count: int = Query(60, ge=10, le=200)):
    """Generate a synthetic automotive dataset for demos."""
    demo_df = generate_demo_dataset(employee_count)
    buffer = io.StringIO()
    demo_df.to_csv(buffer, index=False)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue().encode("utf-8")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=skoda_demo_dataset.csv"},
    )

