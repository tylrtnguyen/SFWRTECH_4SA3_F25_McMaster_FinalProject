"""
Users Router
Handles user account management, authentication, and OAuth
"""

from fastapi import APIRouter, HTTPException, Depends, status
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from app.models.schemas import (
    UserRegister,
    UserLogin,
    OAuthLogin,
    UserResponse,
    UserUpdate,
    Token
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

