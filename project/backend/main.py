"""
FastAPI Backend Application
Main entry point for the job matching and analysis API
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.routers import jobs, payments, analysis, users
from app.core.config import settings
from app.core.singleton import DatabaseManager, StripeManager, APIConnectionManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup: Initialize singleton managers
    DatabaseManager.get_instance()
    StripeManager.get_instance()
    APIConnectionManager.get_instance()
    yield
    # Shutdown: Cleanup if needed
    pass


app = FastAPI(
    title="Job Matching & Analysis API",
    description="API for job matching, fraud analysis, and payment management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors
    Prioritizes email validation errors and returns simplified format
    """
    errors = exc.errors()
    
    # Prioritize email errors first
    email_error = None
    password_error = None
    other_errors = []
    
    for error in errors:
        field_path = error.get("loc", [])
        if len(field_path) > 1 and field_path[1] == "email":
            email_error = error
        elif len(field_path) > 1 and field_path[1] == "password":
            password_error = error
        else:
            other_errors.append(error)
    
    # Determine which error to return (prioritize email)
    error_to_return = email_error or password_error or (other_errors[0] if other_errors else errors[0])
    
    # Extract error message
    error_msg = error_to_return.get("msg", "Validation error")
    error_type = error_to_return.get("type", "validation_error")
    
    # Format error message for better readability
    field_name = error_to_return.get("loc", ["field"])[-1] if error_to_return.get("loc") else "field"
    
    if field_name == "email":
        # Email validation errors
        if "value is not a valid email address" in error_msg.lower() or "email" in error_msg.lower():
            error_message = "Invalid email format"
            error_type = "email_validation_error"
        else:
            error_message = error_msg
            error_type = "email_validation_error"
    elif field_name == "password":
        # Password validation errors
        if error_type == "value_error":
            error_message = error_msg
            error_type = "password_validation_error"
        else:
            error_message = error_msg
            error_type = "password_validation_error"
    elif error_type == "value_error":
        # Other custom validators
        error_message = error_msg
        error_type = "validation_error"
    else:
        error_message = error_msg
        error_type = "validation_error"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "error_message": error_message,
            "error_type": error_type
        }
    )


# Include routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Job Matching & Analysis API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

