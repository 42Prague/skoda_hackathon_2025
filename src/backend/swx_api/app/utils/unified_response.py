"""
Unified Response Helpers
-------------------------
Provides unified success and error response helpers following SWX-API conventions.
"""

from typing import Any, Dict, Optional

from fastapi.responses import JSONResponse


def unified_success(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200
) -> JSONResponse:
    """
    Create a unified success response.
    
    Args:
        data: Response data
        message: Optional success message
        status_code: HTTP status code (default: 200)
        
    Returns:
        JSONResponse with unified success format
    """
    response: Dict[str, Any] = {
        "success": True,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return JSONResponse(status_code=status_code, content=response)


def unified_error(
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> JSONResponse:
    """
    Create a unified error response.
    
    Args:
        error_type: Type of error (e.g., "ValidationError", "NotFound", "InternalError")
        message: Error message
        details: Optional error details
        status_code: HTTP status code (default: 500)
        
    Returns:
        JSONResponse with unified error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "detail": message,
            "details": details or {},
        }
    )

