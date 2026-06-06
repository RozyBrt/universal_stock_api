from app.repositories.base_repository import BaseRepository
from app.models.database import Category
from sqlalchemy.future import select
from typing import Optional

class CategoryRepository(BaseRepository[Category]):
    async def get_by_slug(self, slug: str) -> Optional[Category]:
        result = await self.session.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Category]:
        result = await self.session.execute(
            select(Category).where(Category.name == name)
        )
        return result.scalar_one_or_none()
