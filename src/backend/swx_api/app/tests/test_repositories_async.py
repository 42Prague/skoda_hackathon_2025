"""
Async Repository Tests
---------------------
Test all repository async operations.
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.repositories.skill_repository import SkillAnalysisRepository
from swx_api.app.repositories.dataset_repository import DatasetRepository
from swx_api.app.repositories.learning_history_repository import LearningHistoryRepository
from swx_api.app.repositories.audit_repository import AuditRepository
from swx_api.app.models.skill_models import (
    EmployeeRecord,
    SkillAnalysisRecord,
    DatasetRecord,
    LearningHistory,
    AuditLog
)


class TestEmployeeRepository:
    """Test EmployeeRepository async operations."""
    
    @pytest.mark.asyncio
    async def test_create_employee(self, test_db_session: AsyncSession):
        """Test creating an employee."""
        repo = EmployeeRepository()
        
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python", "FastAPI"],
        )
        
        created = await repo.create(test_db_session, employee)
        
        assert created.id is not None
        assert created.employee_id == "EMP001"
        assert created.department == "Engineering"
        assert created.skills == ["Python", "FastAPI"]
    
    @pytest.mark.asyncio
    async def test_get_by_employee_id(self, test_db_session: AsyncSession):
        """Test getting employee by employee_id."""
        repo = EmployeeRepository()
        
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python"],
        )
        await repo.create(test_db_session, employee)
        
        found = await repo.get_by_employee_id(test_db_session, "EMP001")
        
        assert found is not None
        assert found.employee_id == "EMP001"
    
    @pytest.mark.asyncio
    async def test_get_by_department(self, test_db_session: AsyncSession):
        """Test getting employees by department."""
        repo = EmployeeRepository()
        
        emp1 = EmployeeRecord(employee_id="EMP001", department="Engineering", skills=[])
        emp2 = EmployeeRecord(employee_id="EMP002", department="Engineering", skills=[])
        emp3 = EmployeeRecord(employee_id="EMP003", department="Sales", skills=[])
        
        await repo.create(test_db_session, emp1)
        await repo.create(test_db_session, emp2)
        await repo.create(test_db_session, emp3)
        
        engineering_emps = await repo.get_by_department(test_db_session, "Engineering")
        
        assert len(engineering_emps) == 2
        assert all(emp.department == "Engineering" for emp in engineering_emps)
    
    @pytest.mark.asyncio
    async def test_search_by_skills(self, test_db_session: AsyncSession):
        """Test searching employees by skills."""
        repo = EmployeeRepository()
        
        emp1 = EmployeeRecord(employee_id="EMP001", department="Eng", skills=["Python", "FastAPI"])
        emp2 = EmployeeRecord(employee_id="EMP002", department="Eng", skills=["JavaScript", "React"])
        emp3 = EmployeeRecord(employee_id="EMP003", department="Eng", skills=["Python", "Django"])
        
        await repo.create(test_db_session, emp1)
        await repo.create(test_db_session, emp2)
        await repo.create(test_db_session, emp3)
        
        # Search for Python (should match emp1 and emp3)
        results = await repo.search_by_skills(test_db_session, ["Python"])
        
        assert len(results) == 2
        assert all("Python" in emp.skills for emp in results)
    
    @pytest.mark.asyncio
    async def test_update_employee(self, test_db_session: AsyncSession):
        """Test updating an employee."""
        repo = EmployeeRepository()
        
        employee = EmployeeRecord(employee_id="EMP001", department="Engineering", skills=["Python"])
        created = await repo.create(test_db_session, employee)
        
        created.skills.append("FastAPI")
        updated = await repo.update(test_db_session, created)
        
        assert "FastAPI" in updated.skills
        assert len(updated.skills) == 2
    
    @pytest.mark.asyncio
    async def test_delete_employee(self, test_db_session: AsyncSession):
        """Test deleting an employee."""
        repo = EmployeeRepository()
        
        employee = EmployeeRecord(employee_id="EMP001", department="Engineering", skills=[])
        created = await repo.create(test_db_session, employee)
        
        await repo.delete(test_db_session, created)
        
        found = await repo.get_by_employee_id(test_db_session, "EMP001")
        assert found is None


class TestSkillAnalysisRepository:
    """Test SkillAnalysisRepository async operations."""
    
    @pytest.mark.asyncio
    async def test_create_skill_analysis(self, test_db_session: AsyncSession):
        """Test creating a skill analysis."""
        repo = SkillAnalysisRepository()
        
        analysis = SkillAnalysisRecord(
            employee_id="EMP001",
            analysis_json={"skills": ["Python"], "score": 85},
        )
        
        created = await repo.create(test_db_session, analysis)
        
        assert created.id is not None
        assert created.employee_id == "EMP001"
        assert created.analysis_json["score"] == 85
    
    @pytest.mark.asyncio
    async def test_get_by_employee_id(self, test_db_session: AsyncSession):
        """Test getting analyses by employee_id."""
        repo = SkillAnalysisRepository()
        
        analysis1 = SkillAnalysisRecord(employee_id="EMP001", analysis_json={})
        analysis2 = SkillAnalysisRecord(employee_id="EMP001", analysis_json={})
        analysis3 = SkillAnalysisRecord(employee_id="EMP002", analysis_json={})
        
        await repo.create(test_db_session, analysis1)
        await repo.create(test_db_session, analysis2)
        await repo.create(test_db_session, analysis3)
        
        emp1_analyses = await repo.get_by_employee_id(test_db_session, "EMP001")
        
        assert len(emp1_analyses) == 2
        assert all(a.employee_id == "EMP001" for a in emp1_analyses)
    
    @pytest.mark.asyncio
    async def test_get_latest_by_employee_id(self, test_db_session: AsyncSession):
        """Test getting latest analysis for employee."""
        repo = SkillAnalysisRepository()
        
        analysis1 = SkillAnalysisRecord(employee_id="EMP001", analysis_json={"version": 1})
        analysis2 = SkillAnalysisRecord(employee_id="EMP001", analysis_json={"version": 2})
        
        await repo.create(test_db_session, analysis1)
        await asyncio.sleep(0.01)  # Small delay to ensure different timestamps
        await repo.create(test_db_session, analysis2)
        
        latest = await repo.get_latest_by_employee_id(test_db_session, "EMP001")
        
        assert latest is not None
        assert latest.analysis_json["version"] == 2


class TestDatasetRepository:
    """Test DatasetRepository async operations."""
    
    @pytest.mark.asyncio
    async def test_create_dataset(self, test_db_session: AsyncSession):
        """Test creating a dataset record."""
        repo = DatasetRepository()
        
        dataset = DatasetRecord(
            dataset_id="DS001",
            metadata={"row_count": 100},
            summary={"total_skills": 50},
        )
        
        created = await repo.create(test_db_session, dataset)
        
        assert created.id is not None
        assert created.dataset_id == "DS001"
        assert created.metadata["row_count"] == 100
    
    @pytest.mark.asyncio
    async def test_get_by_dataset_id(self, test_db_session: AsyncSession):
        """Test getting dataset by dataset_id."""
        repo = DatasetRepository()
        
        dataset = DatasetRecord(dataset_id="DS001", metadata={}, summary={})
        await repo.create(test_db_session, dataset)
        
        found = await repo.get_by_dataset_id(test_db_session, "DS001")
        
        assert found is not None
        assert found.dataset_id == "DS001"


class TestLearningHistoryRepository:
    """Test LearningHistoryRepository async operations."""
    
    @pytest.mark.asyncio
    async def test_create_learning_history(self, test_db_session: AsyncSession):
        """Test creating learning history."""
        repo = LearningHistoryRepository()
        
        history = LearningHistory(
            employee_id="EMP001",
            skill_name="Python",
            learning_type="course",
            completion_status="in_progress",
        )
        
        created = await repo.create(test_db_session, history)
        
        assert created.id is not None
        assert created.employee_id == "EMP001"
        assert created.skill_name == "Python"
    
    @pytest.mark.asyncio
    async def test_get_by_employee_id(self, test_db_session: AsyncSession):
        """Test getting learning history by employee_id."""
        repo = LearningHistoryRepository()
        
        history1 = LearningHistory(employee_id="EMP001", skill_name="Python", learning_type="course", completion_status="completed")
        history2 = LearningHistory(employee_id="EMP001", skill_name="FastAPI", learning_type="course", completion_status="in_progress")
        
        await repo.create(test_db_session, history1)
        await repo.create(test_db_session, history2)
        
        emp1_history = await repo.get_by_employee_id(test_db_session, "EMP001")
        
        assert len(emp1_history) == 2
        assert all(h.employee_id == "EMP001" for h in emp1_history)


class TestAuditRepository:
    """Test AuditRepository async operations."""
    
    @pytest.mark.asyncio
    async def test_create_audit_log(self, test_db_session: AsyncSession):
        """Test creating audit log."""
        repo = AuditRepository()
        
        log = AuditLog(
            event_type="api_call",
            service_name="test_service",
            success=True,
        )
        
        created = await repo.create(test_db_session, log)
        
        assert created.id is not None
        assert created.event_type == "api_call"
        assert created.success is True
    
    @pytest.mark.asyncio
    async def test_get_by_event_type(self, test_db_session: AsyncSession):
        """Test getting logs by event type."""
        repo = AuditRepository()
        
        log1 = AuditLog(event_type="api_call", service_name="test", success=True)
        log2 = AuditLog(event_type="api_call", service_name="test", success=True)
        log3 = AuditLog(event_type="error", service_name="test", success=False)
        
        await repo.create(test_db_session, log1)
        await repo.create(test_db_session, log2)
        await repo.create(test_db_session, log3)
        
        api_logs = await repo.get_by_event_type(test_db_session, "api_call")
        
        assert len(api_logs) == 2
        assert all(log.event_type == "api_call" for log in api_logs)
    
    @pytest.mark.asyncio
    async def test_get_failed_events(self, test_db_session: AsyncSession):
        """Test getting failed events."""
        repo = AuditRepository()
        
        log1 = AuditLog(event_type="error", service_name="test", success=False)
        log2 = AuditLog(event_type="api_call", service_name="test", success=True)
        log3 = AuditLog(event_type="error", service_name="test", success=False)
        
        await repo.create(test_db_session, log1)
        await repo.create(test_db_session, log2)
        await repo.create(test_db_session, log3)
        
        failed = await repo.get_failed_events(test_db_session)
        
        assert len(failed) == 2
        assert all(not log.success for log in failed)

