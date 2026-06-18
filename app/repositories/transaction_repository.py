from app.repositories.base_repository import BaseRepository
from app.models.database import Transaction
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import Optional

class TransactionRepository(BaseRepository[Transaction]):
    async def get_by_item(self, item_id: int, skip: int = 0, limit: int = 100):
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.item_id == item_id)
            .order_by(desc(Transaction.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_latest_by_item(self, item_id: int) -> Optional[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.item_id == item_id)
            .order_by(desc(Transaction.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100):
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.performed_by == user_id)
            .order_by(desc(Transaction.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all(self, skip: int = 0, limit: int = 100):
        result = await self.session.execute(
            select(Transaction)
            .order_by(desc(Transaction.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

