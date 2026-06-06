from app.repositories.base_repository import BaseRepository
from app.models.database import Category, Transaction, User, ApiKey

class CategoryRepository(BaseRepository[Category]):
    pass

class TransactionRepository(BaseRepository[Transaction]):
    pass

class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str):
        from sqlalchemy import select
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

class ApiKeyRepository(BaseRepository[ApiKey]):
    async def get_by_hash_with_user(self, key_hash: str):
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash).options(selectinload(ApiKey.user))
        )
        return result.scalar_one_or_none()
