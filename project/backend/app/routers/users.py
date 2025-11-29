"""
Users Router
Handles user account management, authentication, and OAuth
"""

from fastapi import APIRouter, HTTPException, Depends, status
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
import logging
from app.models.schemas import (
    UserRegister,
    UserLogin,
    OAuthLogin,
    UserResponse,
    UserUpdate,
    Token,
    DashboardStatsResponse
)
from app.core.singleton import DatabaseManager
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.dependencies import get_current_user_id
from app.core.config import settings
from app.services.oauth_service import OAuthService
from app.patterns.observer import user_event_subject, EventType

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    """
    Register a new user with traditional email/password authentication
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Check if user already exists
        existing_user = supabase.table("users").select("user_id, email").eq("email", user_data.email).execute()
        
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password and store in a password field (if you add it to schema)
        # For now, we'll use oauth_id to store password hash (not ideal, but works for demo)
        password_hash = get_password_hash(user_data.password)
        user_id = uuid4()
        
        # Create user with traditional auth (using 'traditional' as oauth_provider)
        supabase.table("users").insert({
            "user_id": str(user_id),
            "email": user_data.email,
            "oauth_provider": "traditional",
            "oauth_id": password_hash,  # Store password hash in oauth_id for traditional auth
            "credits": 50,
            "is_active": True
        }).execute()
        
        # Get created user
        user_response = supabase.table("users").select(
            "user_id, email, oauth_provider, credits, is_active, created_at"
        ).eq("user_id", str(user_id)).execute()
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        user = user_response.data[0]
        
        return UserResponse(
            user_id=UUID(user["user_id"]),
            email=user["email"],
            oauth_provider=user["oauth_provider"],
            credits=user["credits"],
            is_active=user["is_active"],
            created_at=datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")) if isinstance(user["created_at"], str) else user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login_user(credentials: UserLogin):
    """
    Authenticate user with email and password
    Returns JWT access token
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Find user by email
        user_response = supabase.table("users").select(
            "user_id, email, oauth_provider, oauth_id, is_active"
        ).eq("email", credentials.email).execute()
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = user_response.data[0]
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Verify password for traditional auth
        if user["oauth_provider"] == "traditional":
            stored_hash = user["oauth_id"]  # Password hash stored in oauth_id
            if not verify_password(credentials.password, stored_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account uses OAuth authentication. Please use OAuth login."
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["user_id"])},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/oauth/login", response_model=Token)
async def oauth_login(oauth_data: OAuthLogin):
    """
    Authenticate user with OAuth provider (Google or LinkedIn)
    Returns JWT access token
    """
    try:
        oauth_service = OAuthService()
        
        # Verify OAuth token and get user info
        user_info = await oauth_service.get_oauth_user_info(
            provider=oauth_data.provider,
            access_token=oauth_data.access_token
        )
        
        if not user_info.get("email") or not user_info.get("oauth_id"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth token or missing user information"
            )
        
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Check if user exists
        user_response = supabase.table("users").select(
            "user_id, email, oauth_provider, oauth_id, is_active"
        ).eq("email", user_info["email"]).eq("oauth_provider", oauth_data.provider.lower()).execute()
        
        user_id = None
        
        if user_response.data:
            # User exists, update oauth_id if needed
            user = user_response.data[0]
            user_id = UUID(user["user_id"])
            
            if not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )
            
            # Update oauth_id if it changed
            if user["oauth_id"] != user_info["oauth_id"]:
                supabase.table("users").update({
                    "oauth_id": user_info["oauth_id"]
                }).eq("user_id", str(user_id)).execute()
        else:
            # Create new user
            user_id = uuid4()
            supabase.table("users").insert({
                "user_id": str(user_id),
                "email": user_info["email"],
                "oauth_provider": oauth_data.provider.lower(),
                "oauth_id": user_info["oauth_id"],
                "credits": 50,
                "is_active": True
            }).execute()
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_id)},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user_id: UUID = Depends(get_current_user_id)):
    """
    Get current authenticated user's profile
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        user_response = supabase.table("users").select(
            "user_id, email, oauth_provider, credits, is_active, created_at"
        ).eq("user_id", str(current_user_id)).execute()
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_response.data[0]
        
        return UserResponse(
            user_id=UUID(user["user_id"]),
            email=user["email"],
            oauth_provider=user["oauth_provider"],
            credits=user["credits"],
            is_active=user["is_active"],
            created_at=datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")) if isinstance(user["created_at"], str) else user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Update current authenticated user's profile
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Build update dict
        update_data = {}
        if user_update.email is not None:
            # Check if email is already taken
            existing = supabase.table("users").select("user_id").eq("email", user_update.email).execute()
            if existing.data and UUID(existing.data[0]["user_id"]) != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            update_data["email"] = user_update.email
        
        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update user
        supabase.table("users").update(update_data).eq("user_id", str(current_user_id)).execute()
        
        # Get updated user
        user_response = supabase.table("users").select(
            "user_id, email, oauth_provider, credits, is_active, created_at"
        ).eq("user_id", str(current_user_id)).execute()
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_response.data[0]
        
        return UserResponse(
            user_id=UUID(user["user_id"]),
            email=user["email"],
            oauth_provider=user["oauth_provider"],
            credits=user["credits"],
            is_active=user["is_active"],
            created_at=datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")) if isinstance(user["created_at"], str) else user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(current_user_id: UUID = Depends(get_current_user_id)):
    """
    Delete current authenticated user's account
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        # Delete user (cascade will handle related records)
        supabase.table("users").delete().eq("user_id", str(current_user_id)).execute()
        
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID):
    """
    Get user by ID (public endpoint for user lookup)
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()
        
        user_response = supabase.table("users").select(
            "user_id, email, oauth_provider, credits, is_active, created_at"
        ).eq("user_id", str(user_id)).execute()
        
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_response.data[0]
        
        return UserResponse(
            user_id=UUID(user["user_id"]),
            email=user["email"],
            oauth_provider=user["oauth_provider"],
            credits=user["credits"],
            is_active=user["is_active"],
            created_at=datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")) if isinstance(user["created_at"], str) else user["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(current_user_id: UUID = Depends(get_current_user_id)):
    """
    Get dashboard statistics for the current user
    """
    try:
        db_manager = DatabaseManager.get_instance()
        supabase = db_manager.get_connection()

        # Get current week start and previous week start
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())  # Monday of current week
        prev_week_start = week_start - timedelta(days=7)  # Monday of previous week

        # Get user's credits
        user_response = supabase.table("users").select("credits").eq("user_id", str(current_user_id)).execute()
        credits_remaining = user_response.data[0]["credits"] if user_response.data else 0

        # Get job bookmark statistics
        bookmarks_response = supabase.table("job_bookmarks").select("application_status, created_at").eq("user_id", str(current_user_id)).execute()

        # Count by status
        total_bookmarks = len(bookmarks_response.data) if bookmarks_response.data else 0
        in_interview = sum(1 for b in (bookmarks_response.data or []) if b.get("application_status") == "interviewing")
        failed_interview = sum(1 for b in (bookmarks_response.data or []) if b.get("application_status") == "interviewed_failed")
        potential_jobs = sum(1 for b in (bookmarks_response.data or []) if b.get("application_status") == "interested")

        # Calculate weekly changes
        def parse_created_at(created_at_str: str) -> datetime:
            """Parse created_at string and make it offset-aware"""
            if created_at_str.endswith("Z"):
                created_at_str = created_at_str[:-1] + "+00:00"
            dt = datetime.fromisoformat(created_at_str)
            # Make sure it's offset-aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        current_week_bookmarks = sum(1 for b in (bookmarks_response.data or [])
                                   if b.get("created_at") and
                                   parse_created_at(b["created_at"]) >= week_start)
        prev_week_bookmarks = sum(1 for b in (bookmarks_response.data or [])
                                if b.get("created_at") and
                                prev_week_start <= parse_created_at(b["created_at"]) < week_start)

        current_week_interview = sum(1 for b in (bookmarks_response.data or [])
                                   if b.get("application_status") == "interviewing" and
                                   b.get("created_at") and
                                   parse_created_at(b["created_at"]) >= week_start)

        prev_week_interview = sum(1 for b in (bookmarks_response.data or [])
                                if b.get("application_status") == "interviewing" and
                                b.get("created_at") and
                                prev_week_start <= parse_created_at(b["created_at"]) < week_start)

        # Calculate percentage changes
        def calculate_percentage_change(current, previous):
            if previous == 0:
                return current * 100 if current > 0 else 0
            return ((current - previous) / previous) * 100

        job_bookmarks_change = calculate_percentage_change(current_week_bookmarks, prev_week_bookmarks)
        in_interview_change = calculate_percentage_change(current_week_interview, prev_week_interview)

        # Get avg match score from resume_analyses
        resumes_response = supabase.table("resumes").select("id").eq("user_id", str(current_user_id)).execute()
        resume_ids = [r["id"] for r in (resumes_response.data or [])]

        avg_match_score = None
        if resume_ids:
            analyses_response = supabase.table("resume_analyses").select("match_score").in_("resume_id", resume_ids).execute()
            scores = [a["match_score"] for a in (analyses_response.data or []) if a.get("match_score") is not None]
            if scores:
                avg_match_score = round(sum(scores) / len(scores), 1)

        avg_match_score_change = None
        potential_jobs_change = None  # This would need more complex logic to track changes

        return DashboardStatsResponse(
            job_bookmarks=total_bookmarks,
            in_interview=in_interview,
            failed_interview=failed_interview,
            avg_match_score=avg_match_score,
            credits_remaining=credits_remaining,
            potential_jobs=potential_jobs,
            job_bookmarks_change=round(job_bookmarks_change, 1) if job_bookmarks_change != 0 else None,
            in_interview_change=round(in_interview_change, 1) if in_interview_change != 0 else None,
            avg_match_score_change=avg_match_score_change,
            potential_jobs_change=potential_jobs_change
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard stats for user {current_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard statistics: {str(e)}"
        )

