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

