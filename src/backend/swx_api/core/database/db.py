"""
Async Database Connection Module
--------------------------------
This module establishes async database connections, manages async sessions,
and provides dependency injection for FastAPI routes.

Key Components:
- `async_engine`: Async SQLAlchemy engine for database connection.
- `AsyncSessionLocal`: Async session factory for handling transactions.
- `get_async_session()`: FastAPI dependency for async database sessions.
"""

from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from swx_api.core.config.settings import settings
from swx_api.core.middleware.logging_middleware import logger

# Create the async database engine with connection pooling
async_engine = create_async_engine(
    str(settings.SQLALCHEMY_ASYNC_DATABASE_URI),
    echo=False,  # Disables verbose SQL logging for performance
    pool_size=20,  # Maintain up to 20 active connections
    max_overflow=10,  # Allow up to 10 extra connections when needed
    pool_pre_ping=True,  # Verify connections before using
    future=True,  # Use 2.0 style
)

# Async session factory for creating new database sessions
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency injection for database session management in FastAPI.

    Yields:
        AsyncSession: A new async database session that is automatically closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# FastAPI Dependency Injection for async session usage in routes
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]

# Legacy sync support (for migrations and admin tools)
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

sync_engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=False,
    pool_size=20,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)


def get_db() -> Session:
    """
    Legacy sync dependency (for migrations only).
    
    Note: New code should use get_async_session() instead.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Backward-compatible alias used in tests and legacy code
get_session = get_db


# Log all executed SQL queries for debugging purposes
@event.listens_for(Engine, "before_cursor_execute")
def log_sql_execute(conn, cursor, statement, parameters, context, executemany):
    """
    SQLAlchemy event listener to log SQL queries before execution.

    Args:
        conn: Database connection.
        cursor: Database cursor.
        statement (str): The SQL statement being executed.
        parameters (tuple): Query parameters.
        context: Execution context.
        executemany: Boolean indicating batch execution.
    """
    logger.debug(f"SQL QUERY: {statement} | Params: {parameters}")
