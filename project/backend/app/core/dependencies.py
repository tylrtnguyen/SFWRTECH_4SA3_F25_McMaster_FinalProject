"""
FastAPI dependencies for authentication
Supports both Supabase JWT tokens and backend JWT tokens
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID
from app.core.auth import decode_access_token, decode_supabase_token
from app.core.singleton import DatabaseManager

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """
    Dependency to get current user ID from JWT token
    Supports both Supabase JWT tokens and backend JWT tokens
    """
    token = credentials.credentials
    
    # Strip "Bearer " prefix if present (shouldn't be, but handle it just in case)
    if token.startswith("Bearer "):
        token = token[7:]  # Remove "Bearer " prefix
        logger.warning("Token had 'Bearer ' prefix, stripping it")
    
    # Validate token is present and not empty
    if not token:
        logger.error("Empty or missing token in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not isinstance(token, str) or not token.strip():
        logger.error(f"Invalid token format: {type(token)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Token received (length: {len(token)}, preview: {token[:50]}...)")
    
    # Try Supabase token first (since frontend uses Supabase auth)
    supabase_payload = None
    try:
        supabase_payload = decode_supabase_token(token)
        logger.debug(f"Supabase payload: {supabase_payload}")
        if supabase_payload:
            logger.info(f"Supabase token decoded successfully. Payload keys: {list(supabase_payload.keys())}")
    except Exception as e:
        logger.error(f"Exception during Supabase token decode: {str(e)}", exc_info=True)
        supabase_payload = None

    if supabase_payload:
        user_id_str = supabase_payload.get("sub")
        if not user_id_str:
            logger.warning("Supabase token decoded but missing 'sub' field")
            # Fall through to backend token verification
        else:
            try:
                user_id = UUID(user_id_str)
                # Verify user exists in database
                try:
                    db_manager = DatabaseManager.get_instance()
                    supabase = db_manager.get_connection()

                    # Execute query and check for errors
                    user_response = supabase.table("users").select("user_id").eq("user_id", str(user_id)).execute()

                    # Check if Supabase returned an error
                    if hasattr(user_response, 'error') and user_response.error:
                        logger.error(f"Supabase query error: {user_response.error}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Database query failed: {str(user_response.error)}",
                            headers={"WWW-Authenticate": "Bearer"},
                        )

                    # Check if user exists
                    if user_response.data and len(user_response.data) > 0:
                        logger.debug(f"Successfully authenticated user: {user_id}")
                        return user_id
                    else:
                        # User doesn't exist in backend database
                        logger.warning(f"User authenticated via Supabase token but not found in database (user_id: {user_id_str})")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"User not found in system. Please ensure your account is properly synchronized (user_id: {user_id_str})",
                            headers={"WWW-Authenticate": "Bearer"},
                        )
                except HTTPException:
                    # Re-raise HTTP exceptions
                    raise
                except Exception as db_error:
                    # Database connection or query error
                    logger.error(f"Database error during user lookup: {str(db_error)}", exc_info=True)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to verify user in database: {str(db_error)}",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            except ValueError as e:
                # Invalid UUID format in token
                logger.warning(f"Invalid UUID format in Supabase token 'sub' field: {user_id_str}")
                # Fall through to backend token verification
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
    else:
        logger.debug("Supabase token decode returned None, trying backend token")
    
    # Fall back to backend token verification
    logger.debug("Attempting backend token verification")
    payload = decode_access_token(token)
    
    if payload is None:
        logger.warning("Both Supabase and backend token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials - token could not be verified. Please ensure you are logged in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Backend token decoded but missing 'sub' field")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials - missing user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_uuid = UUID(user_id)
        logger.debug(f"Successfully authenticated user via backend token: {user_uuid}")
        return user_uuid
    except ValueError:
        logger.warning(f"Invalid UUID format in backend token 'sub' field: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

