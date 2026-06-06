from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional
from datetime import datetime, timezone
from app.core.security import verify_token, verify_api_key
# Note: UserRepository placeholder
from app.repositories.base_repository import BaseRepository
from app.models.database import User, ApiKey
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Security schemes
http_bearer = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ============= JWT DEPENDENCY =============
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency untuk validate JWT token dari Authorization header
    """
    token = credentials.credentials
    payload = verify_token(token)  # Raises HTTPException jika invalid
    
    # Manual query as UserRepository is not fully implemented yet
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

# ============= API KEY DEPENDENCY =============
async def get_current_user_by_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency untuk validate API Key
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required"
        )
    
    # Manual query for API Key
    import hashlib
    provided_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == provided_hash).options(selectinload(ApiKey.user))
    )
    api_key_record = result.scalar_one_or_none()
    
    if not api_key_record or not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    # Check expiration
    if api_key_record.expires_at and api_key_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key expired"
        )
    
    # Update last_used_at
    api_key_record.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    
    return api_key_record.user

# ============= ROLE-BASED ACCESS CONTROL =============
async def require_admin(current_user = Depends(get_current_user)):
    """
    Dependency untuk enforce admin role
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
