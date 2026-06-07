from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, APIKeyHeader
from typing import Optional
from datetime import datetime, timezone
from app.core.security import verify_token, verify_api_key
from app.repositories.user_repository import UserRepository, ApiKeyRepository
from app.models.database import User, ApiKey
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ============= JWT & API KEY DEPENDENCY =============
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency untuk validate JWT token atau API Key.
    Swagger otomatis akan memunculkan kedua opsi (OAuth2 dan APIKeyHeader).
    """
    if api_key:
        import hashlib
        provided_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        api_key_repo = ApiKeyRepository(db, ApiKey)
        api_key_record = await api_key_repo.get_by_hash_with_user(provided_hash)
        
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
        api_key_record.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.commit()
        return api_key_record.user

    elif token:
        payload = verify_token(token)  # Raises HTTPException jika invalid
        
        user_repo = UserRepository(db, User)
        user = await user_repo.get_by_id(int(payload["sub"]))
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        return user
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide Bearer Token or X-API-Key header"
    )

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
