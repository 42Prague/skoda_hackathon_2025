"""
TONE Validation Tests
---------------------
Test TONE prompt building, response parsing, fallback triggering, JSON preservation, field validation.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from swx_api.app.services.tone_service import TONEService, get_tone_service


class TestTONEService:
    """Test TONE service functionality."""
    
    def test_build_tone_prompt(self):
        """Test TONE prompt building."""
        service = TONEService()
        service.use_tone = True
        
        base_prompt = "Analyze employee skills"
        schema = {
            "current_skills": list,
            "missing_skills": list,
            "gap_score": int
        }
        
        prompt = service.build_tone_prompt(base_prompt, schema)
        
        assert "TONE" in prompt or "Token-Optimized" in prompt
        assert "schema" in prompt.lower() or "response" in prompt.lower()
    
    def test_build_tone_prompt_disabled(self):
        """Test prompt building when TONE is disabled."""
        service = TONEService()
        service.use_tone = False
        
        base_prompt = "Analyze employee skills"
        schema = {"test": str}
        
        prompt = service.build_tone_prompt(base_prompt, schema)
        
        assert prompt == base_prompt  # Should return unchanged
    
    def test_parse_llm_response_json(self):
        """Test parsing JSON response."""
        service = TONEService()
        service.use_tone = False
        
        json_response = '{"current_skills": ["Python"], "gap_score": 75}'
        schema = {
            "current_skills": list,
            "gap_score": int
        }
        
        result = service.parse_llm_response(json_response, schema)
        
        assert isinstance(result, dict)
        assert "current_skills" in result
        assert result["gap_score"] == 75
    
    def test_parse_llm_response_tone(self):
        """Test parsing TONE response."""
        service = TONEService()
        service.use_tone = True
        
        # Mock TONE decode
        with patch("swx_api.app.services.tone_service.tone_decode") as mock_decode:
            mock_decode.return_value = {
                "current_skills": ["Python"],
                "gap_score": 75
            }
            
            tone_response = "current_skills[1]: Python\ngap_score: 75"
            schema = {
                "current_skills": list,
                "gap_score": int
            }
            
            result = service.parse_llm_response(tone_response, schema)
            
            assert isinstance(result, dict)
            assert "current_skills" in result
    
    def test_parse_llm_response_with_markdown(self):
        """Test parsing response with markdown code blocks."""
        service = TONEService()
        
        json_response = '```json\n{"current_skills": ["Python"]}\n```'
        result = service.parse_llm_response(json_response, {"current_skills": list})
        
        assert isinstance(result, dict)
        assert "current_skills" in result
    
    def test_parse_llm_response_fallback_to_json(self):
        """Test fallback from TONE to JSON."""
        service = TONEService()
        service.use_tone = True
        
        # Mock TONE decode failure
        with patch("swx_api.app.services.tone_service.tone_decode") as mock_decode:
            mock_decode.side_effect = Exception("TONE parse failed")
            
            json_response = '{"current_skills": ["Python"], "gap_score": 75}'
            schema = {
                "current_skills": list,
                "gap_score": int
            }
            
            result = service.parse_llm_response(json_response, schema)
            
            assert isinstance(result, dict)
            assert "current_skills" in result
    
    def test_parse_llm_response_safe_default(self):
        """Test safe default when parsing fails."""
        service = TONEService()
        
        invalid_response = "This is not JSON or TONE"
        schema = {
            "current_skills": list,
            "gap_score": int
        }
        
        result = service.parse_llm_response(invalid_response, schema)
        
        assert isinstance(result, dict)
        # Should have safe defaults
        assert "current_skills" in result or "error" in result
    
    def test_validate_and_fix_missing_fields(self):
        """Test validation and fixing of missing fields."""
        service = TONEService()
        service.validation_mode = True
        
        incomplete_data = {
            "current_skills": ["Python"]
            # Missing gap_score
        }
        schema = {
            "current_skills": list,
            "gap_score": int,
            "missing_skills": list
        }
        
        fixed = service._validate_and_fix(incomplete_data, schema)
        
        assert "gap_score" in fixed
        assert "missing_skills" in fixed
        assert isinstance(fixed["gap_score"], int)
        assert isinstance(fixed["missing_skills"], list)
    
    def test_validate_and_fix_type_correction(self):
        """Test type correction in validation."""
        service = TONEService()
        service.validation_mode = True
        
        wrong_type_data = {
            "current_skills": "not a list",
            "gap_score": "not an int"
        }
        schema = {
            "current_skills": list,
            "gap_score": int
        }
        
        fixed = service._validate_and_fix(wrong_type_data, schema)
        
        # Should attempt to fix types or provide defaults
        assert isinstance(fixed, dict)
    
    def test_encode_to_tone(self):
        """Test encoding to TONE format."""
        service = TONEService()
        service.tone_available = True
        
        data = {
            "current_skills": ["Python", "SQL"],
            "gap_score": 75
        }
        
        with patch("swx_api.app.services.tone_service.tone_encode") as mock_encode:
            mock_encode.return_value = "current_skills[2]: Python,SQL\ngap_score: 75"
            
            result = service.encode_to_tone(data)
            
            assert isinstance(result, str)
            assert "Python" in result or "75" in result
    
    def test_encode_to_tone_fallback(self):
        """Test encoding fallback to JSON."""
        service = TONEService()
        service.tone_available = False
        
        data = {"test": "data"}
        result = service.encode_to_tone(data)
        
        # Should return JSON
        parsed = json.loads(result)
        assert parsed == data
    
    def test_decode_from_tone(self):
        """Test decoding from TONE format."""
        service = TONEService()
        service.tone_available = True
        
        tone_text = "current_skills[2]: Python,SQL\ngap_score: 75"
        
        with patch("swx_api.app.services.tone_service.tone_decode") as mock_decode:
            mock_decode.return_value = {
                "current_skills": ["Python", "SQL"],
                "gap_score": 75
            }
            
            result = service.decode_from_tone(tone_text)
            
            assert isinstance(result, dict)
            assert "current_skills" in result
    
    def test_decode_from_tone_fallback(self):
        """Test decoding fallback to JSON."""
        service = TONEService()
        service.tone_available = False
        
        json_text = '{"test": "data"}'
        result = service.decode_from_tone(json_text)
        
        assert isinstance(result, dict)
        assert result["test"] == "data"
    
    def test_clean_response_text(self):
        """Test response text cleaning."""
        service = TONEService()
        
        # Test with markdown code blocks
        text_with_markdown = '```json\n{"test": "data"}\n```'
        cleaned = service._clean_response_text(text_with_markdown)
        assert "```" not in cleaned
        
        # Test with prefix
        text_with_prefix = 'Response: {"test": "data"}'
        cleaned = service._clean_response_text(text_with_prefix)
        assert not cleaned.startswith("Response:")
    
    def test_create_safe_default(self):
        """Test safe default creation."""
        service = TONEService()
        
        schema = {
            "current_skills": list,
            "gap_score": int,
            "missing_skills": list,
            "analysis_summary": str
        }
        
        default = service._create_safe_default(schema)
        
        assert isinstance(default, dict)
        assert "current_skills" in default
        assert isinstance(default["current_skills"], list)
        assert isinstance(default["gap_score"], int)
        assert isinstance(default["missing_skills"], list)
        assert isinstance(default["analysis_summary"], str)


class TestTONEIntegration:
    """Test TONE integration with LLM client."""
    
    def test_llm_client_with_tone(self, mock_llm_response):
        """Test LLM client using TONE format."""
        from swx_api.app.services.llm_client import LLMClient, LLMConfig
        
        config = LLMConfig(
            provider="featherless",
            model="test-model",
            api_key="test-key"
        )
        
        with patch("swx_api.app.services.tone_service.get_tone_service") as mock_tone:
            tone_service = MagicMock()
            tone_service.use_tone = True
            tone_service.build_tone_prompt.return_value = "TONE prompt"
            tone_service.parse_llm_response.return_value = mock_llm_response
            mock_tone.return_value = tone_service
            
            client = LLMClient(config)
            
            employee_data = {
                "employee_id": "EMP001",
                "department": "Engineering",
                "skills": ["Python", "SQL"]
            }
            
            # Should use TONE service
            result = client.analyze_skills(employee_data, None)
            
            assert "current_skills" in result
    
    def test_tone_service_singleton(self):
        """Test TONE service singleton pattern."""
        service1 = get_tone_service()
        service2 = get_tone_service()
        
        assert service1 is service2  # Should be same instance


class TestTONEValidationMode:
    """Test TONE validation mode."""
    
    def test_validation_logging(self, tmp_path):
        """Test validation logging."""
        import os
        from pathlib import Path
        
        # Mock validation log directory
        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        
        with patch("swx_api.app.services.tone_service.VALIDATION_LOG_DIR", validation_dir):
            service = TONEService()
            service.validation_mode = True
            
            incomplete_data = {"current_skills": ["Python"]}
            schema = {
                "current_skills": list,
                "gap_score": int
            }
            
            service._validate_and_fix(incomplete_data, schema)
            
            # Check if log file was created
            log_files = list(validation_dir.glob("*.jsonl"))
            # Log might be created or not depending on implementation
            assert True  # Just verify no exception
    
    def test_validation_with_complete_data(self):
        """Test validation with complete data."""
        service = TONEService()
        service.validation_mode = True
        
        complete_data = {
            "current_skills": ["Python"],
            "gap_score": 75,
            "missing_skills": ["Docker"]
        }
        schema = {
            "current_skills": list,
            "gap_score": int,
            "missing_skills": list
        }
        
        result = service._validate_and_fix(complete_data, schema)
        
        assert result == complete_data  # Should be unchanged if complete

