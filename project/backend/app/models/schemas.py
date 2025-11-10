"""
Pydantic schemas for request/response models
Matches database schema definitions
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
from decimal import Decimal
from uuid import UUID
import re


# User Models
class UserBase(BaseModel):
    """Base user model"""
    email: str = Field(..., max_length=255, description="User email address")
    oauth_provider: str = Field(..., max_length=50, description="OAuth provider (e.g., google, linkedin)")
    oauth_id: str = Field(..., max_length=255, description="OAuth provider user ID")


class UserCreate(UserBase):
    """User creation model"""
    pass


class UserRegister(BaseModel):
    """User registration model for traditional signup"""
    email: EmailStr = Field(..., max_length=255, description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        errors = []
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', v):
            errors.append('at least one uppercase letter')
        
        # Check for number
        if not re.search(r'[0-9]', v):
            errors.append('at least one number')
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\/_\-+=~`]', v):
            errors.append('at least one special character')
        
        if errors:
            raise ValueError(f'Password must contain: {", ".join(errors)}')
        
        return v


class UserLogin(BaseModel):
    """User login model for traditional authentication"""
    email: EmailStr = Field(..., max_length=255, description="User email address")
    password: str = Field(..., description="User password")


class OAuthLogin(BaseModel):
    """OAuth login model"""
    provider: str = Field(..., description="OAuth provider (google, linkedin)")
    access_token: str = Field(..., description="OAuth access token from provider")
    oauth_id: Optional[str] = Field(None, description="OAuth provider user ID")


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class User(UserBase):
    """User model matching database schema"""
    user_id: UUID = Field(..., description="Unique user identifier")
    credits: int = Field(default=50, description="Current credit balance")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Account creation timestamp")
    is_active: bool = Field(default=True, description="Account status")
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response model for API"""
    user_id: UUID
    email: str
    oauth_provider: str
    credits: int
    is_active: bool
    created_at: datetime


# Credit Transaction Models
class CreditTransactionBase(BaseModel):
    """Base credit transaction model"""
    user_id: UUID = Field(..., description="User reference")
    transaction_type: str = Field(..., max_length=50, description="Type: purchase, deduction, refund")
    amount: int = Field(..., description="Credit amount (positive/negative)")
    stripe_payment_id: Optional[str] = Field(None, max_length=255, description="Stripe payment intent ID")


class CreditTransactionCreate(CreditTransactionBase):
    """Credit transaction creation model"""
    pass


class CreditTransaction(CreditTransactionBase):
    """Credit transaction model matching database schema"""
    transaction_id: UUID = Field(..., description="Unique transaction identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Transaction timestamp")
    
    class Config:
        from_attributes = True


class CreditTransactionResponse(BaseModel):
    """Credit transaction response model"""
    transaction_id: UUID
    user_id: UUID
    transaction_type: str
    amount: int
    stripe_payment_id: Optional[str]
    created_at: datetime


# Job Models
class JobBase(BaseModel):
    """Base job model"""
    title: str = Field(..., max_length=500, description="Job title")
    company: str = Field(..., max_length=255, description="Company name")
    location: Optional[str] = Field(None, max_length=255, description="Job location")
    source: str = Field(..., max_length=100, description="Source (e.g., linkedin, indeed, manual)")
    source_url: Optional[str] = Field(None, description="Original job posting URL")
    posted_date: Optional[date] = Field(None, description="Job posting date")


class JobCreate(JobBase):
    """Job creation model"""
    pass


class Job(JobBase):
    """Job model matching database schema"""
    job_id: UUID = Field(..., description="Unique job identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Record creation timestamp")
    
    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    """Job response model for API"""
    job_id: UUID
    title: str
    company: str
    location: Optional[str]
    source: str
    source_url: Optional[str]
    posted_date: Optional[date]
    created_at: datetime


# Job Analysis Models
class JobAnalysisBase(BaseModel):
    """Base job analysis model"""
    user_id: UUID = Field(..., description="User who requested analysis")
    job_id: UUID = Field(..., description="Job being analyzed")
    fraud_score: Optional[Decimal] = Field(None, ge=0, le=100, description="Fraud probability score (0-100)")
    analysis_type: str = Field(..., max_length=50, description="Type: ml_model, api_based")
    credits_used: int = Field(default=2, description="Credits consumed")
    
    @field_validator('fraud_score')
    @classmethod
    def validate_fraud_score(cls, v):
        """Validate fraud score is between 0 and 100"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('fraud_score must be between 0 and 100')
        return v


class JobAnalysisCreate(JobAnalysisBase):
    """Job analysis creation model"""
    pass


class JobAnalysis(JobAnalysisBase):
    """Job analysis model matching database schema"""
    analysis_id: UUID = Field(..., description="Unique analysis identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Analysis timestamp")
    
    class Config:
        from_attributes = True


class JobAnalysisResponse(BaseModel):
    """Job analysis response model"""
    analysis_id: UUID
    user_id: UUID
    job_id: UUID
    fraud_score: Optional[Decimal]
    analysis_type: str
    credits_used: int
    created_at: datetime


# Job Match Models
class JobMatchBase(BaseModel):
    """Base job match model"""
    user_id: UUID = Field(..., description="User who requested match")
    job_id: UUID = Field(..., description="Job being matched")
    resume_id: UUID = Field(..., description="Resume version used")
    match_score: Optional[Decimal] = Field(None, ge=0, le=100, description="Overall match score (0-100)")
    skill_score: Optional[Decimal] = Field(None, description="Skill alignment score")
    experience_score: Optional[Decimal] = Field(None, description="Experience match score")
    matching_strategy: str = Field(..., max_length=50, description="Algorithm used")
    credits_used: int = Field(default=3, description="Credits consumed")
    
    @field_validator('match_score')
    @classmethod
    def validate_match_score(cls, v):
        """Validate match score is between 0 and 100"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError('match_score must be between 0 and 100')
        return v


class JobMatchCreate(JobMatchBase):
    """Job match creation model"""
    pass


class JobMatch(JobMatchBase):
    """Job match model matching database schema"""
    match_id: UUID = Field(..., description="Unique match identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Match timestamp")
    
    class Config:
        from_attributes = True


class JobMatchResponse(BaseModel):
    """Job match response model"""
    match_id: UUID
    user_id: UUID
    job_id: UUID
    resume_id: UUID
    match_score: Optional[Decimal]
    skill_score: Optional[Decimal]
    experience_score: Optional[Decimal]
    matching_strategy: str
    credits_used: int
    created_at: datetime


# Job Bookmark Models (inferred schema)
class JobBookmarkBase(BaseModel):
    """Base job bookmark model"""
    user_id: UUID = Field(..., description="User who bookmarked the job")
    job_id: UUID = Field(..., description="Bookmarked job")


class JobBookmarkCreate(JobBookmarkBase):
    """Job bookmark creation model"""
    pass


class JobBookmark(JobBookmarkBase):
    """Job bookmark model"""
    bookmark_id: UUID = Field(..., description="Unique bookmark identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Bookmark timestamp")
    
    class Config:
        from_attributes = True


class JobBookmarkResponse(BaseModel):
    """Job bookmark response model"""
    bookmark_id: UUID
    user_id: UUID
    job_id: UUID
    created_at: datetime


# Log Models
class LogBase(BaseModel):
    """Base log model"""
    level: str = Field(..., max_length=20, description="Log level (e.g., INFO, WARNING, ERROR, DEBUG)")
    message: str = Field(..., description="The log message content")
    user_id: Optional[UUID] = Field(None, description="Optional user reference for user-specific actions")
    action: Optional[str] = Field(None, max_length=100, description="Action type (e.g., job_analysis, credit_purchase, login)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional structured log data")


class LogCreate(LogBase):
    """Log creation model"""
    pass


class Log(LogBase):
    """Log model matching database schema"""
    log_id: int = Field(..., description="Auto-incrementing log entry ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the log entry was created")
    
    class Config:
        from_attributes = True


class LogResponse(BaseModel):
    """Log response model"""
    log_id: int
    timestamp: datetime
    level: str
    message: str
    user_id: Optional[UUID]
    action: Optional[str]
    details: Optional[Dict[str, Any]]


# Request/Response Models for API Endpoints
class JobAnalysisRequest(BaseModel):
    """Request for job analysis"""
    job_id: UUID = Field(..., description="Job ID to analyze")
    analysis_type: str = Field(default="api_based", max_length=50, description="Type: ml_model, api_based")


# Internal models for Chain of Responsibility pattern
class JobAnalysisRequestInternal(BaseModel):
    """Internal request model for Chain of Responsibility handlers"""
    job_title: str
    company_name: str
    job_description: str
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    requirements: Optional[str] = None


class JobAnalysisResult(BaseModel):
    """Result model for Chain of Responsibility pattern"""
    fraud_score: Optional[float] = None
    match_score: Optional[float] = None
    is_fraudulent: bool = False
    fraud_indicators: List[str] = []
    scoring_factors: List[str] = []
    suggestions: List[str] = []
    errors: List[str] = []


class JobMatchRequest(BaseModel):
    """Request for job matching"""
    job_id: UUID = Field(..., description="Job ID to match")
    resume_id: UUID = Field(..., description="Resume ID to use for matching")
    matching_strategy: str = Field(default="balanced", max_length=50, description="Matching strategy: salary, location, skills, balanced")


class PaymentIntentCreate(BaseModel):
    """Create payment intent"""
    user_id: UUID = Field(..., description="User ID")
    amount: int = Field(..., gt=0, description="Amount in cents (must be greater than 0)")
    credits: int = Field(..., gt=0, description="Number of credits to purchase (must be greater than 0)")


class PaymentIntentResponse(BaseModel):
    """Payment intent response"""
    client_secret: str
    payment_intent_id: str
    amount: int
    credits: int


class PaymentWebhook(BaseModel):
    """Stripe webhook payload"""
    type: str
    data: Dict[str, Any]


class UserPreferences(BaseModel):
    """User preferences for job matching"""
    min_salary: Optional[int] = None
    preferred_locations: List[str] = []
    skills: List[str] = []
    job_types: List[str] = []


# API Response Models
class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    status_code: int
    error_message: str
    error_type: str
