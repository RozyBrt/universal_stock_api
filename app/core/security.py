from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import hashlib
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from functools import wraps
from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============= PASSWORD UTILITIES =============
def hash_password(password: str) -> str:
    """Hash password menggunakan bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password terhadap hash"""
    return pwd_context.verify(plain_password, hashed_password)

# ============= JWT UTILITIES =============
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate JWT access token
    
    Args:
        data: Payload yang mau di-encode
        expires_delta: Custom expiration time
    
    Returns:
        JWT token sebagai string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify dan decode JWT token
    
    Raises:
        HTTPException: Jika token invalid atau expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# ============= API KEY UTILITIES =============
def generate_api_key() -> tuple[str, str]:
    """
    Generate API key dengan format: prefix_randomstring
    
    Returns:
        (plain_key, key_hash) - simpan plain_key ke user, hash ke database
    """
    plain_key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    return plain_key, key_hash

def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Verify API key terhadap stored hash"""
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    # Constant-time comparison untuk mencegah timing attacks
    return secrets.compare_digest(provided_hash, stored_hash)
