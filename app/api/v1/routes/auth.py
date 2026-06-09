from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.config import settings
from app.api.v1.dependencies import get_current_user
from app.models.schemas import LoginRequest, TokenResponse, RegisterRequest, ApiKeyResponse
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.database import get_db
from app.core.exceptions import InvalidCredentialsException, DuplicateEmailException

router = APIRouter(prefix="/auth", tags=["auth"])

# ============= LOGIN ENDPOINT (RATE LIMITED) =============

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        429: {"description": "Too many login attempts"}
    }
)
@limiter.limit(settings.RATE_LIMIT_AUTH_LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint dengan JWT token generation.
    """
    service = AuthService(db)
    tokens = await service.authenticate(form_data.username, form_data.password)
    return tokens

# ============= REGISTER ENDPOINT (RATE LIMITED) =============

@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Invalid input"},
        409: {"description": "Email already registered"},
        429: {"description": "Too many registration attempts"}
    }
)
@limiter.limit(settings.RATE_LIMIT_AUTH_REGISTER)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    User registration endpoint.
    """
    user_service = UserService(db)
    user = await user_service.register(data)
    return {"message": "User registered successfully", "user_id": user.id}

# ============= REFRESH TOKEN ENDPOINT (RATE LIMITED) =============

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses={
        200: {"description": "Token refreshed"},
        401: {"description": "Invalid refresh token"},
        429: {"description": "Too many refresh attempts"}
    }
)
@limiter.limit(settings.RATE_LIMIT_AUTH_REFRESH)
async def refresh_token(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token menggunakan refresh token.
    """
    service = AuthService(db)
    tokens = await service.refresh_tokens(current_user.id)
    return tokens

# ============= API KEY MANAGEMENT =============

@router.get("/api-key", response_model=list[ApiKeyResponse])
@limiter.limit(settings.RATE_LIMIT_API_KEYS)
async def get_api_keys(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ambil daftar API Key milik user"""
    user_service = UserService(db)
    return await user_service.get_user_api_keys(current_user.id)

@router.post("/api-key/generate")
@limiter.limit(settings.RATE_LIMIT_API_KEYS)
async def generate_api_key(
    request: Request,
    name: str = "Default Key",
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate API Key baru"""
    user_service = UserService(db)
    new_key = await user_service.create_api_key(current_user.id, name)
    return {"api_key": new_key, "message": "Key generated successfully"}

@router.delete("/api-key/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.RATE_LIMIT_API_KEYS)
async def revoke_api_key(
    request: Request,
    key_id: int,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cabut/nonaktifkan API Key"""
    user_service = UserService(db)
    success = await user_service.revoke_api_key(key_id, current_user.id)
    if not success:
        from app.core.exceptions import InvalidInputException
        raise InvalidInputException(field="key_id", message="API Key not found or unauthorized")
    return None
