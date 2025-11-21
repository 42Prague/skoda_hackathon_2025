"""
Async Skill Analysis Repository
--------------------------------
Repository for SkillAnalysisRecord model - handles all async DB operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from swx_api.app.models.skill_models import SkillAnalysisRecord
from swx_api.app.repositories.base_repository import BaseRepository


class SkillAnalysisRepository(BaseRepository[SkillAnalysisRecord]):
    """Async repository for skill analysis records."""
    
    def __init__(self):
        """Initialize skill analysis repository."""
        super().__init__(SkillAnalysisRecord)
    
    async def get_by_employee_id(
        self, 
        session: AsyncSession, 
        employee_id: str, 
        limit: Optional[int] = None
    ) -> List[SkillAnalysisRecord]:
        """Get all analyses for an employee, ordered by creation date (newest first)."""
        statement = select(SkillAnalysisRecord).where(
            SkillAnalysisRecord.employee_id == employee_id
        ).order_by(desc(SkillAnalysisRecord.created_at))
        
        if limit:
            statement = statement.limit(limit)
        
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_latest_by_employee_id(
        self, 
        session: AsyncSession, 
        employee_id: str
    ) -> Optional[SkillAnalysisRecord]:
        """Get the latest analysis for an employee."""
        analyses = await self.get_by_employee_id(session, employee_id, limit=1)
        return analyses[0] if analyses else None
    
    async def get_all_analyses(
        self, 
        session: AsyncSession, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[SkillAnalysisRecord]:
        """Get all analyses, ordered by creation date (newest first)."""
        statement = select(SkillAnalysisRecord).order_by(
            desc(SkillAnalysisRecord.created_at)
        ).offset(offset)
        if limit:
            statement = statement.limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
