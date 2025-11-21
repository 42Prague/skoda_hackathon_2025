"""
Async Database Helpers
----------------------
Helper functions to bridge SQLModel and SQLAlchemy async session differences.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, SQLModel
from typing import TypeVar, Type, List, Optional, Any

ModelType = TypeVar("ModelType", bound=SQLModel)


async def exec_select(
    session: AsyncSession,
    statement: Any,
) -> Any:
    """
    Execute a select statement with AsyncSession.
    
    SQLAlchemy's AsyncSession uses execute().scalars() instead of exec().
    This helper bridges the gap between SQLModel's sync API and SQLAlchemy's async API.
    
    Args:
        session: SQLAlchemy AsyncSession
        statement: SQLModel select statement
        
    Returns:
        Result object with .all(), .first(), .one(), etc.
    """
    result = await session.execute(statement)
    return result.scalars()


class AsyncSessionHelper:
    """Helper class to add exec() method to AsyncSession for compatibility."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def exec(self, statement: Any) -> Any:
        """Execute a select statement (compatibility with SQLModel's exec())."""
        result = await self.session.execute(statement)
        return result.scalars()
    
    def __getattr__(self, name: str):
        """Delegate all other attributes to the underlying session."""
        return getattr(self.session, name)
    
    def __aenter__(self):
        return self
    
    def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.session.__aexit__(exc_type, exc_val, exc_tb)

