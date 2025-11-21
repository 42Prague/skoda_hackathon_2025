"""
Async Dataset Ingestion Service
-------------------------------
Service layer for dataset ingestion with async repository integration.
"""

from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.models.skill_models import DatasetRecord
from swx_api.app.repositories.dataset_repository import DatasetRepository
from swx_api.app.services.ingestion_service import ingest_file_async, list_datasets_async


class DatasetIngestionService:
    """Async service for dataset ingestion operations."""
    
    def __init__(self, dataset_repo: DatasetRepository):
        """
        Initialize service with dataset repository.
        
        Args:
            dataset_repo: Dataset repository instance
        """
        self.dataset_repo = dataset_repo
    
    async def ingest_file(
        self, 
        session: AsyncSession,
        file_path: str, 
        original_filename: str
    ) -> Dict:
        """
        Ingest a file and save to database.
        
        Args:
            session: Async database session
            file_path: Path to uploaded file
            original_filename: Original filename
            
        Returns:
            Ingestion result dictionary
        """
        from pathlib import Path
        
        # Use ingestion service for business logic (async)
        result = await ingest_file_async(Path(file_path), original_filename)
        
        # Save to database using async repository
        try:
            dataset_record = DatasetRecord(
                dataset_id=result["dataset_id"],
                metadata=result.get("metadata", {}),
                summary=result.get("summary", {}),
                dq_score=result.get("metadata", {}).get("data_quality_score"),
            )
            await self.dataset_repo.create(session, dataset_record)
        except Exception:
            # Log but don't fail ingestion if DB save fails
            pass
        
        return result
    
    async def list_datasets(self, session: AsyncSession) -> List[Dict]:
        """
        List all ingested datasets, merging file-based and DB datasets.
        
        Args:
            session: Async database session
            
        Returns:
            List of dataset dictionaries
        """
        # Get file-based datasets (async)
        file_datasets = await list_datasets_async()
        
        # Get DB datasets using async repository
        db_datasets = await self.dataset_repo.get_all_datasets(session)
        
        # Merge file-based and DB datasets
        dataset_map = {d["dataset_id"]: d for d in file_datasets}
        for db_ds in db_datasets:
            if db_ds.dataset_id not in dataset_map:
                dataset_map[db_ds.dataset_id] = {
                    "dataset_id": db_ds.dataset_id,
                    "metadata": db_ds.metadata or {},
                    "summary": db_ds.summary or {},
                    "dq_score": db_ds.dq_score,
                }
        
        return list(dataset_map.values())
