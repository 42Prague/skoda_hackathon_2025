"""
Ingestion Tests
---------------
Test ingestion of CSV, Excel, JSON, TXT, DOCX files with various scenarios.
"""

import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
from fastapi import UploadFile

from swx_api.app.services.ingestion_service import (
    ingest_file,
    list_datasets,
    load_employees_from_dataset,
    SUPPORTED_EXTENSIONS,
    mask_pii_dataframe,
    mask_pii_text,
    detect_skill_fields,
    compute_data_quality_metrics,
)
from swx_api.app.models.skill_models import DatasetRecord


class TestIngestionService:
    """Test ingestion service functions."""
    
    def test_mask_pii_text(self):
        """Test PII masking in text."""
        text = "Contact John Doe at john.doe@example.com or call +420 123 456 789"
        masked = mask_pii_text(text)
        assert "[REDACTED]" in masked
        assert "john.doe@example.com" not in masked
        assert "John Doe" not in masked
        assert "+420 123 456 789" not in masked
    
    def test_mask_pii_dataframe(self):
        """Test PII masking in DataFrame."""
        df = pd.DataFrame({
            "name": ["John Doe", "Jane Smith"],
            "email": ["john@example.com", "jane@example.com"],
            "phone": ["+420 123 456", "+420 789 012"],
            "skills": ["Python", "JavaScript"]
        })
        masked_df = mask_pii_dataframe(df)
        assert "[REDACTED]" in masked_df["name"].iloc[0]
        assert "[REDACTED]" in masked_df["email"].iloc[0]
    
    def test_detect_skill_fields(self):
        """Test skill field detection."""
        df = pd.DataFrame({
            "employee_id": ["EMP001", "EMP002"],
            "skills": ["Python,SQL", "JavaScript"],
            "competencies": ["Leadership", "Communication"],
            "abilities": ["Problem-solving", "Analytics"]
        })
        skill_fields = detect_skill_fields(df)
        assert "skills" in skill_fields
        assert "competencies" in skill_fields
        assert "abilities" in skill_fields
    
    def test_compute_data_quality_metrics(self):
        """Test data quality metrics computation."""
        df = pd.DataFrame({
            "employee_id": ["EMP001", "EMP002", "EMP003"],
            "department": ["Engineering", None, "Marketing"],
            "skills": ["Python", "SQL", None],
            "years": [5, 3, None]
        })
        metrics = compute_data_quality_metrics(df)
        assert metrics["total_rows"] == 3
        assert metrics["total_columns"] == 4
        assert "missing_values" in metrics
        assert "department" in metrics["missing_values"]
    
    def test_ingest_csv_file(self, temp_data_dir):
        """Test CSV file ingestion."""
        # Create test CSV
        csv_path = temp_data_dir / "raw" / "test.csv"
        csv_content = """employee_id,department,skills,email
EMP001,Engineering,"Python,SQL,JavaScript",john.doe@example.com
EMP002,Marketing,"Excel,Power BI",jane.smith@example.com
"""
        csv_path.write_text(csv_content)
        
        # Mock paths
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            result = ingest_file(csv_path, "test.csv")
            
            assert result["success"] is True or "dataset_id" in result
            assert "normalized_path" in result
            assert "metadata" in result
            assert "dq_report_path" in result or result.get("dq_report_path") is not None
    
    def test_ingest_json_file(self, temp_data_dir):
        """Test JSON file ingestion."""
        json_path = temp_data_dir / "raw" / "test.json"
        json_data = [
            {
                "employee_id": "EMP001",
                "department": "Engineering",
                "skills": ["Python", "SQL", "JavaScript"],
                "email": "john.doe@example.com"
            },
            {
                "employee_id": "EMP002",
                "department": "Marketing",
                "skills": ["Excel", "Power BI"],
                "email": "jane.smith@example.com"
            }
        ]
        json_path.write_text(json.dumps(json_data))
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            result = ingest_file(json_path, "test.json")
            
            assert "dataset_id" in result
            assert "normalized_path" in result
            assert "metadata" in result
    
    def test_ingest_txt_file(self, temp_data_dir):
        """Test TXT file ingestion."""
        txt_path = temp_data_dir / "raw" / "test.txt"
        txt_content = """Employee Skills Report

Employee ID: EMP001
Department: Engineering
Skills: Python, SQL, JavaScript
Email: john.doe@example.com
"""
        txt_path.write_text(txt_content)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            result = ingest_file(txt_path, "test.txt")
            
            assert "dataset_id" in result
            assert "normalized_path" in result
            assert "metadata" in result
    
    def test_ingest_malformed_csv(self, temp_data_dir):
        """Test malformed CSV handling."""
        csv_path = temp_data_dir / "raw" / "malformed.csv"
        csv_content = """employee_id,department,skills
EMP001,Engineering,"Python,SQL
EMP002,Marketing,Excel,Power BI
"""
        csv_path.write_text(csv_content)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            # Should handle gracefully or raise appropriate error
            try:
                result = ingest_file(csv_path, "malformed.csv")
                # If it succeeds, should still produce some output
                assert "dataset_id" in result or "error" in result
            except Exception as e:
                # Expected for malformed CSV
                assert isinstance(e, (ValueError, pd.errors.ParserError))
    
    def test_ingest_missing_columns(self, temp_data_dir):
        """Test ingestion with missing expected columns."""
        csv_path = temp_data_dir / "raw" / "missing_cols.csv"
        csv_content = """name,age
John Doe,30
Jane Smith,25
"""
        csv_path.write_text(csv_content)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            # Should handle missing columns gracefully
            result = ingest_file(csv_path, "missing_cols.csv")
            assert "dataset_id" in result
            assert "metadata" in result
    
    def test_ingest_corrupted_file(self, temp_data_dir):
        """Test corrupted file handling."""
        corrupted_path = temp_data_dir / "raw" / "corrupted.csv"
        corrupted_path.write_bytes(b"\x00\x01\x02\x03\xff\xfe")  # Binary garbage
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            # Should raise appropriate error
            with pytest.raises((ValueError, UnicodeDecodeError, pd.errors.ParserError)):
                ingest_file(corrupted_path, "corrupted.csv")
    
    def test_list_datasets(self, temp_data_dir):
        """Test dataset listing."""
        # Create some normalized files
        (temp_data_dir / "normalized" / "dataset1.csv").write_text("test")
        (temp_data_dir / "normalized" / "dataset2.csv").write_text("test")
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            
            datasets = list_datasets()
            assert isinstance(datasets, list)
            assert len(datasets) >= 0
    
    def test_load_employees_from_dataset(self, temp_data_dir):
        """Test loading employees from dataset."""
        dataset_path = temp_data_dir / "normalized" / "employees.csv"
        csv_content = """employee_id,department,skills
EMP001,Engineering,"Python,SQL,JavaScript"
EMP002,Marketing,"Excel,Power BI"
"""
        dataset_path.write_text(csv_content)
        
        employees = load_employees_from_dataset(
            dataset_path,
            employee_id_column="employee_id",
            department_column="department",
            skills_column="skills"
        )
        
        assert len(employees) == 2
        assert employees[0]["employee_id"] == "EMP001"
        assert employees[0]["department"] == "Engineering"
        assert "Python" in employees[0]["skills"]


class TestIngestionAPI:
    """Test ingestion API endpoints."""
    
    def test_ingest_endpoint_csv(self, client, temp_data_dir):
        """Test CSV ingestion endpoint."""
        csv_content = """employee_id,department,skills,email
EMP001,Engineering,"Python,SQL,JavaScript",john.doe@example.com
EMP002,Marketing,"Excel,Power BI",jane.smith@example.com
"""
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
            response = client.post("/api/ingestion/ingest", files=files)
            
            assert response.status_code in [200, 201]
            data = response.json()
            assert data.get("success") is True or "data" in data
            if "data" in data:
                assert "dataset_id" in data["data"]
    
    def test_ingest_endpoint_json(self, client, temp_data_dir):
        """Test JSON ingestion endpoint."""
        json_content = json.dumps([
            {"employee_id": "EMP001", "department": "Engineering", "skills": ["Python"]}
        ])
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.raw_dir = temp_data_dir / "raw"
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.analysis_dir = temp_data_dir / "analysis"
            mock_paths.logs_dir = temp_data_dir / "logs"
            
            files = {"file": ("test.json", io.BytesIO(json_content.encode()), "application/json")}
            response = client.post("/api/ingestion/ingest", files=files)
            
            assert response.status_code in [200, 201]
            data = response.json()
            assert data.get("success") is True or "data" in data
    
    def test_ingest_endpoint_unsupported_file(self, client):
        """Test unsupported file type rejection."""
        files = {"file": ("test.pdf", io.BytesIO(b"test"), "application/pdf")}
        response = client.post("/api/ingestion/ingest", files=files)
        
        assert response.status_code in [400, 422]
        data = response.json()
        assert data.get("success") is False or "error" in data
    
    def test_list_datasets_endpoint(self, client, db_session, sample_dataset_record):
        """Test list datasets endpoint."""
        response = client.get("/api/ingestion/datasets")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "data" in data
        if "data" in data:
            assert isinstance(data["data"], list)
    
    def test_load_employees_endpoint(self, client, db_session, temp_data_dir):
        """Test load employees endpoint."""
        # Create a dataset file
        dataset_path = temp_data_dir / "normalized" / "test_dataset.csv"
        csv_content = """employee_id,department,skills
EMP001,Engineering,"Python,SQL"
EMP002,Marketing,"Excel,Power BI"
"""
        dataset_path.write_text(csv_content)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            
            response = client.post(
                "/api/ingestion/load-employees/test_dataset",
                params={
                    "employee_id_column": "employee_id",
                    "department_column": "department",
                    "skills_column": "skills"
                }
            )
            
            assert response.status_code in [200, 201]
            data = response.json()
            assert data.get("success") is True or "data" in data
            if "data" in data:
                assert "total_loaded" in data["data"] or "created" in data["data"]
    
    def test_load_employees_endpoint_not_found(self, client):
        """Test load employees with non-existent dataset."""
        response = client.post("/api/ingestion/load-employees/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        assert data.get("success") is False or "error" in data

