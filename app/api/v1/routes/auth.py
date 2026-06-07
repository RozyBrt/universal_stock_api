from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.schemas import LoginRequest, TokenResponse, RegisterRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register user baru"""
    service = UserService(db)
    try:
        user = await service.register(data)
        return {"message": "User registered successfully", "user_id": user.id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login dan dapatkan JWT token"""
    service = AuthService(db)
    # OAuth2PasswordRequestForm menggunakan field 'username' (di sini diisi email)
    tokens = await service.authenticate(data.username, data.password)
    return tokens

@router.post("/api-key/generate")
async def generate_api_key(
    name: str = "Default Key",
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate API key untuk current user"""
    service = UserService(db)
    plain_key = await service.create_api_key(current_user.id, name)
    return {
        "api_key": plain_key,
        "message": "Save this key securely, it cannot be recovered!"
    }

from sqlalchemy import select
from app.models.database import ApiKey

@router.get("/api-key", response_model=list)
async def get_api_keys(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List API keys for current user"""
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id)
    )
    keys = result.scalars().all()
    return [{"id": k.id, "name": k.name, "created_at": k.created_at, "is_active": k.is_active, "expires_at": k.expires_at, "last_used_at": k.last_used_at} for k in keys]

@router.delete("/api-key/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke API key"""
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    
    key.is_active = False
    await db.commit()
    return None
