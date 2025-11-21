"""
Employee Validators
-------------------
Validation functions for employee-related inputs.
"""

from typing import List

from fastapi import HTTPException


def validate_employee_id(employee_id: str) -> str:
    """Validate employee ID format."""
    if not employee_id or not employee_id.strip():
        raise HTTPException(status_code=400, detail="Employee ID cannot be empty")
    
    if len(employee_id) > 255:
        raise HTTPException(status_code=400, detail="Employee ID must be 255 characters or less")
    
    return employee_id.strip()


def validate_department(department: str) -> str:
    """Validate department name."""
    if not department or not department.strip():
        raise HTTPException(status_code=400, detail="Department cannot be empty")
    
    if len(department) > 255:
        raise HTTPException(status_code=400, detail="Department must be 255 characters or less")
    
    return department.strip()


def validate_skills_list(skills: List[str]) -> List[str]:
    """Validate skills list."""
    if skills is None:
        return []
    
    validated = []
    for skill in skills:
        if skill and skill.strip():
            validated.append(skill.strip())
    
    return validated

