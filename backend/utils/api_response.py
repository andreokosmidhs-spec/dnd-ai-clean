"""
API Response Normalization Utility

Standardizes all API responses across the backend to have a consistent shape:
- Success: {success: true, data: <payload>, error: null}
- Error: {success: false, data: null, error: {type, message, details}}
"""

from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse


def api_success(data: Any = None, status_code: int = 200) -> JSONResponse:
    """
    Create a standardized success response
    
    Args:
        data: The payload to return (can be any JSON-serializable value)
        status_code: HTTP status code (default: 200)
    
    Returns:
        JSONResponse with standardized success shape
    
    Example:
        return api_success({"id": "123", "name": "Campaign"})
        # => {success: true, data: {id: "123", name: "Campaign"}, error: null}
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "error": None
        }
    )


def api_error(
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        error_type: Short error code (e.g., "validation_error", "not_found")
        message: Human-readable error message
        details: Optional structured error details (e.g., field errors)
        status_code: HTTP status code (default: 400)
    
    Returns:
        JSONResponse with standardized error shape
    
    Example:
        return api_error(
            error_type="validation_error",
            message="Campaign title is required",
            details={"field": "title"},
            status_code=422
        )
        # => {success: false, data: null, error: {type: "validation_error", ...}}
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {}
            }
        }
    )


# Common error type constants
class ErrorType:
    """Standard error type codes"""
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    INTERNAL_ERROR = "internal_error"
    BAD_REQUEST = "bad_request"
    SERVICE_ERROR = "service_error"
    DATABASE_ERROR = "database_error"


# Convenience functions for common errors
def validation_error(message: str, details: Optional[Dict] = None) -> JSONResponse:
    """Return 422 validation error"""
    return api_error(ErrorType.VALIDATION_ERROR, message, details, 422)


def not_found_error(message: str = "Resource not found") -> JSONResponse:
    """Return 404 not found error"""
    return api_error(ErrorType.NOT_FOUND, message, status_code=404)


def internal_error(message: str = "Internal server error") -> JSONResponse:
    """Return 500 internal error"""
    return api_error(ErrorType.INTERNAL_ERROR, message, status_code=500)


def unauthorized_error(message: str = "Unauthorized") -> JSONResponse:
    """Return 401 unauthorized error"""
    return api_error(ErrorType.UNAUTHORIZED, message, status_code=401)
