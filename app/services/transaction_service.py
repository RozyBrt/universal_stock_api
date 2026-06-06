from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.transaction_repository import TransactionRepository
from app.models.database import Transaction
from typing import Optional

class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TransactionRepository(session, Transaction)

    async def get_all_transactions(self, skip: int = 0, limit: int = 100):
        """Ambil semua riwayat transaksi stok"""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_item_history(self, item_id: int, skip: int = 0, limit: int = 100):
        """Lihat riwayat transaksi untuk barang spesifik"""
        return await self.repo.get_by_item(item_id, skip=skip, limit=limit)

    async def get_user_history(self, user_id: int, skip: int = 0, limit: int = 100):
        """Lihat transaksi yang dilakukan oleh user tertentu"""
        return await self.repo.get_by_user(user_id, skip=skip, limit=limit)
