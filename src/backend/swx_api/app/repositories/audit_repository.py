"""
Async Audit Repository
----------------------
Repository for AuditLog model - handles all async DB operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from swx_api.app.models.skill_models import AuditLog
from swx_api.app.repositories.base_repository import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Async repository for audit log records."""
    
    def __init__(self):
        """Initialize audit repository."""
        super().__init__(AuditLog)
    
    async def get_by_event_type(
        self, 
        session: AsyncSession, 
        event_type: str, 
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """Get audit logs by event type."""
        statement = select(AuditLog).where(
            AuditLog.event_type == event_type
        ).order_by(desc(AuditLog.created_at))
        if limit:
            statement = statement.limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_by_service_name(
        self, 
        session: AsyncSession, 
        service_name: str, 
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """Get audit logs by service name."""
        statement = select(AuditLog).where(
            AuditLog.service_name == service_name
        ).order_by(desc(AuditLog.created_at))
        if limit:
            statement = statement.limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_failed_events(
        self, 
        session: AsyncSession, 
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """Get all failed events."""
        statement = select(AuditLog).where(
            AuditLog.success == False
        ).order_by(desc(AuditLog.created_at))
        if limit:
            statement = statement.limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def get_all_logs(
        self, 
        session: AsyncSession, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[AuditLog]:
        """Get all audit logs, ordered by creation date (newest first)."""
        statement = select(AuditLog).order_by(
            desc(AuditLog.created_at)
        ).offset(offset)
        if limit:
            statement = statement.limit(limit)
        result = await session.execute(statement)
        return list(result.scalars().all())
