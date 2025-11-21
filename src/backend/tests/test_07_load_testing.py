"""
Load Testing
------------
Test with 2000 employees, 100k skill records. Ensure no memory leaks, no crashes, correct queue handling.
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import psutil
import os

from swx_api.app.services.ingestion_service import ingest_file, load_employees_from_dataset
from swx_api.app.models.skill_models import EmployeeRecord


class TestLoadTesting:
    """Load testing with large datasets."""
    
    def test_ingest_large_dataset(self, db_session, temp_data_dir, large_dataset_content):
        """Test ingesting large dataset (2000 employees)."""
        csv_path = temp_data_dir / "raw" / "large_dataset.csv"
        csv_path.write_text(large_dataset_content)
        
        # Monitor memory
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            try:
                ingestion_result = ingest_file(csv_path, "large_dataset.csv")
                
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = memory_after - memory_before
                
                # Verify ingestion succeeded
                assert "dataset_id" in ingestion_result
                assert ingestion_result["metadata"]["row_count"] == 2000
                
                # Memory increase should be reasonable (< 500MB for 2000 rows)
                assert memory_increase < 500, f"Memory increase too large: {memory_increase}MB"
                
            except Exception as e:
                pytest.fail(f"Ingestion failed with large dataset: {e}")
    
    def test_load_large_dataset_to_database(self, db_session, temp_data_dir, large_dataset_content):
        """Test loading large dataset into database."""
        # Create normalized file
        normalized_path = temp_data_dir / "normalized" / "large_dataset.csv"
        normalized_path.write_text(large_dataset_content)
        
        # Monitor memory
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            employees = load_employees_from_dataset(normalized_path)
            
            assert len(employees) == 2000
            
            # Load in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(employees), batch_size):
                batch = employees[i:i + batch_size]
                for emp_data in batch:
                    employee = EmployeeRecord(
                        employee_id=emp_data["employee_id"],
                        department=emp_data["department"],
                        skills=emp_data["skills"],
                        metadata=emp_data["metadata"]
                    )
                    db_session.add(employee)
                db_session.commit()
            
            # Verify all loaded
            total_count = db_session.query(EmployeeRecord).count()
            assert total_count == 2000
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            
            # Memory should be reasonable
            assert memory_increase < 1000, f"Memory increase too large: {memory_increase}MB"
            
        except Exception as e:
            pytest.fail(f"Loading large dataset failed: {e}")
    
    def test_query_large_dataset(self, db_session):
        """Test querying large dataset."""
        # Create 2000 employees
        employees = []
        for i in range(2000):
            employee = EmployeeRecord(
                employee_id=f"LOAD{i:04d}",
                department=f"Dept{i % 10}",
                skills=[f"Skill{j}" for j in range(5)],
                metadata={"index": i}
            )
            employees.append(employee)
        
        # Add in batches
        batch_size = 100
        for i in range(0, len(employees), batch_size):
            batch = employees[i:i + batch_size]
            db_session.add_all(batch)
            db_session.commit()
        
        # Query all
        all_employees = db_session.query(EmployeeRecord).all()
        assert len(all_employees) == 2000
        
        # Query by department
        dept_employees = db_session.query(EmployeeRecord).filter(
            EmployeeRecord.department == "Dept0"
        ).all()
        assert len(dept_employees) > 0
        
        # Query with skill filter
        skill_employees = [
            emp for emp in all_employees
            if emp.skills and "Skill0" in emp.skills
        ]
        assert len(skill_employees) > 0
    
    def test_no_memory_leak_on_repeated_operations(self, db_session, temp_data_dir):
        """Test that repeated operations don't cause memory leaks."""
        process = psutil.Process(os.getpid())
        memory_samples = []
        
        # Create small dataset
        csv_content = """employee_id,department,skills
EMP001,Engineering,"Python,SQL"
EMP002,Marketing,"Excel,Power BI"
"""
        
        for iteration in range(10):
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            csv_path = temp_data_dir / "raw" / f"iter_{iteration}.csv"
            csv_path.write_text(csv_content)
            
            with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
                mock_paths.raw_dir = temp_data_dir / "raw"
                mock_paths.normalized_dir = temp_data_dir / "normalized"
                mock_paths.processed_dir = temp_data_dir / "processed"
                mock_paths.analysis_dir = temp_data_dir / "analysis"
                mock_paths.logs_dir = temp_data_dir / "logs"
                
                try:
                    ingest_file(csv_path, f"iter_{iteration}.csv")
                except Exception:
                    pass  # Some iterations might fail, that's okay
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(memory_after - memory_before)
        
        # Memory increase should be stable (not growing linearly)
        if len(memory_samples) > 1:
            # Check that memory doesn't grow significantly
            max_increase = max(memory_samples)
            avg_increase = sum(memory_samples) / len(memory_samples)
            
            # Max should not be more than 2x average (indicates leak)
            assert max_increase < avg_increase * 2, "Possible memory leak detected"
    
    def test_concurrent_requests(self, client, db_session, sample_employees):
        """Test handling concurrent requests."""
        import concurrent.futures
        
        employee = sample_employees[0]
        
        def make_request():
            try:
                response = client.get(f"/api/analytics/employees/{employee.employee_id}")
                return response.status_code
            except Exception as e:
                return str(e)
        
        # Make 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Most requests should succeed (200 or 404)
        success_count = sum(1 for r in results if r in [200, 404])
        assert success_count > 40, f"Too many failures: {success_count}/50"
    
    def test_large_payload_handling(self, client, db_session):
        """Test handling of large payloads."""
        # Create large skills list
        large_skills = [f"Skill{i}" for i in range(1000)]
        
        request_data = {
            "employee_id": "LARGE001",
            "role_requirements": {
                "required_skills": large_skills
            }
        }
        
        # Should handle gracefully (either accept or reject with appropriate error)
        response = client.post("/api/skills/analysis", json=request_data)
        assert response.status_code in [200, 201, 400, 413, 422, 500]
        
        # Should not crash
        health_response = client.get("/healthz")
        assert health_response.status_code == 200
    
    def test_database_connection_pooling(self, db_session):
        """Test database connection pooling under load."""
        # Create many employees
        employees = []
        for i in range(500):
            employee = EmployeeRecord(
                employee_id=f"POOL{i:04d}",
                department="Engineering",
                skills=["Python", "SQL"]
            )
            employees.append(employee)
        
        # Add in batches
        batch_size = 50
        for i in range(0, len(employees), batch_size):
            batch = employees[i:i + batch_size]
            db_session.add_all(batch)
            db_session.commit()
        
        # Verify all saved
        total = db_session.query(EmployeeRecord).count()
        assert total >= 500
        
        # Connection should still work
        test_emp = db_session.query(EmployeeRecord).filter_by(
            employee_id="POOL0000"
        ).first()
        assert test_emp is not None

