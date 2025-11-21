"""
API Endpoint Tests
------------------
Test all API endpoints with success cases, invalid inputs, missing params, corrupted data, excessive payloads, rate limits.
"""

import io
import json
from typing import Dict, Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from swx_api.app.models.skill_models import (
    EmployeeRecord,
    SkillAnalysisRecord,
    DatasetRecord,
    SkillAnalysisCreate,
)


class TestIngestionEndpoints:
    """Test ingestion API endpoints."""
    
    def test_ingest_csv_success(self, client, temp_data_dir):
        """Test successful CSV ingestion."""
        csv_content = """employee_id,department,skills,email
EMP001,Engineering,"Python,SQL,JavaScript",john.doe@example.com
EMP002,Marketing,"Excel,Power BI",jane.smith@example.com
"""
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = client.post("/api/ingestion/ingest", files=files)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_ingest_json_success(self, client, temp_data_dir):
        """Test successful JSON ingestion."""
        json_content = json.dumps([
            {"employee_id": "EMP001", "department": "Engineering", "skills": ["Python"]}
        ])
        files = {"file": ("test.json", io.BytesIO(json_content.encode()), "application/json")}
        response = client.post("/api/ingestion/ingest", files=files)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_ingest_missing_file(self, client):
        """Test ingestion with missing file."""
        response = client.post("/api/ingestion/ingest")
        assert response.status_code in [400, 422]
    
    def test_ingest_invalid_file_type(self, client):
        """Test ingestion with invalid file type."""
        files = {"file": ("test.pdf", io.BytesIO(b"test"), "application/pdf")}
        response = client.post("/api/ingestion/ingest", files=files)
        assert response.status_code in [400, 422]
    
    def test_list_datasets_success(self, client, db_session, sample_dataset_record):
        """Test listing datasets."""
        response = client.get("/api/ingestion/datasets")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_load_employees_success(self, client, db_session, temp_data_dir):
        """Test loading employees from dataset."""
        # Create dataset file
        dataset_path = temp_data_dir / "normalized" / "test_dataset.csv"
        csv_content = """employee_id,department,skills
EMP001,Engineering,"Python,SQL"
"""
        dataset_path.write_text(csv_content)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            
            response = client.post(
                "/api/ingestion/load-employees/test_dataset",
                params={"employee_id_column": "employee_id"}
            )
            assert response.status_code in [200, 201]
    
    def test_load_employees_not_found(self, client):
        """Test loading employees from non-existent dataset."""
        response = client.post("/api/ingestion/load-employees/nonexistent")
        assert response.status_code == 404


class TestSkillEndpoints:
    """Test skill-related API endpoints."""
    
    def test_build_ontology_success(self, client, db_session, temp_data_dir):
        """Test building skill ontology."""
        # Create dataset
        dataset_path = temp_data_dir / "normalized" / "test.csv"
        csv_content = """employee_id,department,skills
EMP001,Engineering,"Python,SQL,JavaScript"
"""
        dataset_path.write_text(csv_content)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            
            response = client.post("/api/skills/ontology", params={"dataset_id": "test"})
            assert response.status_code in [200, 201]
            data = response.json()
            assert data.get("success") is True or "data" in data
    
    def test_analyze_employee_success(self, client, db_session, sample_employees):
        """Test employee skill analysis."""
        employee = sample_employees[0]
        
        request_data = {
            "employee_id": employee.employee_id,
            "role_requirements": None
        }
        
        response = client.post("/api/skills/analysis", json=request_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_analyze_employee_not_found(self, client):
        """Test analysis with non-existent employee."""
        request_data = {
            "employee_id": "NONEXISTENT",
            "role_requirements": None
        }
        
        response = client.post("/api/skills/analysis", json=request_data)
        assert response.status_code == 404
    
    def test_get_employee_analysis_success(self, client, db_session, sample_employees):
        """Test getting employee analysis."""
        employee = sample_employees[0]
        
        # Create analysis record
        analysis = SkillAnalysisRecord(
            employee_id=employee.employee_id,
            analysis_json={"gap_score": 75}
        )
        db_session.add(analysis)
        db_session.commit()
        
        response = client.get(f"/api/skills/analysis/{employee.employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_employee_analysis_not_found(self, client):
        """Test getting analysis for non-existent employee."""
        response = client.get("/api/skills/analysis/NONEXISTENT")
        assert response.status_code == 404
    
    def test_calculate_role_fit_success(self, client, db_session, sample_employees):
        """Test role fit calculation."""
        employee = sample_employees[0]
        
        request_data = {
            "role_title": "Senior Software Engineer",
            "required_skills": ["Python", "SQL"],
            "preferred_skills": ["Docker"]
        }
        
        response = client.post(
            f"/api/skills/role-fit/{employee.employee_id}",
            json=request_data
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_calculate_role_fit_not_found(self, client):
        """Test role fit with non-existent employee."""
        request_data = {"required_skills": ["Python"]}
        response = client.post("/api/skills/role-fit/NONEXISTENT", json=request_data)
        assert response.status_code == 404


class TestRecommendationsEndpoints:
    """Test recommendations API endpoints."""
    
    def test_get_skill_recommendations_success(self, client, db_session, sample_employees):
        """Test getting skill recommendations."""
        employee = sample_employees[0]
        
        response = client.get(f"/api/skills/recommendations/skills/{employee.employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_skill_recommendations_not_found(self, client):
        """Test recommendations for non-existent employee."""
        response = client.get("/api/skills/recommendations/skills/NONEXISTENT")
        assert response.status_code == 404
    
    def test_get_training_path_success(self, client, db_session, sample_employees):
        """Test getting training path."""
        employee = sample_employees[0]
        
        request_data = {
            "employee_id": employee.employee_id,
            "target_skills": ["Docker", "Kubernetes"]
        }
        
        response = client.post("/api/skills/recommendations/training-path", json=request_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_next_role_recommendations(self, client, db_session, sample_employees):
        """Test getting next role recommendations."""
        employee = sample_employees[0]
        
        request_data = {
            "employee_id": employee.employee_id,
            "current_role": "Software Engineer"
        }
        
        response = client.post("/api/skills/recommendations/next-role", json=request_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True or "data" in data


class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""
    
    def test_get_employee_analytics_success(self, client, db_session, sample_employees):
        """Test getting employee analytics."""
        employee = sample_employees[0]
        
        response = client.get(f"/api/analytics/employees/{employee.employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_employee_analytics_not_found(self, client):
        """Test analytics for non-existent employee."""
        response = client.get("/api/analytics/employees/NONEXISTENT")
        assert response.status_code == 404
    
    def test_get_department_analytics_success(self, client, db_session, sample_employees):
        """Test getting department analytics."""
        department = sample_employees[0].department
        
        response = client.get(f"/api/analytics/departments/{department}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_global_analytics_success(self, client, db_session, sample_employees):
        """Test getting global analytics."""
        response = client.get("/api/analytics/global")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_skill_forecast_success(self, client, db_session, sample_employees):
        """Test getting skill forecast."""
        response = client.get("/api/analytics/forecast", params={"months": 6})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_skill_forecast_invalid_months(self, client):
        """Test forecast with invalid months parameter."""
        response = client.get("/api/analytics/forecast", params={"months": 24})
        assert response.status_code in [400, 422]
    
    def test_get_team_similarity_success(self, client, db_session, sample_employees):
        """Test getting team similarity."""
        response = client.get("/api/analytics/team-similarity")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data


class TestDashboardEndpoints:
    """Test dashboard API endpoints."""
    
    def test_get_dashboard_overview(self, client, db_session, sample_employees):
        """Test getting dashboard overview."""
        response = client.get("/api/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_skill_map(self, client, db_session, sample_employees):
        """Test getting skill map."""
        response = client.get("/api/dashboard/skill-map")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_skill_heatmap(self, client, db_session, sample_employees):
        """Test getting skill heatmap."""
        response = client.get("/api/dashboard/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_skill_trends(self, client, db_session, sample_employees):
        """Test getting skill trends."""
        response = client.get("/api/dashboard/trends", params={"period_months": 6})
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_ui_contract(self, client):
        """Test getting UI contract."""
        response = client.get("/api/dashboard/ui-contract")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data


class TestAdvancedEndpoints:
    """Test advanced feature endpoints."""
    
    def test_get_skill_taxonomy(self, client, db_session, sample_employees):
        """Test getting skill taxonomy."""
        response = client.get("/api/skills/taxonomy")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_get_mentor_recommendations(self, client, db_session, sample_employees):
        """Test getting mentor recommendations."""
        employee = sample_employees[0]
        
        response = client.get(f"/api/recommendations/mentor/{employee.employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
    
    def test_simulate_scenario(self, client, db_session, sample_employees):
        """Test scenario simulation."""
        request_data = {
            "scenario_type": "employee_loss",
            "scenario_params": {
                "employee_ids": [sample_employees[0].employee_id]
            }
        }
        
        response = client.post("/api/analytics/simulate", json=request_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True or "data" in data


class TestErrorHandling:
    """Test error handling in endpoints."""
    
    def test_invalid_json_payload(self, client):
        """Test endpoint with invalid JSON."""
        response = client.post(
            "/api/skills/analysis",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, client):
        """Test endpoint with missing required fields."""
        response = client.post("/api/skills/analysis", json={})
        assert response.status_code in [400, 422]
    
    def test_excessive_payload_size(self, client):
        """Test endpoint with excessive payload."""
        large_data = {"employee_id": "EMP001", "skills": ["Skill"] * 10000}
        response = client.post("/api/skills/analysis", json=large_data)
        # Should handle gracefully (either accept or reject with appropriate error)
        assert response.status_code in [200, 201, 400, 413, 422]
    
    def test_sql_injection_attempt(self, client):
        """Test SQL injection attempt."""
        malicious_id = "EMP001'; DROP TABLE employee_record; --"
        response = client.get(f"/api/analytics/employees/{malicious_id}")
        # Should handle safely (not crash, return 404 or error)
        assert response.status_code in [400, 404, 422, 500]
        # Verify table still exists
        response2 = client.get("/api/analytics/global")
        assert response2.status_code == 200
    
    def test_path_traversal_attempt(self, client):
        """Test path traversal attempt."""
        malicious_path = "../../etc/passwd"
        response = client.post(f"/api/ingestion/load-employees/{malicious_path}")
        assert response.status_code in [400, 404, 422]


class TestRateLimiting:
    """Test rate limiting (if implemented)."""
    
    def test_multiple_requests(self, client, db_session, sample_employees):
        """Test multiple rapid requests."""
        employee = sample_employees[0]
        
        # Make multiple requests rapidly
        for _ in range(10):
            response = client.get(f"/api/analytics/employees/{employee.employee_id}")
            assert response.status_code in [200, 429]  # 429 if rate limited
        
        # Should not crash
        assert True

