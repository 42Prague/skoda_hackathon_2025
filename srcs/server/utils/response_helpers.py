"""
Response Helper Functions
Standardized response formatting for API endpoints
"""

from flask import jsonify
from typing import Any, Dict, Optional

def success_response(data: Any = None, message: str = "Success", 
                    status_code: int = 200) -> tuple:
    """
    Create a standardized success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        "success": True,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status_code

def error_response(error: str, status_code: int = 400, 
                  details: Optional[Dict] = None) -> tuple:
    """
    Create a standardized error response
    
    Args:
        error: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (response, status_code)
    """
    response = {
        "success": False,
        "error": error,
        "status_code": status_code
    }
    
    if details:
        response["details"] = details
    
    return jsonify(response), status_code

def paginated_response(data: list, page: int, per_page: int, 
                      total: int, message: str = "Success") -> tuple:
    """
    Create a paginated response
    
    Args:
        data: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Success message
        
    Returns:
        Tuple of (response, status_code)
    """
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    response = {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }
    
    return jsonify(response), 200

def validation_error_response(errors: Dict[str, list]) -> tuple:
    """
    Create a validation error response
    
    Args:
        errors: Dictionary of field errors
        
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        error="Validation failed",
        status_code=422,
        details={"validation_errors": errors}
    )
