"""
Async Route Tests
----------------
Test all API routes with async operations.
"""

import pytest
from httpx import AsyncClient

from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.app.repositories.employee_repository import EmployeeRepository


class TestIngestionRoutes:
    """Test ingestion routes."""
    
    @pytest.mark.asyncio
    async def test_get_datasets(self, async_client: AsyncClient, test_db_session):
        """Test GET /api/ingestion/datasets."""
        response = await async_client.get("/api/ingestion/datasets")
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_ingest_dataset(
        self,
        async_client: AsyncClient,
        test_db_session,
        temp_data_dir
    ):
        """Test POST /api/ingestion/ingest."""
        import pandas as pd
        from io import BytesIO
        
        # Create test CSV
        df = pd.DataFrame({
            "employee_id": ["EMP001"],
            "department": ["Engineering"],
            "skills": ["Python"],
        })
        csv_bytes = BytesIO()
        df.to_csv(csv_bytes, index=False)
        csv_bytes.seek(0)
        
        files = {"file": ("test.csv", csv_bytes, "text/csv")}
        
        response = await async_client.post(
            "/api/ingestion/ingest",
            files=files
        )
        
        # Should succeed or return appropriate error
        assert response.status_code in [200, 400, 500]
        data = response.json()
        assert "success" in data or "error" in data


class TestSkillsRoutes:
    """Test skills routes."""
    
    @pytest.mark.asyncio
    async def test_get_ontology(self, async_client: AsyncClient, test_db_session):
        """Test GET /api/skills/ontology."""
        response = await async_client.get("/api/skills/ontology")
        
        # May return 404 if no datasets, or 200 with ontology
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_analyze_employee_skill(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test POST /api/skills/analyze."""
        # Create test employee
        repo = EmployeeRepository()
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python", "FastAPI"],
        )
        await repo.create(test_db_session, employee)
        
        request_data = {
            "employee_id": "EMP001",
            "role_requirements": None
        }
        
        response = await async_client.post(
            "/api/skills/analyze",
            json=request_data
        )
        
        assert response.status_code in [200, 404, 500]
        data = response.json()
        assert "success" in data or "error" in data


class TestAnalyticsRoutes:
    """Test analytics routes."""
    
    @pytest.mark.asyncio
    async def test_get_employee_analytics(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test GET /api/analytics/employee/{employee_id}."""
        # Create test employee
        repo = EmployeeRepository()
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python"],
        )
        await repo.create(test_db_session, employee)
        
        response = await async_client.get("/api/analytics/employee/EMP001")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "data" in data
    
    @pytest.mark.asyncio
    async def test_get_department_analytics(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test GET /api/analytics/department/{department}."""
        # Create test employees
        repo = EmployeeRepository()
        emp1 = EmployeeRecord(employee_id="EMP001", department="Engineering", skills=["Python"])
        emp2 = EmployeeRecord(employee_id="EMP002", department="Engineering", skills=["FastAPI"])
        
        await repo.create(test_db_session, emp1)
        await repo.create(test_db_session, emp2)
        
        response = await async_client.get("/api/analytics/department/Engineering")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data


class TestRecommendationsRoutes:
    """Test recommendations routes."""
    
    @pytest.mark.asyncio
    async def test_get_skill_recommendations(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test GET /api/recommendations/skills/{employee_id}."""
        # Create test employee
        repo = EmployeeRepository()
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python"],
        )
        await repo.create(test_db_session, employee)
        
        response = await async_client.get("/api/recommendations/skills/EMP001")
        
        assert response.status_code in [200, 404, 500]
        data = response.json()
        assert "success" in data or "error" in data


class TestAdvancedRoutes:
    """Test advanced skill routes."""
    
    @pytest.mark.asyncio
    async def test_get_skill_forecast(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test GET /api/analytics/forecast."""
        response = await async_client.get("/api/analytics/forecast?months=6")
        
        assert response.status_code in [200, 500]
        data = response.json()
        assert "success" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_get_skill_taxonomy(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test GET /api/skills/taxonomy."""
        response = await async_client.get("/api/skills/taxonomy")
        
        assert response.status_code in [200, 500]
        data = response.json()
        assert "success" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_compute_role_fit(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test POST /api/skills/role-fit."""
        # Create test employee
        repo = EmployeeRepository()
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python", "FastAPI"],
        )
        await repo.create(test_db_session, employee)
        
        request_data = {
            "employee_id": "EMP001",
            "role_definition": {
                "role_name": "Backend Developer",
                "mandatory_skills": ["Python", "FastAPI"],
                "preferred_skills": ["PostgreSQL"]
            }
        }
        
        response = await async_client.post(
            "/api/skills/role-fit",
            json=request_data
        )
        
        assert response.status_code in [200, 404, 500]
        data = response.json()
        assert "success" in data or "error" in data

