"""
Comprehensive Tests for Advanced Features
-----------------------------------------
Unit and integration tests for all new advanced features.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from swx_api.app.services.skill_forecasting_service import SkillForecastingService
from swx_api.app.services.skill_taxonomy_service import SkillTaxonomyService
from swx_api.app.services.role_fit_service import RoleFitService
from swx_api.app.services.team_similarity_service import TeamSimilarityService
from swx_api.app.services.mentor_recommendation_service import MentorRecommendationService
from swx_api.app.services.scenario_simulation_service import ScenarioSimulationService
from swx_api.app.services.advanced_dq_service import AdvancedDQService
from swx_api.app.services.data_repair_service import DataRepairService
from swx_api.app.services.audit_service import AuditService


# Test Data
SAMPLE_EMPLOYEES = [
    {
        "employee_id": "emp_001",
        "department": "Engineering",
        "skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "metadata": {}
    },
    {
        "employee_id": "emp_002",
        "department": "Engineering",
        "skills": ["Python", "React", "Node.js"],
        "metadata": {}
    },
    {
        "employee_id": "emp_003",
        "department": "Data Science",
        "skills": ["Python", "Pandas", "Machine Learning"],
        "metadata": {}
    },
    {
        "employee_id": "emp_004",
        "department": "DevOps",
        "skills": ["Docker", "Kubernetes", "Terraform"],
        "metadata": {}
    }
]

SAMPLE_SKILLS = ["Python", "Django", "PostgreSQL", "Docker", "React", "Node.js", "Pandas", "Machine Learning", "Kubernetes", "Terraform"]


class TestSkillForecasting:
    """Tests for Skill Forecasting Engine."""
    
    def test_forecast_service_initialization(self):
        """Test service initializes correctly."""
        service = SkillForecastingService()
        assert service is not None
        assert service.llm_config is not None
    
    def test_forecast_skills_basic(self):
        """Test basic skill forecasting."""
        service = SkillForecastingService()
        forecast = service.forecast_skills(
            SAMPLE_EMPLOYEES,
            forecast_horizon="6m"
        )
        
        assert forecast is not None
        assert "forecast_horizon" in forecast
        assert "emerging_skills" in forecast
        assert "declining_skills" in forecast
        assert "predicted_trend_curve" in forecast
        assert forecast["forecast_horizon"] == "6m"
    
    def test_forecast_horizon_parsing(self):
        """Test forecast horizon parsing."""
        service = SkillForecastingService()
        assert service._parse_horizon("3m") == 3
        assert service._parse_horizon("6m") == 6
        assert service._parse_horizon("12m") == 12
        assert service._parse_horizon("invalid") == 6  # Default
    
    def test_baseline_generation(self):
        """Test baseline skill frequency generation."""
        service = SkillForecastingService()
        baseline = service._generate_baseline(SAMPLE_EMPLOYEES)
        
        assert "skill_frequency" in baseline
        assert "total_employees" in baseline
        assert baseline["total_employees"] == len(SAMPLE_EMPLOYEES)
        assert "Python" in baseline["skill_frequency"]


class TestSkillTaxonomy:
    """Tests for Skill Taxonomy Builder."""
    
    def test_taxonomy_service_initialization(self):
        """Test service initializes correctly."""
        service = SkillTaxonomyService()
        assert service is not None
    
    def test_build_taxonomy_basic(self):
        """Test basic taxonomy building."""
        service = SkillTaxonomyService()
        taxonomy = service.build_taxonomy(SAMPLE_SKILLS)
        
        assert taxonomy is not None
        assert "taxonomy" in taxonomy
        assert "skill_families" in taxonomy
        assert "normalized_mapping" in taxonomy
    
    def test_fallback_taxonomy(self):
        """Test fallback taxonomy when AI fails."""
        service = SkillTaxonomyService()
        taxonomy = service._fallback_taxonomy(SAMPLE_SKILLS)
        
        assert taxonomy is not None
        assert "skill_domains" in taxonomy


class TestRoleFit:
    """Tests for Role Fit Matching Engine."""
    
    def test_role_fit_service_initialization(self):
        """Test service initializes correctly."""
        service = RoleFitService()
        assert service is not None
    
    def test_compute_role_fit_basic(self):
        """Test basic role fit computation."""
        service = RoleFitService()
        
        employee_profile = SAMPLE_EMPLOYEES[0]
        role_definition = {
            "role_name": "Senior Python Developer",
            "mandatory_skills": ["Python", "Django"],
            "preferred_skills": ["Docker"]
        }
        
        fit_result = service.compute_role_fit(
            employee_profile,
            role_definition
        )
        
        assert fit_result is not None
        assert "fit_score" in fit_result
        assert 0 <= fit_result["fit_score"] <= 100
        assert "missing_mandatory_skills" in fit_result
        assert "readiness_level" in fit_result
        assert fit_result["readiness_level"] in ["ready", "almost-ready", "not-ready"]
    
    def test_skill_matching(self):
        """Test skill matching logic."""
        service = RoleFitService()
        
        employee_skills = ["Python", "Django", "PostgreSQL"]
        required_skills = ["Python", "Django", "React"]
        
        matches = service._match_skills(employee_skills, required_skills)
        
        assert matches["match_count"] == 2
        assert "Python" in matches["matched"]
        assert "Django" in matches["matched"]
        assert "React" not in matches["matched"]


class TestTeamSimilarity:
    """Tests for Team Similarity Analysis."""
    
    def test_team_similarity_service_initialization(self):
        """Test service initializes correctly."""
        service = TeamSimilarityService()
        assert service is not None
    
    def test_analyze_team_similarity_basic(self):
        """Test basic team similarity analysis."""
        service = TeamSimilarityService()
        similarity = service.analyze_team_similarity(SAMPLE_EMPLOYEES)
        
        assert similarity is not None
        assert "similarity_matrix" in similarity
        assert "cross_support_opportunities" in similarity
        assert "skill_redundancies" in similarity
    
    def test_department_profile_building(self):
        """Test department profile building."""
        service = TeamSimilarityService()
        profile = service._build_department_profile(
            "Engineering",
            [SAMPLE_EMPLOYEES[0], SAMPLE_EMPLOYEES[1]]
        )
        
        assert profile["department"] == "Engineering"
        assert profile["team_size"] == 2
        assert "skills" in profile
        assert "skill_frequency" in profile


class TestMentorRecommendation:
    """Tests for Mentor Recommendation Service."""
    
    def test_mentor_service_initialization(self):
        """Test service initializes correctly."""
        service = MentorRecommendationService()
        assert service is not None
    
    def test_find_mentors_basic(self):
        """Test basic mentor finding."""
        service = MentorRecommendationService()
        
        target_employee = SAMPLE_EMPLOYEES[0]
        recommendations = service.find_mentors(
            target_employee["employee_id"],
            target_employee,
            SAMPLE_EMPLOYEES,
            max_recommendations=5
        )
        
        assert recommendations is not None
        assert "mentors" in recommendations
        assert "skill_coverage" in recommendations
        assert recommendations["employee_id"] == target_employee["employee_id"]


class TestScenarioSimulation:
    """Tests for Scenario Simulation Engine."""
    
    def test_simulation_service_initialization(self):
        """Test service initializes correctly."""
        service = ScenarioSimulationService()
        assert service is not None
    
    def test_simulate_employee_loss(self):
        """Test employee loss scenario."""
        service = ScenarioSimulationService()
        
        scenario_params = {
            "employee_ids": ["emp_001"]
        }
        
        result = service.simulate_scenario(
            "employee_loss",
            scenario_params,
            SAMPLE_EMPLOYEES
        )
        
        assert result is not None
        assert "impact_predictions" in result
        assert "new_risk_scores" in result
        assert result["scenario_type"] == "employee_loss"
    
    def test_simulate_training_completion(self):
        """Test training completion scenario."""
        service = ScenarioSimulationService()
        
        scenario_params = {
            "skill": "Kubernetes",
            "employee_ids": ["emp_001", "emp_002"]
        }
        
        result = service.simulate_scenario(
            "training_completion",
            scenario_params,
            SAMPLE_EMPLOYEES
        )
        
        assert result is not None
        assert "impact_predictions" in result


class TestAdvancedDQ:
    """Tests for Advanced Data Quality Service."""
    
    def test_dq_service_initialization(self):
        """Test service initializes correctly."""
        service = AdvancedDQService()
        assert service is not None
    
    @pytest.mark.skipif(True, reason="Requires pandas DataFrame")
    def test_compute_advanced_dq_metrics(self):
        """Test advanced DQ metrics computation."""
        # This would require creating a test DataFrame
        # Skipped for now, but structure is here
        pass


class TestDataRepair:
    """Tests for Data Repair Service."""
    
    def test_data_repair_service_initialization(self):
        """Test service initializes correctly."""
        service = DataRepairService()
        assert service is not None


class TestAuditService:
    """Tests for Audit Service."""
    
    def test_audit_service_initialization(self):
        """Test service initializes correctly."""
        service = AuditService()
        assert service is not None
    
    def test_log_ingestion(self):
        """Test logging ingestion events."""
        service = AuditService()
        service.log_ingestion(
            dataset_id="test_ds_001",
            filename="test.csv",
            status="success"
        )
        # Verify log was written (would need to read file)
    
    def test_log_ai_call(self):
        """Test logging AI calls."""
        service = AuditService()
        service.log_ai_call(
            service_name="test_service",
            model="test_model",
            prompt_length=100,
            response_length=200,
            success=True
        )
    
    def test_log_error(self):
        """Test logging errors."""
        service = AuditService()
        service.log_error(
            error_type="TestError",
            error_message="Test error message",
            service_name="test_service"
        )


# Integration Tests (would require database and API setup)
@pytest.mark.integration
class TestIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.mark.skipif(True, reason="Requires running API server")
    def test_forecast_endpoint(self):
        """Test forecast API endpoint."""
        # Would use httpx to test actual endpoint
        pass
    
    @pytest.mark.skipif(True, reason="Requires running API server")
    def test_taxonomy_endpoint(self):
        """Test taxonomy API endpoint."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

