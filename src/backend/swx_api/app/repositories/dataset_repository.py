"""
Async Dataset Repository
------------------------
Repository for DatasetRecord model - handles all async DB operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from swx_api.app.models.skill_models import DatasetRecord
from swx_api.app.repositories.base_repository import BaseRepository


class DatasetRepository(BaseRepository[DatasetRecord]):
    """Async repository for dataset records."""
    
    def __init__(self):
        """Initialize dataset repository."""
        super().__init__(DatasetRecord)
    
    async def get_by_dataset_id(
        self, 
        session: AsyncSession, 
        dataset_id: str
    ) -> Optional[DatasetRecord]:
        """Get dataset by dataset_id."""
        statement = select(DatasetRecord).where(DatasetRecord.dataset_id == dataset_id)
        result = await session.execute(statement)
        return result.scalars().first()
    
    async def get_all_datasets(
        self, 
        session: AsyncSession, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[DatasetRecord]:
        """Get all datasets, ordered by creation date (newest first)."""
        statement = select(DatasetRecord).order_by(
            desc(DatasetRecord.created_at)
        ).offset(offset)
        if limit:
            statement = statement.limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_latest_dataset(
        self, 
        session: AsyncSession
    ) -> Optional[DatasetRecord]:
        """Get the latest dataset."""
        datasets = await self.get_all_datasets(session, limit=1)
        return datasets[0] if datasets else None
