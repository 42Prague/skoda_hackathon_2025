"""
Data Validation Functions
Input validation for API endpoints
"""

from typing import Dict, List, Optional, Any

def validate_employee_data(data: Dict[str, Any]) -> Optional[str]:
    """
    Validate employee data for creation/update
    
    Args:
        data: Dictionary containing employee data
        
    Returns:
        Error message if validation fails, None if valid
    """
    errors = []
    
    # Required fields
    required_fields = ['name', 'position', 'skills']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Field '{field}' is required")
    
    # Validate name
    if 'name' in data:
        if not isinstance(data['name'], str) or len(data['name'].strip()) < 2:
            errors.append("Name must be a string with at least 2 characters")
        elif len(data['name']) > 100:
            errors.append("Name cannot exceed 100 characters")
    
    # Validate position
    if 'position' in data:
        if not isinstance(data['position'], str) or len(data['position'].strip()) < 2:
            errors.append("Position must be a string with at least 2 characters")
        elif len(data['position']) > 100:
            errors.append("Position cannot exceed 100 characters")
    
    # Validate skills
    if 'skills' in data:
        if not isinstance(data['skills'], list):
            errors.append("Skills must be a list")
        elif len(data['skills']) == 0:
            errors.append("At least one skill is required")
        else:
            for i, skill in enumerate(data['skills']):
                if not isinstance(skill, str) or len(skill.strip()) < 1:
                    errors.append(f"Skill at index {i} must be a non-empty string")
                elif len(skill) > 50:
                    errors.append(f"Skill at index {i} cannot exceed 50 characters")
    
    # Validate experience_years (optional)
    if 'experience_years' in data:
        if not isinstance(data['experience_years'], (int, float)):
            errors.append("Experience years must be a number")
        elif data['experience_years'] < 0 or data['experience_years'] > 50:
            errors.append("Experience years must be between 0 and 50")
    
    # Validate department (optional)
    if 'department' in data and data['department']:
        if not isinstance(data['department'], str) or len(data['department'].strip()) < 1:
            errors.append("Department must be a non-empty string")
        elif len(data['department']) > 100:
            errors.append("Department cannot exceed 100 characters")
    
    return "; ".join(errors) if errors else None

def validate_skill_list(skills: List[str]) -> Optional[str]:
    """
    Validate a list of skills
    
    Args:
        skills: List of skill strings
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not isinstance(skills, list):
        return "Skills must be provided as a list"
    
    if len(skills) == 0:
        return "At least one skill must be provided"
    
    errors = []
    for i, skill in enumerate(skills):
        if not isinstance(skill, str):
            errors.append(f"Skill at index {i} must be a string")
        elif len(skill.strip()) < 1:
            errors.append(f"Skill at index {i} cannot be empty")
        elif len(skill) > 50:
            errors.append(f"Skill at index {i} cannot exceed 50 characters")
    
    return "; ".join(errors) if errors else None

def validate_pagination_params(page: Any, per_page: Any) -> Dict[str, Any]:
    """
    Validate and normalize pagination parameters
    
    Args:
        page: Page number (as received from request)
        per_page: Items per page (as received from request)
        
    Returns:
        Dictionary with validated page and per_page values
    """
    # Default values
    default_page = 1
    default_per_page = 10
    max_per_page = 100
    
    # Validate page
    try:
        page = int(page) if page else default_page
        if page < 1:
            page = default_page
    except (ValueError, TypeError):
        page = default_page
    
    # Validate per_page
    try:
        per_page = int(per_page) if per_page else default_per_page
        if per_page < 1:
            per_page = default_per_page
        elif per_page > max_per_page:
            per_page = max_per_page
    except (ValueError, TypeError):
        per_page = default_per_page
    
    return {"page": page, "per_page": per_page}

def validate_employee_ids(employee_ids: List[Any]) -> Optional[str]:
    """
    Validate a list of employee IDs
    
    Args:
        employee_ids: List of employee ID values
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not isinstance(employee_ids, list):
        return "Employee IDs must be provided as a list"
    
    if len(employee_ids) == 0:
        return "At least one employee ID must be provided"
    
    errors = []
    for i, emp_id in enumerate(employee_ids):
        try:
            emp_id_int = int(emp_id)
            if emp_id_int < 1:
                errors.append(f"Employee ID at index {i} must be a positive integer")
        except (ValueError, TypeError):
            errors.append(f"Employee ID at index {i} must be a valid integer")
    
    return "; ".join(errors) if errors else None

def validate_filter_params(department: str = None, position: str = None, 
                          min_experience: Any = None) -> Dict[str, Any]:
    """
    Validate and normalize filter parameters
    
    Args:
        department: Department filter
        position: Position filter
        min_experience: Minimum experience filter
        
    Returns:
        Dictionary with validated filter parameters
    """
    validated = {}
    
    # Validate department
    if department:
        if isinstance(department, str) and len(department.strip()) > 0:
            validated['department'] = department.strip()
    
    # Validate position
    if position:
        if isinstance(position, str) and len(position.strip()) > 0:
            validated['position'] = position.strip()
    
    # Validate min_experience
    if min_experience is not None:
        try:
            min_exp = int(min_experience)
            if 0 <= min_exp <= 50:
                validated['min_experience'] = min_exp
        except (ValueError, TypeError):
            pass  # Invalid value, ignore filter
    
    return validated

def sanitize_string_input(input_str: str, max_length: int = 200) -> str:
    """
    Sanitize string input by trimming and limiting length
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Strip whitespace and limit length
    sanitized = input_str.strip()[:max_length]
    
    # Remove potentially harmful characters (basic sanitization)
    # In production, you might want more sophisticated sanitization
    harmful_chars = ['<', '>', '&', '"', "'"]
    for char in harmful_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized

def validate_skill_analysis_params(data: Dict[str, Any]) -> Optional[str]:
    """
    Validate parameters for skill analysis requests
    
    Args:
        data: Request data dictionary
        
    Returns:
        Error message if validation fails, None if valid
    """
    errors = []
    
    # Validate department if provided
    if 'department' in data and data['department']:
        if not isinstance(data['department'], str) or len(data['department'].strip()) < 1:
            errors.append("Department must be a non-empty string")
    
    # Validate position if provided
    if 'position' in data and data['position']:
        if not isinstance(data['position'], str) or len(data['position'].strip()) < 1:
            errors.append("Position must be a non-empty string")
    
    # Validate team size for team recommendations
    if 'team_size' in data:
        try:
            team_size = int(data['team_size'])
            if team_size < 1 or team_size > 20:
                errors.append("Team size must be between 1 and 20")
        except (ValueError, TypeError):
            errors.append("Team size must be a valid integer")
    
    # Validate required skills list
    if 'required_skills' in data:
        if not isinstance(data['required_skills'], list):
            errors.append("Required skills must be provided as a list")
    
    return "; ".join(errors) if errors else None
