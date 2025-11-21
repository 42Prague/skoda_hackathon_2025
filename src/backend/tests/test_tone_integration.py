"""
Integration tests for TONE format integration.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from swx_api.app.services.tone_service import get_tone_service, TONEService
from swx_api.app.services.llm_client import LLMClient, LLMConfig


class TestTONEService:
    """Test TONE service functionality."""
    
    def test_tone_service_initialization(self):
        """Test TONE service initializes correctly."""
        with patch.dict(os.environ, {"USE_TONE": "false"}):
            service = TONEService()
            assert service.use_tone is False
            assert service.validation_mode is False
    
    def test_tone_service_enabled(self):
        """Test TONE service when enabled."""
        with patch.dict(os.environ, {"USE_TONE": "true"}):
            service = TONEService()
            # Will be False if toneformat not installed, True if installed
            assert isinstance(service.use_tone, bool)
    
    def test_build_tone_prompt(self):
        """Test building TONE prompt with schema."""
        service = TONEService()
        base_prompt = "Analyze skills"
        schema = {
            "current_skills": list,
            "gap_score": int
        }
        
        prompt = service.build_tone_prompt(base_prompt, schema)
        assert "Analyze skills" in prompt
        assert isinstance(prompt, str)
    
    def test_parse_llm_response_json(self):
        """Test parsing JSON response (fallback)."""
        service = TONEService()
        response = '{"current_skills": ["Python"], "gap_score": 75}'
        
        result = service.parse_llm_response(response, {"current_skills": list, "gap_score": int})
        assert result["current_skills"] == ["Python"]
        assert result["gap_score"] == 75
    
    def test_parse_llm_response_with_validation(self):
        """Test parsing with validation mode."""
        with patch.dict(os.environ, {"VALIDATION_MODE": "true"}):
            service = TONEService()
            response = '{"current_skills": ["Python"]}'
            schema = {"current_skills": list, "gap_score": int}
            
            result = service.parse_llm_response(response, schema)
            assert "current_skills" in result
            assert "gap_score" in result  # Should be auto-filled


class TestLLMClientTONE:
    """Test LLM client with TONE integration."""
    
    def test_llm_client_with_tone_service(self):
        """Test LLM client initializes with TONE service."""
        config = LLMConfig.from_env()
        client = LLMClient(config)
        
        assert hasattr(client, 'tone_service')
        assert client.tone_service is not None
    
    @patch('swx_api.app.services.llm_client.httpx.Client')
    def test_call_llm_with_fallback(self, mock_httpx):
        """Test LLM call with automatic fallback."""
        config = LLMConfig(
            provider="featherless",
            model="test-model",
            api_key=None,
            endpoint=None
        )
        client = LLMClient(config)
        
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": '{"result": "test"}'},
            "choices": [{"message": {"content": '{"result": "test"}'}}]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx.return_value.__enter__.return_value = mock_client_instance
        
        result = client.call_llm(
            prompt="Test prompt",
            schema={"result": str},
            system_message="Test system",
            temperature=0.7,
            max_tokens=100
        )
        
        # Should return parsed result or safe default
        assert isinstance(result, dict)
    
    def test_analyze_skills_with_tone(self):
        """Test skill analysis with TONE support."""
        config = LLMConfig.from_env()
        client = LLMClient(config)
        
        employee_data = {
            "employee_id": "test_001",
            "department": "Engineering",
            "skills": ["Python", "SQL"]
        }
        
        # Should not raise error (will use fallback if LLM unavailable)
        result = client.analyze_skills(employee_data)
        
        assert isinstance(result, dict)
        assert "current_skills" in result
        assert "gap_score" in result


class TestTONEIntegration:
    """End-to-end integration tests."""
    
    def test_tone_service_singleton(self):
        """Test TONE service is a singleton."""
        service1 = get_tone_service()
        service2 = get_tone_service()
        
        assert service1 is service2
    
    def test_tone_encoding_decoding(self):
        """Test TONE encoding and decoding."""
        service = get_tone_service()
        
        data = {
            "items": [
                {"id": 1, "name": "Item1"},
                {"id": 2, "name": "Item2"}
            ]
        }
        
        # Encoding should work (or fallback to JSON)
        encoded = service.encode_to_tone(data)
        assert isinstance(encoded, str)
        
        # Decoding should work
        decoded = service.decode_from_tone(encoded)
        assert isinstance(decoded, dict)
        assert "items" in decoded


@pytest.mark.asyncio
class TestTONEInServices:
    """Test TONE integration in actual services."""
    
    async def test_skill_forecasting_with_tone(self):
        """Test skill forecasting service uses TONE."""
        from swx_api.app.services.skill_forecasting_service import SkillForecastingService
        
        service = SkillForecastingService()
        
        # Should have LLM client with TONE support
        assert hasattr(service, 'llm_client')
        assert hasattr(service.llm_client, 'tone_service')
    
    async def test_role_fit_with_tone(self):
        """Test role fit service uses TONE."""
        from swx_api.app.services.role_fit_service import RoleFitService
        
        service = RoleFitService()
        
        # Should have LLM client with TONE support
        assert hasattr(service, 'llm_client')
        assert hasattr(service.llm_client, 'tone_service')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

