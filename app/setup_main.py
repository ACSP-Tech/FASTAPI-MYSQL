from fastapi.middleware.cors import CORSMiddleware

def configure_cors(app):
    """Configure CORS middleware for the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Dict, Any, List

async def custom_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom handler to convert the complex RequestValidationError 
    into a simple, desired 400 Bad Request structure.

    Desired Output Format:
    {
      "error": "Validation failed",
      "details": {
        "currency_code": "is required"
      }
    }
    """
    
    # Structure to hold the simplified errors
    error_details: Dict[str, Any] = {}

    for error in exc.errors():
        # The 'loc' field is a tuple pointing to the error location, 
        # usually (body, field_name). We grab the field_name (index 1).
        field = error['loc'][1] if len(error['loc']) > 1 else 'request_body'
        
        # Determine the simple error message based on the error type
        if error['type'] == 'missing':
            message = "is required"
        elif error['type'] == 'value_error':
            # Example: population field validation (gt=0)
            message = f"is invalid: {error['msg']}"
        else:
            message = error['msg']
            
        error_details[field] = message

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation failed",
            "details": error_details
        }
    )

def register_exception_handlers(app: FastAPI):
    """Register all custom exception handlers"""
    app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
