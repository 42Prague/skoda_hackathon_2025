"""
Async Employee Repository
--------------------------
Repository for EmployeeRecord model - handles all async DB operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.app.repositories.base_repository import BaseRepository


class EmployeeRepository(BaseRepository[EmployeeRecord]):
    """Async repository for employee records."""
    
    def __init__(self):
        """Initialize employee repository."""
        super().__init__(EmployeeRecord)
    
    async def get_by_employee_id(
        self, 
        session: AsyncSession, 
        employee_id: str
    ) -> Optional[EmployeeRecord]:
        """Get employee by employee_id."""
        statement = select(EmployeeRecord).where(EmployeeRecord.employee_id == employee_id)
        # SQLAlchemy AsyncSession uses execute().scalars(), not exec()
        result = await session.execute(statement)
        scalars = result.scalars()
        return scalars.first()
    
    async def get_by_department(
        self, 
        session: AsyncSession, 
        department: str, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[EmployeeRecord]:
        """Get all employees in a department."""
        statement = select(EmployeeRecord).where(
            EmployeeRecord.department == department
        ).offset(offset)
        if limit:
            statement = statement.limit(limit)
        # SQLAlchemy AsyncSession uses execute().scalars(), not exec()
        result = await session.execute(statement)
        scalars = result.scalars()
        return list(scalars.all())
    
    async def get_all_employees(
        self, 
        session: AsyncSession, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[EmployeeRecord]:
        """Get all employees."""
        return await self.get_all(session, limit=limit, offset=offset)
    
    async def search_by_skills(
        self, 
        session: AsyncSession, 
        skills: List[str], 
        match_all: bool = False
    ) -> List[EmployeeRecord]:
        """
        Search employees by skills.
        
        Args:
            session: Async database session
            skills: List of skills to search for
            match_all: If True, employee must have all skills; if False, any skill matches
        """
        statement = select(EmployeeRecord)
        result = await session.execute(statement)
        all_employees = list(result.scalars().all())
        
        filtered = []
        for emp in all_employees:
            if not emp.skills:
                continue
            
            emp_skills_lower = [s.lower() for s in emp.skills]
            search_skills_lower = [s.lower() for s in skills]
            
            if match_all:
                if all(s in emp_skills_lower for s in search_skills_lower):
                    filtered.append(emp)
            else:
                if any(s in emp_skills_lower for s in search_skills_lower):
                    filtered.append(emp)
        
        return filtered
    
    async def get_departments(self, session: AsyncSession) -> List[str]:
        """Get list of all unique departments."""
        statement = select(EmployeeRecord.department).distinct()
        result = await session.execute(statement)
        departments = list(result.scalars().all())
        return [dept for dept in departments if dept]
