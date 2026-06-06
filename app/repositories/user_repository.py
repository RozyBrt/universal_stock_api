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
    pass
