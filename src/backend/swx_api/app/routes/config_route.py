"""
Skill Coach Config Route
------------------------
API endpoint for UI contract (metadata for frontend).
"""

import logging
import os

from fastapi import APIRouter

from swx_api.app.services.tone_service import get_tone_service
from swx_api.app.utils.unified_response import unified_success, unified_error

logger = logging.getLogger("config_route")

router = APIRouter(prefix="/api/config")


@router.get("/ui-contract")
async def get_ui_contract():
    """Get UI contract (metadata for frontend) with TONE capabilities."""
    tone_service = get_tone_service()
    
    try:
        contract = {
            "version": "2.1.0",
            "endpoints": {
                "ingestion": "/api/ingestion/ingest",
                "ontology": "/api/skills/ontology",
                "analysis": "/api/skills/analysis",
                "recommendations": "/api/skills/recommendations",
                "analytics": {
                    "employees": "/api/analytics/employees/{employee_id}",
                    "departments": "/api/analytics/departments/{department_name}",
                    "global": "/api/analytics/global",
                    "forecast": {
                        "path": "/api/analytics/forecast",
                        "method": "GET",
                        "params": {"months": "int (3, 6, or 12)"},
                        "description": "AI-powered skill demand forecasting 3-12 months ahead"
                    },
                    "team_similarity": {
                        "path": "/api/analytics/team-similarity",
                        "method": "GET",
                        "description": "Cross-team skill similarity analysis"
                    },
                    "simulate": {
                        "path": "/api/analytics/simulate",
                        "method": "POST",
                        "body": {
                            "scenario_type": "string ('employee_loss', 'training_completion', 'skill_mandatory')",
                            "scenario_params": "object"
                        },
                        "description": "What-if scenario simulation engine"
                    }
                },
                "skills": {
                    "taxonomy": {
                        "path": "/api/skills/taxonomy",
                        "method": "GET",
                        "description": "Automated skill taxonomy builder (AI-powered classification)"
                    },
                    "role_fit": {
                        "path": "/api/skills/role-fit",
                        "method": "POST",
                        "body": {
                            "employee_id": "string",
                            "role_definition": "object (mandatory_skills, preferred_skills)",
                            "skill_importance": "object (optional)"
                        },
                        "description": "Team/Role fit matching engine"
                    }
                },
                "recommendations": {
                    "mentor": {
                        "path": "/api/recommendations/mentor/{employee_id}",
                        "method": "GET",
                        "params": {"max_recommendations": "int (1-50)"},
                        "description": "Employee-to-employee mentor finder"
                    }
                },
                "employees": {
                    "learning_history": {
                        "create": {
                            "path": "/api/employees/{employee_id}/learning-history",
                            "method": "POST",
                            "body": {
                                "course_name": "string",
                                "provider": "string (optional)",
                                "start_date": "datetime (optional)",
                                "end_date": "datetime (optional)",
                                "hours": "float (optional)",
                                "completion_status": "string",
                                "skills_covered": "array (optional)",
                                "certificate_url": "string (optional)"
                            },
                            "description": "Create learning history record"
                        },
                        "get": {
                            "path": "/api/employees/{employee_id}/learning-history",
                            "method": "GET",
                            "description": "Get learning history for employee"
                        }
                    }
                },
                "ingestion": {
                    "data_repair": {
                        "path": "/api/ingestion/data-repair",
                        "method": "POST",
                        "body": {
                            "dataset_id": "string",
                            "dataset_name": "string"
                        },
                        "description": "AI-powered data repair suggestions and normalization"
                    }
                },
                "dashboard": {
                    "overview": "/api/dashboard/overview",
                    "skill_map": "/api/dashboard/skill-map",
                    "heatmap": "/api/dashboard/heatmap",
                    "trends": "/api/dashboard/trends",
                },
            },
            "supported_file_types": ["csv", "xlsx", "xls", "json", "txt", "docx"],
            "response_format": {
                "success": "boolean",
                "data": "object",
                "message": "string (optional)",
                "error": {
                    "type": "string",
                    "message": "string",
                    "details": "object",
                },
            },
            "tone_format": {
                "enabled": tone_service.use_tone,
                "validation_mode": tone_service.validation_mode,
                "prompt_format": "TONE (Token-Optimized Notation Engine) - compact, human-readable format",
                "api_output": "JSON (unchanged - frontend compatibility maintained)",
                "example": {
                    "tone_prompt": "items[2]{id,name}:\n  1,Item1\n  2,Item2",
                    "json_response": {
                        "items": [{"id": 1, "name": "Item1"}, {"id": 2, "name": "Item2"}]
                    }
                },
                "local_model_support": {
                    "enabled": True,
                    "provider": "Ollama",
                    "endpoint": os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/v1"),
                    "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
                    "description": "Automatic fallback to local Ollama model if external APIs fail"
                }
            }
        }
        
        return unified_success(
            data=contract,
            message="UI contract retrieved successfully"
        )
    except Exception as exc:
        logger.error(f"Error getting UI contract: {exc}", exc_info=True)
        return unified_error(
            error_type="InternalError",
            message=f"Failed to get UI contract: {str(exc)}",
            status_code=500
        )

