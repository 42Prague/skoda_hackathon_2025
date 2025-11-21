"""
Ontology Schemas
----------------
Pydantic schemas for skill ontology responses.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict


class OntologyResponse(BaseModel):
    """Response schema for skill ontology."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skills": ["Battery Systems", "Autonomous Software"],
                "clusters": [],
                "normalized_mapping": {"battery": "Battery Systems"},
                "department_skill_map": {"Powertrain Engineering": ["Battery Systems"]},
            }
        }
    )

    skills: List[str]
    clusters: List[Dict[str, Any]]
    normalized_mapping: Dict[str, str]
    department_skill_map: Dict[str, List[str]]

