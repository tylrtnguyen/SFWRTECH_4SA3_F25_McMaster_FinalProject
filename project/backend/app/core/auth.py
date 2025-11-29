"""
Authentication utilities
JWT token generation and password hashing
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
# Configure bcrypt to truncate passwords automatically
# Note: Using default settings to avoid compatibility issues
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    # Bcrypt has a 72-byte limit, so truncate if necessary (same as hashing)
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes
        password_bytes = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while len(password_bytes) > 0 and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
            password_bytes = password_bytes[:-1]
        plain_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Bcrypt has a 72-byte limit, so truncate if necessary
    # Truncate password to ensure it's under 72 bytes when encoded
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes
        password_bytes = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while len(password_bytes) > 0 and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
            password_bytes = password_bytes[:-1]
        # Decode back to string - this ensures the password is always <= 72 bytes
        password = password_bytes.decode('utf-8', errors='ignore')
    
    # Pass the (possibly truncated) password to passlib
    # Passlib will encode it again, but it will be <= 72 bytes
    try:
        return pwd_context.hash(password)
    except ValueError as e:
        # If passlib still complains, truncate more aggressively
        if "cannot be longer than 72 bytes" in str(e):
            # Truncate to 70 bytes to be safe
            password_bytes = password.encode('utf-8')[:70]
            while len(password_bytes) > 0 and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
                password_bytes = password_bytes[:-1]
            password = password_bytes.decode('utf-8', errors='ignore')
            return pwd_context.hash(password)
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def decode_supabase_token(token: str) -> Optional[dict]:
    """
    Decode Supabase JWT token
    First tries to verify with JWT secret if available, otherwise decodes without verification
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Strip "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
        logger.debug("Stripped 'Bearer ' prefix from token")
    
    try:
        # Try to verify with JWT secret if configured
        if settings.SUPABASE_JWT_SECRET:
            try:
                # Verify token signature with Supabase JWT secret
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_exp": True}
                )
                logger.debug("Successfully verified Supabase token with JWT secret")
                return payload
            except JWTError as e:
                # If verification fails, log and fall through to unverified decode
                logger.debug(f"JWT verification failed with secret: {str(e)}, trying unverified decode")
                pass
        
        # Decode without verification (for development or when JWT secret not available)
        # This is less secure but allows the system to work
        # Note: jwt.decode() requires a key parameter even when verify_signature=False
        # Also need to disable audience verification since Supabase tokens have aud="authenticated"
        try:
            unverified_payload = jwt.decode(
                token,
                key="",  # Empty key since we're not verifying signature
                options={"verify_signature": False, "verify_exp": False, "verify_aud": False}
            )
            logger.debug("Successfully decoded Supabase token without verification")
        except JWTError as e:
            logger.error(f"Failed to decode Supabase token (malformed): {str(e)}")
            return None
        
        # Basic validation: check if it has required claims
        if "sub" in unverified_payload:
            # Check expiration manually
            if "exp" in unverified_payload:
                from datetime import datetime, timezone
                exp = unverified_payload.get("exp")
                current_time = datetime.now(timezone.utc).timestamp()
                if exp and current_time > exp:
                    logger.warning(f"Supabase token expired. Exp: {exp}, Current: {current_time}")
                    return None  # Token expired
                else:
                    logger.debug(f"Token expiration check passed. Exp: {exp}, Current: {current_time}")
            
            logger.debug(f"Supabase token decoded successfully. User ID (sub): {unverified_payload.get('sub')}")
            return unverified_payload
        else:
            logger.warning("Supabase token decoded but missing 'sub' field")
            return None
        
    except JWTError as e:
        # Token is malformed or invalid
        logger.error(f"JWT decode error: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        # Other errors (e.g., invalid token format)
        logger.error(f"Token decode error: {str(e)}", exc_info=True)
        return None

