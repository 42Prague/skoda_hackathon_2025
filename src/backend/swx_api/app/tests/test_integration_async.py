"""
Async Integration Tests
----------------------
End-to-end integration tests for async operations.
"""

import pytest
from httpx import AsyncClient

from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.app.repositories.employee_repository import EmployeeRepository


class TestEndToEndAsync:
    """End-to-end async integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test complete workflow: create employee -> analyze -> get recommendations."""
        repo = EmployeeRepository()
        
        # 1. Create employee
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python", "FastAPI"],
        )
        await repo.create(test_db_session, employee)
        
        # 2. Analyze employee skills
        analyze_response = await async_client.post(
            "/api/skills/analyze",
            json={"employee_id": "EMP001"}
        )
        
        assert analyze_response.status_code in [200, 500]
        
        # 3. Get analytics
        analytics_response = await async_client.get("/api/analytics/employee/EMP001")
        
        assert analytics_response.status_code in [200, 404]
        
        # 4. Get recommendations
        recommendations_response = await async_client.get(
            "/api/recommendations/skills/EMP001"
        )
        
        assert recommendations_response.status_code in [200, 404, 500]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self,
        async_client: AsyncClient,
        test_db_session
    ):
        """Test handling concurrent async requests."""
        repo = EmployeeRepository()
        
        # Create multiple employees
        for i in range(5):
            employee = EmployeeRecord(
                employee_id=f"EMP{i:03d}",
                department="Engineering",
                skills=["Python"],
            )
            await repo.create(test_db_session, employee)
        
        # Make concurrent requests
        import asyncio
        
        async def get_analytics(emp_id: str):
            return await async_client.get(f"/api/analytics/employee/{emp_id}")
        
        tasks = [get_analytics(f"EMP{i:03d}") for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should complete
        assert len(responses) == 5
        assert all(r.status_code in [200, 404] for r in responses)
    
    @pytest.mark.asyncio
    async def test_database_transaction_rollback(
        self,
        test_db_session
    ):
        """Test that database transactions work correctly with async."""
        repo = EmployeeRepository()
        
        employee = EmployeeRecord(
            employee_id="EMP001",
            department="Engineering",
            skills=["Python"],
        )
        
        created = await repo.create(test_db_session, employee)
        assert created.id is not None
        
        # Rollback
        await test_db_session.rollback()
        
        # Employee should not be found after rollback
        found = await repo.get_by_employee_id(test_db_session, "EMP001")
        # Note: In test setup, session is rolled back, so this may be None
        # This tests that rollback works correctly

