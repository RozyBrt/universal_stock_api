from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.category_repository import CategoryRepository
from app.models.database import Category
from app.models.schemas import CategoryCreate, CategoryUpdate
import re

class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CategoryRepository(session, Category)

    def _generate_slug(self, name: str) -> str:
        """Simple slug generator"""
        return re.sub(r'[^\w+]', '-', name.lower()).strip('-')

    async def create_category(self, data: CategoryCreate) -> Category:
        # Check if name exists
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise ValueError(f"Category with name '{data.name}' already exists")
        
        slug = self._generate_slug(data.name)
        
        # Check if slug exists
        existing_slug = await self.repo.get_by_slug(slug)
        if existing_slug:
            # Add a random or incrementing suffix if needed, but for now just error
            raise ValueError(f"Category slug '{slug}' already exists")

        return await self.repo.create(
            name=data.name,
            description=data.description,
            slug=slug
        )

    async def get_categories(self, skip: int = 0, limit: int = 100):
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_category(self, category_id: int) -> Category:
        return await self.repo.get_by_id(category_id)

    async def update_category(self, category_id: int, data: CategoryUpdate) -> Category:
        update_data = data.model_dump(exclude_none=True)
        if "name" in update_data:
            update_data["slug"] = self._generate_slug(update_data["name"])
            
        return await self.repo.update(category_id, **update_data)

    async def delete_category(self, category_id: int) -> bool:
        return await self.repo.delete(category_id)
