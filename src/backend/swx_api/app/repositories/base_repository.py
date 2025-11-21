"""
Async Base Repository
---------------------
Base repository class with common async CRUD operations.
"""

from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """Base repository with common async CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository.
        
        Args:
            model: SQLModel class
        """
        self.model = model
    
    async def create(self, session: AsyncSession, obj: ModelType) -> ModelType:
        """Create a new record."""
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj
    
    async def get_by_id(self, session: AsyncSession, id: UUID) -> Optional[ModelType]:
        """Get record by ID."""
        return await session.get(self.model, id)
    
    async def get_all(
        self, 
        session: AsyncSession, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[ModelType]:
        """Get all records with optional pagination."""
        statement = select(self.model).offset(offset)
        if limit:
            statement = statement.limit(limit)
        # SQLAlchemy AsyncSession uses execute().scalars(), not exec()
        result = await session.execute(statement)
        scalars = result.scalars()
        return list(scalars.all())
    
    async def update(self, session: AsyncSession, obj: ModelType) -> ModelType:
        """Update an existing record."""
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj
    
    async def delete(self, session: AsyncSession, obj: ModelType) -> None:
        """Delete a record."""
        await session.delete(obj)
        await session.commit()
    
    async def delete_by_id(self, session: AsyncSession, id: UUID) -> bool:
        """Delete record by ID. Returns True if deleted, False if not found."""
        obj = await self.get_by_id(session, id)
        if obj:
            await self.delete(session, obj)
            return True
        return False
    
    async def count(self, session: AsyncSession) -> int:
        """Count total records."""
        statement = select(self.model)
        # SQLAlchemy AsyncSession uses execute().scalars(), not exec()
        result = await session.execute(statement)
        scalars = result.scalars()
        return len(list(scalars.all()))
