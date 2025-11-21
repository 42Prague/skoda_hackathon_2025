"""
Async Learning History Repository
----------------------------------
Repository for LearningHistory model - handles all async DB operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from swx_api.app.models.skill_models import LearningHistory
from swx_api.app.repositories.base_repository import BaseRepository


class LearningHistoryRepository(BaseRepository[LearningHistory]):
    """Async repository for learning history records."""
    
    def __init__(self):
        """Initialize learning history repository."""
        super().__init__(LearningHistory)
    
    async def get_by_employee_id(
        self, 
        session: AsyncSession, 
        employee_id: str, 
        limit: Optional[int] = None
    ) -> List[LearningHistory]:
        """Get all learning history records for an employee, ordered by creation date (newest first)."""
        statement = select(LearningHistory).where(
            LearningHistory.employee_id == employee_id
        ).order_by(desc(LearningHistory.created_at))
        
        if limit:
            statement = statement.limit(limit)
        
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_by_completion_status(
        self, 
        session: AsyncSession, 
        status: str, 
        limit: Optional[int] = None
    ) -> List[LearningHistory]:
        """Get learning history records by completion status."""
        statement = select(LearningHistory).where(
            LearningHistory.completion_status == status
        ).order_by(desc(LearningHistory.created_at))
        
        if limit:
            statement = statement.limit(limit)
        
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_all_history(
        self, 
        session: AsyncSession, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[LearningHistory]:
        """Get all learning history records, ordered by creation date (newest first)."""
        statement = select(LearningHistory).order_by(
            desc(LearningHistory.created_at)
        ).offset(offset)
        if limit:
            statement = statement.limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
