from fastapi import APIRouter, Depends, HTTPException, status
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
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login dan dapatkan JWT token"""
    service = AuthService(db)
    tokens = await service.authenticate(data.email, data.password)
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
