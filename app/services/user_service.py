from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repositories.user_repository import UserRepository, ApiKeyRepository
from app.models.database import User, ApiKey
from app.models.schemas import RegisterRequest
from app.core.security import hash_password, generate_api_key
from typing import Optional

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session, User)
        self.api_key_repo = ApiKeyRepository(session, ApiKey)
    
    async def register(self, data: RegisterRequest) -> User:
        """Register user baru dengan hashed password"""
        # Check email availability
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise ValueError("Email already registered")
            
        # Hash password
        hashed_pwd = hash_password(data.password)
        
        # Logic: First user is admin
        user_count = await self.user_repo.session.execute(
            select(func.count()).select_from(User)
        )
        is_first_user = user_count.scalar() == 0
        role = "admin" if is_first_user else "user"

        # Create user
        user = await self.user_repo.create(
            username=data.username,
            email=data.email,
            password_hash=hashed_pwd,
            full_name=data.full_name,
            role=role
        )
        return user
        
    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.user_repo.get_by_email(email)
        
    async def create_api_key(self, user_id: int, name: str = "Default Key") -> str:
        """Generate dan simpan API key baru"""
        plain_key, key_hash = generate_api_key()
        
        await self.api_key_repo.create(
            user_id=user_id,
            key_hash=key_hash,
            name=name
        )
        
        return plain_key
        
    async def get_user_api_keys(self, user_id: int):
        """Ambil semua API key milik user"""
        return await self.api_key_repo.get_by_user_id(user_id)
        
    async def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        """Cabut API key (soft delete/inactive)"""
        key = await self.api_key_repo.get_by_id(key_id)
        if not key or key.user_id != user_id:
            return False
        
        key.is_active = False
        await self.session.commit()
        return True
