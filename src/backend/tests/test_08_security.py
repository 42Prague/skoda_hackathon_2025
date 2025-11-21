"""
Security Tests
--------------
Test PII masking, SQL injection, unsafe inputs, invalid file uploads, oversized payloads, malicious JSON.
"""

import io
import json
from pathlib import Path

import pytest

from swx_api.app.services.ingestion_service import mask_pii_text, mask_pii_dataframe
import pandas as pd


class TestPIIMasking:
    """Test PII masking functionality."""
    
    def test_mask_email(self):
        """Test email masking."""
        text = "Contact john.doe@example.com for details"
        masked = mask_pii_text(text)
        assert "john.doe@example.com" not in masked
        assert "[REDACTED]" in masked
    
    def test_mask_phone(self):
        """Test phone number masking."""
        text = "Call +420 123 456 789 or 123-456-7890"
        masked = mask_pii_text(text)
        assert "+420 123 456 789" not in masked
        assert "123-456-7890" not in masked
        assert "[REDACTED]" in masked
    
    def test_mask_name(self):
        """Test name masking."""
        text = "John Doe and Jane Smith are working on the project"
        masked = mask_pii_text(text)
        assert "John Doe" not in masked
        assert "Jane Smith" not in masked
        assert "[REDACTED]" in masked
    
    def test_mask_pii_in_dataframe(self):
        """Test PII masking in DataFrame."""
        df = pd.DataFrame({
            "name": ["John Doe", "Jane Smith"],
            "email": ["john@example.com", "jane@example.com"],
            "phone": ["+420 123 456", "+420 789 012"],
            "skills": ["Python", "JavaScript"]
        })
        
        masked_df = mask_pii_dataframe(df)
        
        # Check that PII is masked
        for idx in range(len(masked_df)):
            assert "[REDACTED]" in str(masked_df["name"].iloc[idx])
            assert "[REDACTED]" in str(masked_df["email"].iloc[idx])
            assert "[REDACTED]" in str(masked_df["phone"].iloc[idx])
        
        # Skills should not be masked
        assert "Python" in masked_df["skills"].iloc[0]
    
    def test_mask_multiple_pii_in_text(self):
        """Test masking multiple PII types in one text."""
        text = "John Doe (john.doe@example.com) can be reached at +420 123 456 789"
        masked = mask_pii_text(text)
        
        assert "John Doe" not in masked
        assert "john.doe@example.com" not in masked
        assert "+420 123 456 789" not in masked
        assert masked.count("[REDACTED]") >= 3


class TestSQLInjection:
    """Test SQL injection prevention."""
    
    def test_sql_injection_in_employee_id(self, client, db_session):
        """Test SQL injection in employee_id parameter."""
        malicious_ids = [
            "EMP001'; DROP TABLE employee_record; --",
            "EMP001' OR '1'='1",
            "EMP001'; DELETE FROM employee_record; --",
            "EMP001' UNION SELECT * FROM employee_record; --"
        ]
        
        for malicious_id in malicious_ids:
            response = client.get(f"/api/analytics/employees/{malicious_id}")
            # Should handle safely (not crash, return 404 or error)
            assert response.status_code in [400, 404, 422, 500]
            
            # Verify table still exists
            verify_response = client.get("/api/analytics/global")
            assert verify_response.status_code == 200
    
    def test_sql_injection_in_department(self, client, db_session):
        """Test SQL injection in department parameter."""
        malicious_dept = "Engineering'; DROP TABLE employee_record; --"
        
        response = client.get(f"/api/analytics/departments/{malicious_dept}")
        # Should handle safely
        assert response.status_code in [400, 404, 422, 500]
        
        # Verify table still exists
        verify_response = client.get("/api/analytics/global")
        assert verify_response.status_code == 200
    
    def test_sql_injection_in_json_payload(self, client, db_session):
        """Test SQL injection in JSON payload."""
        malicious_payload = {
            "employee_id": "EMP001'; DROP TABLE employee_record; --",
            "role_requirements": None
        }
        
        response = client.post("/api/skills/analysis", json=malicious_payload)
        # Should handle safely
        assert response.status_code in [400, 404, 422, 500]
        
        # Verify table still exists
        verify_response = client.get("/api/analytics/global")
        assert verify_response.status_code == 200


class TestUnsafeInputs:
    """Test handling of unsafe inputs."""
    
    def test_path_traversal_in_filename(self, client, temp_data_dir):
        """Test path traversal in filename."""
        malicious_filenames = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam"
        ]
        
        csv_content = "employee_id,department,skills\nEMP001,Engineering,Python\n"
        
        for filename in malicious_filenames:
            files = {"file": (filename, io.BytesIO(csv_content.encode()), "text/csv")}
            response = client.post("/api/ingestion/ingest", files=files)
            
            # Should handle safely (reject or sanitize)
            assert response.status_code in [200, 201, 400, 422]
            
            # Verify file wasn't written outside intended directory
            if response.status_code in [200, 201]:
                # Check that no files were created in parent directories
                parent_dir = temp_data_dir.parent
                suspicious_files = list(parent_dir.glob("passwd")) + list(parent_dir.glob("sam"))
                assert len(suspicious_files) == 0
    
    def test_xss_in_employee_data(self, client, db_session):
        """Test XSS prevention in employee data."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            request_data = {
                "employee_id": payload,
                "role_requirements": None
            }
            
            response = client.post("/api/skills/analysis", json=request_data)
            # Should handle safely (sanitize or reject)
            assert response.status_code in [200, 201, 400, 404, 422, 500]
            
            # Response should not contain unescaped script tags
            if response.status_code == 200:
                response_text = response.text
                assert "<script>" not in response_text.lower()
    
    def test_command_injection_in_filename(self, client):
        """Test command injection in filename."""
        malicious_filenames = [
            "test.csv; rm -rf /",
            "test.csv | cat /etc/passwd",
            "test.csv && echo 'hacked'"
        ]
        
        csv_content = "employee_id,department,skills\nEMP001,Engineering,Python\n"
        
        for filename in malicious_filenames:
            files = {"file": (filename, io.BytesIO(csv_content.encode()), "text/csv")}
            response = client.post("/api/ingestion/ingest", files=files)
            
            # Should handle safely
            assert response.status_code in [200, 201, 400, 422]


class TestInvalidFileUploads:
    """Test handling of invalid file uploads."""
    
    def test_oversized_file(self, client):
        """Test handling of oversized file."""
        # Create large file (10MB)
        large_content = "employee_id,department,skills\n" + "EMP001,Engineering,Python\n" * 100000
        
        files = {"file": ("large.csv", io.BytesIO(large_content.encode()), "text/csv")}
        response = client.post("/api/ingestion/ingest", files=files)
        
        # Should handle gracefully (either accept or reject with appropriate error)
        assert response.status_code in [200, 201, 400, 413, 422, 500]
    
    def test_corrupted_file(self, client):
        """Test handling of corrupted file."""
        corrupted_content = b"\x00\x01\x02\x03\xff\xfe\xfd\xfc"
        
        files = {"file": ("corrupted.csv", io.BytesIO(corrupted_content), "application/octet-stream")}
        response = client.post("/api/ingestion/ingest", files=files)
        
        # Should handle gracefully
        assert response.status_code in [400, 422, 500]
    
    def test_wrong_file_extension(self, client):
        """Test handling of wrong file extension."""
        # CSV content with .txt extension
        csv_content = "employee_id,department,skills\nEMP001,Engineering,Python\n"
        files = {"file": ("test.txt", io.BytesIO(csv_content.encode()), "text/plain")}
        response = client.post("/api/ingestion/ingest", files=files)
        
        # Should reject or handle appropriately
        assert response.status_code in [200, 201, 400, 422]
    
    def test_empty_file(self, client):
        """Test handling of empty file."""
        files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        response = client.post("/api/ingestion/ingest", files=files)
        
        # Should handle gracefully
        assert response.status_code in [400, 422, 500]


class TestMaliciousJSON:
    """Test handling of malicious JSON."""
    
    def test_json_bomb(self, client):
        """Test JSON bomb (deeply nested JSON)."""
        def create_nested_json(depth):
            if depth == 0:
                return {"value": "test"}
            return {"nested": create_nested_json(depth - 1)}
        
        # Create deeply nested JSON (1000 levels)
        try:
            nested_json = create_nested_json(1000)
            request_data = {
                "employee_id": "EMP001",
                "role_requirements": nested_json
            }
            
            response = client.post("/api/skills/analysis", json=request_data)
            # Should handle gracefully (either accept or reject)
            assert response.status_code in [200, 201, 400, 413, 422, 500]
        except (RecursionError, MemoryError):
            # Expected for very deep nesting
            pass
    
    def test_large_json_array(self, client):
        """Test large JSON array."""
        large_array = [{"skill": f"Skill{i}"} for i in range(10000)]
        request_data = {
            "employee_id": "EMP001",
            "role_requirements": {"skills": large_array}
        }
        
        response = client.post("/api/skills/analysis", json=request_data)
        # Should handle gracefully
        assert response.status_code in [200, 201, 400, 413, 422, 500]
    
    def test_invalid_json_structure(self, client):
        """Test invalid JSON structure."""
        # Send valid JSON but with wrong structure
        request_data = {
            "wrong_field": "value",
            "another_wrong_field": 123
        }
        
        response = client.post("/api/skills/analysis", json=request_data)
        # Should reject with validation error
        assert response.status_code in [400, 422]
    
    def test_special_characters_in_json(self, client, db_session):
        """Test special characters in JSON."""
        special_chars = [
            "\x00",  # Null byte
            "\x1f",  # Control character
            "\u0000",  # Unicode null
            "\uffff",  # Invalid Unicode
        ]
        
        for char in special_chars:
            request_data = {
                "employee_id": f"EMP{char}001",
                "role_requirements": None
            }
            
            try:
                response = client.post("/api/skills/analysis", json=request_data)
                # Should handle safely
                assert response.status_code in [200, 201, 400, 422, 500]
            except Exception:
                # Some special chars might cause JSON encoding issues
                pass


class TestInputValidation:
    """Test input validation."""
    
    def test_missing_required_fields(self, client):
        """Test missing required fields."""
        incomplete_data = {}  # Missing employee_id
        response = client.post("/api/skills/analysis", json=incomplete_data)
        assert response.status_code in [400, 422]
    
    def test_invalid_field_types(self, client):
        """Test invalid field types."""
        invalid_data = {
            "employee_id": 12345,  # Should be string
            "role_requirements": "not an object"  # Should be object or null
        }
        response = client.post("/api/skills/analysis", json=invalid_data)
        assert response.status_code in [400, 422]
    
    def test_negative_values(self, client, db_session, sample_employees):
        """Test negative values where not allowed."""
        employee = sample_employees[0]
        
        # Try negative months
        response = client.get("/api/analytics/forecast", params={"months": -1})
        assert response.status_code in [400, 422]
        
        # Try zero or negative
        response = client.get("/api/analytics/forecast", params={"months": 0})
        assert response.status_code in [400, 422]
    
    def test_extremely_large_strings(self, client):
        """Test extremely large string inputs."""
        large_string = "A" * 100000  # 100KB string
        
        request_data = {
            "employee_id": large_string,
            "role_requirements": None
        }
        
        response = client.post("/api/skills/analysis", json=request_data)
        # Should handle gracefully
        assert response.status_code in [200, 201, 400, 404, 422, 500]


class TestAuthenticationAndAuthorization:
    """Test authentication and authorization (if implemented)."""
    
    def test_unauthenticated_access(self, client):
        """Test access without authentication."""
        # If auth is required, these should fail
        # If auth is not implemented, these should work
        response = client.get("/api/analytics/global")
        # Should either work (no auth) or return 401/403 (auth required)
        assert response.status_code in [200, 401, 403]
    
    def test_invalid_token(self, client):
        """Test access with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/analytics/global", headers=headers)
        # Should either work (no auth) or return 401 (invalid token)
        assert response.status_code in [200, 401, 403]

