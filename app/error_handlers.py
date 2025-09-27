"""
Professional error handling for Recipe API.
Provides consistent error responses with proper HTTP status codes.
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error with consistent structure"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "api_error",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError400(APIError):
    """400 Bad Request - Client sent invalid data"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, "validation_error", details)


class NotFoundError404(APIError):
    """404 Not Found - Resource doesn't exist"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, "not_found", details)


class UnprocessableEntity422(APIError):
    """422 Unprocessable Entity - Valid format but business logic errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 422, "unprocessable_entity", details)


def create_error_response(
    message: str,
    status_code: int,
    error_code: str = "error",
    details: Optional[Dict[str, Any]] = None,
    validation_errors: Optional[List[Dict[str, Any]]] = None
) -> JSONResponse:
    """Create standardized error response"""
    
    error_data = {
        "error": True,
        "message": message,
        "error_code": error_code,
        "status_code": status_code
    }
    
    if details:
        error_data["details"] = details
        
    if validation_errors:
        error_data["validation_errors"] = validation_errors
        error_data["validation_error_count"] = len(validation_errors)
    
    # Log error for debugging
    logger.error(f"API Error {status_code}: {message}", extra={"details": details})
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


def create_validation_error_response(validation_result) -> JSONResponse:
    """Create 422 error response from validation result"""
    return create_error_response(
        message="Validation failed - please check your data and try again",
        status_code=422,
        error_code="validation_failed",
        details={
            "error_count": len(validation_result.errors),
            "validation_summary": "Multiple validation errors found"
        },
        validation_errors=validation_result.errors
    )


def create_not_found_error_response(resource_type: str = "Resource", resource_id: str = None) -> JSONResponse:
    """Create 404 error response for missing resources"""
    message = f"{resource_type} not found"
    details = {}
    
    if resource_id:
        message += f" with ID '{resource_id}'"
        details["requested_id"] = resource_id
        details["resource_type"] = resource_type.lower()
    
    return create_error_response(
        message=message,
        status_code=404,
        error_code="not_found",
        details=details
    )


def create_bad_request_error_response(message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Create 400 error response for bad requests"""
    return create_error_response(
        message=message,
        status_code=400,
        error_code="bad_request",
        details=details
    )


def create_server_error_response(message: str = "Internal server error") -> JSONResponse:
    """Create 500 error response for server errors"""
    return create_error_response(
        message=message,
        status_code=500,
        error_code="internal_server_error",
        details={"suggestion": "Please try again later or contact support"}
    )


def handle_pydantic_validation_error(error: ValidationError) -> JSONResponse:
    """Convert Pydantic validation error to standardized response"""
    validation_errors = []
    
    for err in error.errors():
        field = ".".join(str(loc) for loc in err.get('loc', []))
        validation_errors.append({
            "field": field,
            "message": err.get('msg', 'Invalid value'),
            "code": err.get('type', 'validation_error'),
            "input_value": err.get('input')
        })
    
    return create_error_response(
        message="Request data validation failed",
        status_code=422,
        error_code="pydantic_validation_error",
        validation_errors=validation_errors
    )


def create_success_response(
    data: Any,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    
    if meta:
        response["meta"] = meta
    
    return response


def create_file_error_response(message: str, file_info: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Create error response for file operations"""
    details = {}
    if file_info:
        details.update(file_info)
    
    return create_error_response(
        message=message,
        status_code=400,
        error_code="file_error", 
        details=details
    )


# HTTP Status Code Constants for consistency
class StatusCodes:
    """HTTP Status codes used in the API"""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
