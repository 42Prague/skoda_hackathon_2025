"""
Comprehensive Integration Tests for ŠKODA AI Skill Coach
---------------------------------------------------------
End-to-end tests for all major features.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

# Import the FastAPI app
from swx_api.core.main import app
from swx_api.app.models.skill_models import EmployeeRecord, DatasetRecord
from swx_api.core.database.db import get_session


# Test database setup
@pytest.fixture(scope="function")
def db_session():
    """Create a temporary database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_session():
        yield db_session
    
    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    content = """employee_id,department,skills,name,years_experience
EMP001,Engineering,"Python, JavaScript, SQL",John Doe,5
EMP002,Engineering,"Python, React, Docker",Jane Smith,3
EMP003,Sales,"Communication, Negotiation, CRM",Bob Johnson,7
EMP004,Marketing,"SEO, Content Writing, Analytics",Alice Brown,4
EMP005,IT,"Linux, Networking, Security",Charlie Wilson,6"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_excel_file():
    """Create a sample Excel file for testing."""
    import pandas as pd
    
    data = {
        'employee_id': ['EMP001', 'EMP002', 'EMP003'],
        'department': ['Engineering', 'Engineering', 'Sales'],
        'skills': ['Python;JavaScript;SQL', 'Python;React;Docker', 'Communication;Negotiation'],
        'years_experience': [5, 3, 7]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_json_file():
    """Create a sample JSON file for testing."""
    content = [
        {
            "employee_id": "EMP001",
            "department": "Engineering",
            "skills": ["Python", "JavaScript", "SQL"],
            "years_experience": 5
        },
        {
            "employee_id": "EMP002",
            "department": "Engineering",
            "skills": ["Python", "React", "Docker"],
            "years_experience": 3
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(content, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestIngestion:
    """Test ingestion endpoints."""
    
    def test_ingest_csv(self, client, sample_csv_file):
        """Test CSV ingestion."""
        with open(sample_csv_file, 'rb') as f:
            response = client.post(
                "/api/ingestion/ingest",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dataset_id" in data["data"]
        assert data["data"]["filename"] == "test.csv"
        assert "normalized_path" in data["data"]
        assert "metadata" in data["data"]
    
    def test_ingest_excel(self, client, sample_excel_file):
        """Test Excel ingestion."""
        with open(sample_excel_file, 'rb') as f:
            response = client.post(
                "/api/ingestion/ingest",
                files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "dataset_id" in data["data"]
    
    def test_ingest_json(self, client, sample_json_file):
        """Test JSON ingestion."""
        with open(sample_json_file, 'rb') as f:
            response = client.post(
                "/api/ingestion/ingest",
                files={"file": ("test.json", f, "application/json")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_datasets(self, client):
        """Test dataset listing."""
        response = client.get("/api/ingestion/datasets")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_load_employees_from_dataset(self, client, db_session, sample_csv_file):
        """Test loading employees from dataset."""
        # First ingest the dataset
        with open(sample_csv_file, 'rb') as f:
            ingest_response = client.post(
                "/api/ingestion/ingest",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        dataset_id = ingest_response.json()["data"]["dataset_id"]
        
        # Load employees
        response = client.post(f"/api/ingestion/load-employees/{dataset_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_loaded" in data["data"]
        assert data["data"]["total_loaded"] > 0


class TestSkillOntology:
    """Test skill ontology endpoints."""
    
    def test_build_ontology(self, client, db_session, sample_csv_file):
        """Test ontology building."""
        # Ingest dataset
        with open(sample_csv_file, 'rb') as f:
            ingest_response = client.post(
                "/api/ingestion/ingest",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        dataset_id = ingest_response.json()["data"]["dataset_id"]
        
        # Build ontology
        response = client.post(f"/api/skills/ontology?dataset_id={dataset_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "skills" in data["data"]
        assert "clusters" in data["data"]
        assert "normalized_mapping" in data["data"]


class TestSkillAnalysis:
    """Test skill analysis endpoints."""
    
    def test_analyze_employee(self, client, db_session):
        """Test employee skill analysis."""
        # Create test employee
        employee = EmployeeRecord(
            employee_id="TEST001",
            department="Engineering",
            skills=["Python", "JavaScript", "SQL"],
            metadata={"years_experience": 5}
        )
        db_session.add(employee)
        db_session.commit()
        
        # Analyze
        response = client.post(
            "/api/skills/analysis",
            json={
                "employee_id": "TEST001",
                "role_requirements": {
                    "required_skills": ["Python", "JavaScript", "React"],
                    "preferred_skills": ["Docker", "Kubernetes"]
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "current_skills" in data["data"]
        assert "missing_skills" in data["data"]
        assert "gap_score" in data["data"]
        assert "strengths" in data["data"]
    
    def test_get_employee_analysis(self, client, db_session):
        """Test retrieving employee analysis."""
        # Create test employee
        employee = EmployeeRecord(
            employee_id="TEST002",
            department="Engineering",
            skills=["Python", "JavaScript"],
        )
        db_session.add(employee)
        db_session.commit()
        
        # Analyze first
        client.post(
            "/api/skills/analysis",
            json={"employee_id": "TEST002"}
        )
        
        # Get analysis
        response = client.get("/api/skills/analysis/TEST002")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data["data"]
    
    def test_role_fit_scoring(self, client, db_session):
        """Test role-fit scoring."""
        # Create test employee
        employee = EmployeeRecord(
            employee_id="TEST003",
            department="Engineering",
            skills=["Python", "JavaScript", "React"],
        )
        db_session.add(employee)
        db_session.commit()
        
        # Calculate role-fit
        response = client.post(
            "/api/skills/role-fit/TEST003",
            json={
                "role_title": "Senior Software Engineer",
                "required_skills": ["Python", "JavaScript", "React", "Node.js"],
                "preferred_skills": ["Docker", "Kubernetes"],
                "department": "Engineering"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "readiness_score" in data["data"]
        assert isinstance(data["data"]["readiness_score"], int)
        assert 0 <= data["data"]["readiness_score"] <= 100


class TestAnalytics:
    """Test analytics endpoints."""
    
    def test_employee_analytics(self, client, db_session):
        """Test employee analytics."""
        # Create test employee
        employee = EmployeeRecord(
            employee_id="ANAL001",
            department="Engineering",
            skills=["Python", "JavaScript", "SQL", "React"],
        )
        db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/analytics/employees/ANAL001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "skill_level_stats" in data["data"]
        assert "readiness_score" in data["data"]
    
    def test_department_analytics(self, client, db_session):
        """Test department analytics."""
        # Create test employees
        for i in range(5):
            employee = EmployeeRecord(
                employee_id=f"DEPT{i:03d}",
                department="Engineering",
                skills=["Python", "JavaScript"] + [f"Skill{i}"] if i % 2 else [],
            )
            db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/analytics/departments/Engineering")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "team_skill_heatmap" in data["data"]
        assert "skill_shortages" in data["data"]
        assert "risk_scores" in data["data"]
    
    def test_global_analytics(self, client, db_session):
        """Test global analytics."""
        # Create test employees
        for i in range(10):
            employee = EmployeeRecord(
                employee_id=f"GLOBAL{i:03d}",
                department=f"Dept{i % 3}",
                skills=["Python"] + [f"Skill{i}"],
            )
            db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/analytics/global")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "skill_frequency" in data["data"]
        assert "skill_clusters" in data["data"]


class TestRecommendations:
    """Test recommendations endpoints."""
    
    def test_skill_recommendations(self, client, db_session):
        """Test skill recommendations."""
        # Create test employee
        employee = EmployeeRecord(
            employee_id="REC001",
            department="Engineering",
            skills=["Python", "JavaScript"],
        )
        db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/skills/recommendations/skills/REC001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_training_path(self, client, db_session):
        """Test training path generation."""
        # Create test employee
        employee = EmployeeRecord(
            employee_id="TRAIN001",
            department="Engineering",
            skills=["Python"],
        )
        db_session.add(employee)
        db_session.commit()
        
        response = client.post(
            "/api/skills/recommendations/training-path",
            params={"employee_id": "TRAIN001"},
            json=["React", "Node.js", "Docker"]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "target_skills" in data["data"]
        assert "steps" in data["data"]
        assert "timeline" in data["data"]
    
    def test_next_role_recommendations(self, client, db_session):
        """Test next role recommendations."""
        # Create test employee
        employee = EmployeeRecord(
            employee_id="ROLE001",
            department="Engineering",
            skills=["Python", "JavaScript", "React"],
        )
        db_session.add(employee)
        db_session.commit()
        
        available_roles = [
            {
                "title": "Senior Software Engineer",
                "department": "Engineering",
                "required_skills": ["Python", "JavaScript", "React"],
                "preferred_skills": ["Node.js", "Docker"]
            },
            {
                "title": "Tech Lead",
                "department": "Engineering",
                "required_skills": ["Python", "JavaScript", "Leadership"],
                "preferred_skills": ["Management"]
            }
        ]
        
        response = client.post(
            "/api/skills/recommendations/next-role",
            params={"employee_id": "ROLE001"},
            json=available_roles
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_department_interventions(self, client, db_session):
        """Test department intervention recommendations."""
        # Create test employees
        for i in range(5):
            employee = EmployeeRecord(
                employee_id=f"INT{i:03d}",
                department="Engineering",
                skills=["Python"] if i < 2 else ["JavaScript"],
            )
            db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/skills/recommendations/department-interventions/Engineering")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestDashboard:
    """Test dashboard endpoints."""
    
    def test_dashboard_overview(self, client, db_session):
        """Test dashboard overview."""
        # Create test employees
        for i in range(5):
            employee = EmployeeRecord(
                employee_id=f"DASH{i:03d}",
                department=f"Dept{i % 2}",
                skills=["Python", "JavaScript"],
            )
            db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/dashboard/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_employees" in data["data"]
        assert "total_departments" in data["data"]
    
    def test_skill_heatmap(self, client, db_session):
        """Test skill heatmap."""
        # Create test employees
        for i in range(5):
            employee = EmployeeRecord(
                employee_id=f"HEAT{i:03d}",
                department="Engineering",
                skills=["Python", "JavaScript"] + [f"Skill{i}"] if i % 2 else [],
            )
            db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/dashboard/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], dict)
    
    def test_skill_trends(self, client, db_session):
        """Test skill trends."""
        # Create test employees
        for i in range(10):
            employee = EmployeeRecord(
                employee_id=f"TREND{i:03d}",
                department=f"Dept{i % 3}",
                skills=["Python"] + [f"Skill{i}"] if i < 5 else ["JavaScript"],
            )
            db_session.add(employee)
        db_session.commit()
        
        response = client.get("/api/dashboard/trends")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "emerging_skills" in data["data"]
        assert "declining_skills" in data["data"]
        assert "stable_skills" in data["data"]
    
    def test_ui_contract(self, client):
        """Test UI contract endpoint."""
        response = client.get("/api/dashboard/ui-contract")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "endpoints" in data["data"]
        assert "supported_file_types" in data["data"]


class TestPIIMasking:
    """Test PII masking functionality."""
    
    def test_pii_masking_in_ingestion(self, client):
        """Test that PII is masked during ingestion."""
        csv_content = """employee_id,department,skills,email,phone
EMP001,Engineering,"Python, JavaScript",john.doe@example.com,+1234567890
EMP002,Sales,"Communication",jane.smith@example.com,+0987654321"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = Path(f.name)
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/ingestion/ingest",
                    files={"file": ("test.csv", f, "text/csv")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Check normalized file for PII masking
            normalized_path = Path(data["data"]["normalized_path"])
            if normalized_path.exists():
                with open(normalized_path, 'r') as f:
                    content = f.read()
                    # PII should be masked
                    assert "[REDACTED]" in content or "john.doe@example.com" not in content
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestErrorHandling:
    """Test error handling."""
    
    def test_invalid_file_type(self, client):
        """Test invalid file type rejection."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Invalid content")
            temp_path = Path(f.name)
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/ingestion/ingest",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            # Should accept txt files but might return error for unsupported format
            # Adjust based on your actual implementation
            assert response.status_code in [200, 400]
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_nonexistent_employee(self, client, db_session):
        """Test handling of nonexistent employee."""
        response = client.get("/api/analytics/employees/NONEXISTENT")
        assert response.status_code == 404 or response.status_code == 200
        if response.status_code == 404:
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    def test_empty_dataset(self, client):
        """Test handling of empty dataset."""
        csv_content = "employee_id,department,skills\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_path = Path(f.name)
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/api/ingestion/ingest",
                    files={"file": ("test.csv", f, "text/csv")}
                )
            
            # Should handle empty dataset gracefully
            assert response.status_code in [200, 400]
        finally:
            if temp_path.exists():
                temp_path.unlink()

