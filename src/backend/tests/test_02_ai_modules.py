"""
AI Module Tests
---------------
Test all AI modules with mock LLM, real LLM, local model fallback, and heuristic fallback.
"""

import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any

import pytest
import httpx

from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.skill_ai_service import SkillAIService
from swx_api.app.services.skill_recommendations_service import SkillRecommendationsService
from swx_api.app.services.role_fit_service import RoleFitService
from swx_api.app.services.skill_taxonomy_service import SkillTaxonomyService
from swx_api.app.services.skill_forecasting_service import SkillForecastingService
from swx_api.app.services.team_similarity_service import TeamSimilarityService
from swx_api.app.services.mentor_recommendation_service import MentorRecommendationService
from swx_api.app.services.scenario_simulation_service import ScenarioSimulationService


class TestLLMClient:
    """Test LLM client with various providers and fallbacks."""
    
    def test_llm_config_from_env(self):
        """Test LLM config loading from environment."""
        with patch.dict(os.environ, {
            "SKILL_LLM_PROVIDER": "featherless",
            "FEATHERLESS_API_KEY": "test_key",
            "FEATHERLESS_ENDPOINT": "https://api.test.com/v1"
        }):
            config = LLMConfig.from_env()
            assert config.provider == "featherless"
            assert config.api_key == "test_key"
            assert config.endpoint == "https://api.test.com/v1"
    
    def test_llm_client_heuristic_fallback(self, mock_llm_response):
        """Test heuristic fallback when LLM is unavailable."""
        config = LLMConfig(
            provider="featherless",
            model="test-model",
            api_key=None  # No API key = fallback
        )
        client = LLMClient(config)
        
        employee_data = {
            "employee_id": "EMP001",
            "department": "Engineering",
            "skills": ["Python", "SQL"]
        }
        role_requirements = {
            "required_skills": ["Python", "Docker"],
            "preferred_skills": ["Kubernetes"]
        }
        
        result = client.analyze_skills(employee_data, role_requirements)
        
        assert "current_skills" in result
        assert "missing_skills" in result
        assert "gap_score" in result
        assert isinstance(result["gap_score"], int)
        assert 0 <= result["gap_score"] <= 100
    
    @patch("swx_api.app.services.llm_client.OpenAI")
    def test_llm_client_featherless_success(self, mock_openai, mock_llm_response):
        """Test successful Featherless.ai API call."""
        # Mock OpenAI client
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"current_skills": ["Python"], "missing_skills": ["Docker"], "gap_score": 75, "strengths": [], "recommended_roles": [], "development_path": [], "analysis_summary": "Test"}'
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client_instance
        
        config = LLMConfig(
            provider="featherless",
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
            api_key="test_key",
            endpoint="https://api.featherless.ai/v1"
        )
        client = LLMClient(config)
        
        employee_data = {
            "employee_id": "EMP001",
            "department": "Engineering",
            "skills": ["Python", "SQL"]
        }
        
        result = client.analyze_skills(employee_data, None)
        
        assert "current_skills" in result
        assert "gap_score" in result
    
    @patch("httpx.Client")
    def test_llm_client_ollama_fallback(self, mock_httpx_client, mock_llm_response):
        """Test Ollama local model fallback."""
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": '{"current_skills": ["Python"], "missing_skills": ["Docker"], "gap_score": 75, "strengths": [], "recommended_roles": [], "development_path": [], "analysis_summary": "Test"}'}
        }
        mock_response.raise_for_status = MagicMock()
        mock_http_client = MagicMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__enter__.return_value = mock_http_client
        mock_http_client.__exit__.return_value = None
        mock_httpx_client.return_value = mock_http_client
        
        config = LLMConfig(
            provider="ollama",
            model="llama3.1",
            api_key=None,
            local_model_endpoint="http://localhost:11434/v1"
        )
        client = LLMClient(config)
        
        employee_data = {
            "employee_id": "EMP001",
            "department": "Engineering",
            "skills": ["Python", "SQL"]
        }
        
        result = client._analyze_with_ollama(
            "test prompt",
            {"current_skills": list, "missing_skills": list, "gap_score": int},
            employee_data,
            None
        )
        
        assert "current_skills" in result
        assert "gap_score" in result
    
    def test_llm_client_validate_analysis_result(self):
        """Test analysis result validation."""
        config = LLMConfig(provider="featherless", model="test", api_key=None)
        client = LLMClient(config)
        
        invalid_result = {"current_skills": "not a list"}
        validated = client._validate_analysis_result(invalid_result)
        
        assert isinstance(validated["current_skills"], list)
        assert isinstance(validated["gap_score"], int)


class TestSkillAIService:
    """Test Skill AI Service."""
    
    def test_analyze_employee_with_mock_llm(self, mock_llm_client, sample_employee_data):
        """Test employee analysis with mocked LLM."""
        service = SkillAIService()
        service.llm_client = mock_llm_client
        
        result = service.analyze_employee(
            "EMP001",
            sample_employee_data,
            None
        )
        
        assert "current_skills" in result
        assert "missing_skills" in result
        assert "gap_score" in result
        assert "strengths" in result
        assert "recommended_roles" in result
        assert "development_path" in result
        assert "analysis_summary" in result
    
    def test_analyze_employee_with_heuristic_fallback(self, sample_employee_data):
        """Test employee analysis with heuristic fallback."""
        with patch("swx_api.app.services.skill_ai_service.LLMClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.analyze_skills.side_effect = Exception("LLM unavailable")
            mock_client_class.return_value = mock_client
            
            service = SkillAIService()
            service.llm_client = mock_client
            
            # Should fallback to heuristic
            result = service.analyze_employee(
                "EMP001",
                sample_employee_data,
                None
            )
            
            assert "current_skills" in result
            assert "gap_score" in result
    
    def test_predict_role_readiness(self, mock_llm_client, sample_employee_data):
        """Test role readiness prediction."""
        service = SkillAIService()
        service.llm_client = mock_llm_client
        
        role_requirements = {
            "role_title": "Senior Software Engineer",
            "required_skills": ["Python", "Docker", "Kubernetes"],
            "preferred_skills": ["AWS", "CI/CD"]
        }
        
        result = service.predict_role_readiness(sample_employee_data, role_requirements)
        
        assert "role_fit_score" in result or "gap_score" in result
        assert isinstance(result.get("role_fit_score", result.get("gap_score", 0)), int)


class TestSkillRecommendationsService:
    """Test Skill Recommendations Service."""
    
    def test_recommend_skills(self, db_session, sample_employees):
        """Test skill recommendations."""
        service = SkillRecommendationsService()
        
        employee = sample_employees[0]
        recommendations = service.recommend_skills(
            employee.employee_id,
            employee.skills or [],
            employee.department
        )
        
        assert isinstance(recommendations, list)
    
    def test_recommend_training_path(self, db_session, sample_employees):
        """Test training path recommendations."""
        service = SkillRecommendationsService()
        
        employee = sample_employees[0]
        target_skills = ["Docker", "Kubernetes"]
        path = service.recommend_training_path(
            employee.employee_id,
            employee.skills or [],
            target_skills
        )
        
        assert isinstance(path, list) or isinstance(path, dict)


class TestRoleFitService:
    """Test Role Fit Service."""
    
    def test_calculate_role_fit(self, db_session, sample_employees):
        """Test role fit calculation."""
        service = RoleFitService()
        
        employee = sample_employees[0]
        role_requirements = {
            "required_skills": ["Python", "SQL"],
            "preferred_skills": ["Docker"]
        }
        
        fit_score = service.calculate_role_fit(
            employee.employee_id,
            employee.skills or [],
            role_requirements
        )
        
        assert isinstance(fit_score, dict) or isinstance(fit_score, int)
        if isinstance(fit_score, dict):
            assert "role_fit_score" in fit_score or "score" in fit_score


class TestSkillTaxonomyService:
    """Test Skill Taxonomy Service."""
    
    def test_build_taxonomy(self, db_session, sample_employees):
        """Test taxonomy building."""
        service = SkillTaxonomyService()
        
        all_skills = []
        for emp in sample_employees:
            if emp.skills:
                all_skills.extend(emp.skills)
        
        taxonomy = service.build_taxonomy(all_skills)
        
        assert isinstance(taxonomy, dict) or isinstance(taxonomy, list)


class TestSkillForecastingService:
    """Test Skill Forecasting Service."""
    
    def test_forecast_skill_demand(self, db_session, sample_employees):
        """Test skill demand forecasting."""
        service = SkillForecastingService()
        
        forecast = service.forecast_skill_demand(months=6)
        
        assert isinstance(forecast, dict) or isinstance(forecast, list)


class TestTeamSimilarityService:
    """Test Team Similarity Service."""
    
    def test_calculate_similarity_matrix(self, db_session, sample_employees):
        """Test similarity matrix calculation."""
        service = TeamSimilarityService()
        
        employee_ids = [emp.employee_id for emp in sample_employees[:5]]
        matrix = service.calculate_similarity_matrix(employee_ids)
        
        assert isinstance(matrix, dict) or isinstance(matrix, list)


class TestMentorRecommendationService:
    """Test Mentor Recommendation Service."""
    
    def test_find_mentors(self, db_session, sample_employees):
        """Test mentor finding."""
        service = MentorRecommendationService()
        
        mentee_id = sample_employees[0].employee_id
        mentors = service.find_mentors(mentee_id, top_n=5)
        
        assert isinstance(mentors, list)


class TestScenarioSimulationService:
    """Test Scenario Simulation Service."""
    
    def test_simulate_scenario(self, db_session, sample_employees):
        """Test scenario simulation."""
        service = ScenarioSimulationService()
        
        scenario = {
            "scenario_type": "employee_loss",
            "employee_ids": [sample_employees[0].employee_id],
            "parameters": {}
        }
        
        result = service.simulate_scenario(scenario)
        
        assert isinstance(result, dict)


class TestAIModuleIntegration:
    """Integration tests for AI modules."""
    
    def test_ai_pipeline_end_to_end(self, db_session, sample_employees, mock_llm_client):
        """Test complete AI pipeline."""
        # 1. Skill Analysis
        ai_service = SkillAIService()
        ai_service.llm_client = mock_llm_client
        
        employee = sample_employees[0]
        employee_data = {
            "employee_id": employee.employee_id,
            "department": employee.department,
            "skills": employee.skills or []
        }
        
        analysis = ai_service.analyze_employee(
            employee.employee_id,
            employee_data,
            None
        )
        assert "current_skills" in analysis
        
        # 2. Recommendations
        rec_service = SkillRecommendationsService()
        recommendations = rec_service.recommend_skills(
            employee.employee_id,
            employee.skills or [],
            employee.department
        )
        assert isinstance(recommendations, list)
        
        # 3. Role Fit
        role_fit_service = RoleFitService()
        role_requirements = {"required_skills": ["Python", "SQL"]}
        fit = role_fit_service.calculate_role_fit(
            employee.employee_id,
            employee.skills or [],
            role_requirements
        )
        assert fit is not None

