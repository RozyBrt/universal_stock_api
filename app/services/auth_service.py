from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.core.security import verify_password, create_access_token
from app.models.schemas import TokenResponse
from fastapi import HTTPException, status
from datetime import timedelta
from app.config import settings

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
        
    async def authenticate(self, email: str, password: str) -> TokenResponse:
        """Verify user dan generate JWT token"""
        user = await self.user_service.get_user_by_email(email)
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
            
        # Generate Access Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, 
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token="refresh_token_placeholder", # Implement refresh token later if needed
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
