from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from app.core.rate_limit import limiter
from app.config import settings
from app.api.v1.dependencies import get_current_user
from app.models.schemas import TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("", response_model=list[TransactionResponse])
@limiter.limit(settings.RATE_LIMIT_TRANSACTIONS_GET)
async def get_all_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user), # Harus login
    db: AsyncSession = Depends(get_db)
):
    """Melihat semua riwayat transaksi stok (Perlu Login)"""
    service = TransactionService(db)
    return await service.get_all_transactions(skip=skip, limit=limit)

@router.get("/item/{item_id}", response_model=list[TransactionResponse])
@limiter.limit(settings.RATE_LIMIT_TRANSACTIONS_GET)
async def get_item_transactions(
    request: Request,
    item_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Melihat riwayat transaksi untuk barang tertentu"""
    service = TransactionService(db)
    return await service.get_item_history(item_id, skip=skip, limit=limit)

@router.get("/me", response_model=list[TransactionResponse])
@limiter.limit(settings.RATE_LIMIT_TRANSACTIONS_GET)
async def get_my_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Melihat riwayat transaksi yang dilakukan diri sendiri"""
    service = TransactionService(db)
    return await service.get_user_history(current_user.id, skip=skip, limit=limit)
