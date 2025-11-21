"""
Async Service Tests
------------------
Test all service async operations.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.services.employee_ingestion_service import EmployeeIngestionService
from swx_api.app.services.dataset_ingestion_service import DatasetIngestionService
from swx_api.app.services.skill_analytics_service import SkillAnalyticsService
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.repositories.dataset_repository import DatasetRepository


class TestEmployeeIngestionService:
    """Test EmployeeIngestionService async operations."""
    
    @pytest.mark.asyncio
    async def test_load_employees_from_dataset(
        self,
        test_db_session: AsyncSession,
        temp_data_dir: Path
    ):
        """Test loading employees from dataset."""
        import pandas as pd
        
        # Create test CSV
        csv_path = temp_data_dir / "normalized" / "test_dataset.csv"
        df = pd.DataFrame({
            "employee_id": ["EMP001", "EMP002"],
            "department": ["Engineering", "Sales"],
            "skills": ["Python, FastAPI", "JavaScript, React"],
        })
        df.to_csv(csv_path, index=False)
        
        # Mock paths
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            
            repo = EmployeeRepository()
            service = EmployeeIngestionService(repo)
            
            result = await service.load_employees_from_dataset(
                test_db_session,
                dataset_id="test_dataset",
                employee_id_column="employee_id",
                department_column="department",
                skills_column="skills",
            )
            
            assert result["total_loaded"] == 2
            assert result["created"] == 2
            
            # Verify employees were created
            emp1 = await repo.get_by_employee_id(test_db_session, "EMP001")
            assert emp1 is not None
            assert emp1.department == "Engineering"
            assert "Python" in emp1.skills


class TestDatasetIngestionService:
    """Test DatasetIngestionService async operations."""
    
    @pytest.mark.asyncio
    async def test_ingest_file(
        self,
        test_db_session: AsyncSession,
        temp_data_dir: Path
    ):
        """Test ingesting a file."""
        import pandas as pd
        
        # Create test CSV
        csv_path = temp_data_dir / "raw" / "test.csv"
        df = pd.DataFrame({
            "employee_id": ["EMP001"],
            "department": ["Engineering"],
            "skills": ["Python"],
        })
        df.to_csv(csv_path, index=False)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            
            repo = DatasetRepository()
            service = DatasetIngestionService(repo)
            
            result = await service.ingest_file(
                test_db_session,
                str(csv_path),
                "test.csv"
            )
            
            assert "dataset_id" in result
            assert "metadata" in result
            
            # Verify dataset was saved to DB
            datasets = await repo.get_all_datasets(test_db_session)
            assert len(datasets) > 0
    
    @pytest.mark.asyncio
    async def test_list_datasets(
        self,
        test_db_session: AsyncSession,
        temp_data_dir: Path
    ):
        """Test listing datasets."""
        import pandas as pd
        
        # Create test CSV
        csv_path = temp_data_dir / "normalized" / "test.csv"
        df = pd.DataFrame({"col1": [1, 2, 3]})
        df.to_csv(csv_path, index=False)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            
            repo = DatasetRepository()
            service = DatasetIngestionService(repo)
            
            datasets = await service.list_datasets(test_db_session)
            
            assert len(datasets) > 0
            assert any(d["dataset_id"] == "test" for d in datasets)


class TestSkillAnalyticsService:
    """Test SkillAnalyticsService async operations."""
    
    @pytest.mark.asyncio
    async def test_analyze_employee(
        self,
        test_db_session: AsyncSession
    ):
        """Test analyzing an employee."""
        from swx_api.app.models.skill_models import EmployeeRecord
        
        # Create test employee
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python", "FastAPI", "PostgreSQL"],
        )
        repo = EmployeeRepository()
        await repo.create(test_db_session, employee)
        
        service = SkillAnalyticsService()
        
        result = await service.analyze_employee(
            test_db_session,
            repo,
            "EMP001"
        )
        
        assert "skill_count" in result
        assert "skills" in result
        assert result["skill_count"] == 3
    
    @pytest.mark.asyncio
    async def test_analyze_department(
        self,
        test_db_session: AsyncSession
    ):
        """Test analyzing a department."""
        repo = EmployeeRepository()
        
        # Create test employees
        emp1 = EmployeeRecord(employee_id="EMP001", department="Engineering", skills=["Python", "FastAPI"])
        emp2 = EmployeeRecord(employee_id="EMP002", department="Engineering", skills=["JavaScript", "React"])
        
        await repo.create(test_db_session, emp1)
        await repo.create(test_db_session, emp2)
        
        employees = await repo.get_by_department(test_db_session, "Engineering")
        
        service = SkillAnalyticsService()
        result = await service.analyze_department("Engineering", employees)
        
        assert "department" in result
        assert result["department"] == "Engineering"
        assert "skill_frequency" in result
        assert len(result["skill_frequency"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_global(
        self,
        test_db_session: AsyncSession
    ):
        """Test global analysis."""
        repo = EmployeeRepository()
        
        # Create test employees
        emp1 = EmployeeRecord(employee_id="EMP001", department="Eng", skills=["Python"])
        emp2 = EmployeeRecord(employee_id="EMP002", department="Eng", skills=["Python", "FastAPI"])
        emp3 = EmployeeRecord(employee_id="EMP003", department="Sales", skills=["JavaScript"])
        
        await repo.create(test_db_session, emp1)
        await repo.create(test_db_session, emp2)
        await repo.create(test_db_session, emp3)
        
        employees = await repo.get_all_employees(test_db_session)
        employee_data = [
            {
                "employee_id": emp.employee_id,
                "department": emp.department,
                "skills": emp.skills or [],
            }
            for emp in employees
        ]
        
        service = SkillAnalyticsService()
        result = await service.analyze_global(employee_data)
        
        assert "total_employees" in result
        assert result["total_employees"] == 3
        assert "skill_frequency" in result
        assert "Python" in result["skill_frequency"]

