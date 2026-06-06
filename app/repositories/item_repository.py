from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, func, desc
from app.models.database import Item, Category
from typing import Optional, List, Dict
from datetime import datetime

class ItemRepository:
    """Repository untuk Item dengan optimization: eager loading, pagination, row locking"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ============= READ OPERATIONS (Anti N+1) =============
    
    async def get_by_id(self, item_id: int) -> Optional[Item]:
        """
        Get item by ID dengan eager-load category.
        
        Anti-pattern AVOIDED:
            result = select(Item).where(Item.id == item_id)
            # Kalau lu access item.category nanti, trigger 1 extra query (N+1)
        
        Pattern DIGUNAKAN:
            selectinload(Item.category) → 1 query total (SELECT * FROM items + SELECT * FROM categories)
        """
        result = await self.session.execute(
            select(Item)
            .options(selectinload(Item.category))
            .where(Item.id == item_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_with_pagination(
        self,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False
    ) -> tuple[List[Item], int]:
        """
        Get items dengan pagination dan eager-load category.
        
        Returns:
            (items list, total count)
        
        Why tuple return?
            Frontend butuh total count untuk render pagination UI
            Better return dalam satu query execution daripada 2 separate calls
        """
        # Query untuk count (efficient, tidak perlu load semua rows)
        count_stmt = select(func.count(Item.id))
        if not include_inactive:
            count_stmt = count_stmt.where(Item.is_active == True)
        
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()
        
        # Query untuk items dengan pagination
        items_stmt = (
            select(Item)
            .options(selectinload(Item.category))  # ← Prevent N+1
            .offset(skip)
            .limit(limit)
            .order_by(desc(Item.created_at))
        )
        
        if not include_inactive:
            items_stmt = items_stmt.where(Item.is_active == True)
        
        items_result = await self.session.execute(items_stmt)
        items = items_result.scalars().unique().all()  # .unique() karena selectinload bisa duplicate rows
        
        return items, total
    
    async def search_items(
        self,
        search_term: Optional[str] = None,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        low_stock_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Item], int]:
        """
        Advanced search dengan multiple filters.
        
        Filters:
            - search_term: ILIKE search di name dan SKU
            - category_id: Filter by category
            - min_price, max_price: Price range
            - low_stock_only: qty < reorder_level
        
        Returns:
            (filtered items, total count)
        
        Why ILIKE?
            PostgreSQL case-insensitive search (better UX)
        """
        # Build filters list (cleaner than nested if statements)
        filters = [Item.is_active == True]
        
        if search_term:
            search_pattern = f"%{search_term}%"
            filters.append(
                (Item.name.ilike(search_pattern)) | 
                (Item.sku.ilike(search_pattern))
            )
        
        if category_id:
            filters.append(Item.category_id == category_id)
        
        if min_price is not None:
            filters.append(Item.unit_price >= min_price)
        
        if max_price is not None:
            filters.append(Item.unit_price <= max_price)
        
        if low_stock_only:
            filters.append(Item.quantity_in_stock < Item.reorder_level)
        
        # Count query
        count_stmt = select(func.count(Item.id)).where(and_(*filters))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()
        
        # Items query
        items_stmt = (
            select(Item)
            .options(selectinload(Item.category))
            .where(and_(*filters))
            .offset(skip)
            .limit(limit)
            .order_by(desc(Item.created_at))
        )
        
        items_result = await self.session.execute(items_stmt)
        items = items_result.scalars().unique().all()
        
        return items, total
    
    async def get_by_sku(self, sku: str) -> Optional[Item]:
        """Get item by SKU (with category eager load)"""
        result = await self.session.execute(
            select(Item)
            .options(selectinload(Item.category))
            .where(Item.sku == sku)
        )
        return result.scalar_one_or_none()
    
    async def get_by_category(self, category_id: int, skip: int = 0, limit: int = 50) -> tuple[List[Item], int]:
        """Get items by category dengan pagination"""
        count_result = await self.session.execute(
            select(func.count(Item.id))
            .where(and_(Item.category_id == category_id, Item.is_active == True))
        )
        total = count_result.scalar()
        
        items_result = await self.session.execute(
            select(Item)
            .options(selectinload(Item.category))
            .where(and_(Item.category_id == category_id, Item.is_active == True))
            .offset(skip)
            .limit(limit)
            .order_by(desc(Item.created_at))
        )
        items = items_result.scalars().unique().all()
        
        return items, total
    
    async def get_low_stock_items(self, skip: int = 0, limit: int = 50) -> tuple[List[Item], int]:
        """Get items di bawah reorder_level dengan pagination"""
        count_result = await self.session.execute(
            select(func.count(Item.id))
            .where(and_(
                Item.quantity_in_stock < Item.reorder_level,
                Item.is_active == True
            ))
        )
        total = count_result.scalar()
        
        items_result = await self.session.execute(
            select(Item)
            .options(selectinload(Item.category))
            .where(and_(
                Item.quantity_in_stock < Item.reorder_level,
                Item.is_active == True
            ))
            .offset(skip)
            .limit(limit)
            .order_by(Item.quantity_in_stock.asc())  # Paling critical (paling low stock) di depan
        )
        items = items_result.scalars().unique().all()
        
        return items, total
    
    # ============= WRITE OPERATIONS (With Locking) =============
    
    async def get_for_update(self, item_id: int) -> Optional[Item]:
        """
        Get item dengan row-level lock (FOR UPDATE).
        
        Critical untuk prevent race condition di stock operations.
        
        How it works:
            - Database LOCK baris ini secara exclusive
            - Concurrent transaction ke item ini akan WAIT sampai lock release
            - Guarantee: hanya satu transaction yang bisa update item ini at once
        
        Usage:
            item = await repo.get_for_update(item_id)
            if item.quantity_in_stock < qty:
                raise ValueError("Insufficient stock")
            item.quantity_in_stock -= qty
            await session.commit()
        """
        result = await self.session.execute(
            select(Item)
            .where(Item.id == item_id)
            .with_for_update()  # ← PostgreSQL FOR UPDATE clause
        )
        return result.scalar_one_or_none()
    
    async def update_stock(self, item_id: int, quantity_delta: int) -> Optional[Item]:
        """
        Update stock quantity dengan validation.
        
        Args:
            item_id: Item yang mau di-update
            quantity_delta: +/- (positif untuk add, negatif untuk remove)
        
        Returns:
            Updated item atau None jika tidak ditemukan
        
        Raises:
            ValueError: Jika insufficient stock atau item tidak ditemukan
        """
        item = await self.get_for_update(item_id)
        
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        new_quantity = item.quantity_in_stock + quantity_delta
        
        if new_quantity < 0:
            raise ValueError(
                f"Insufficient stock. Required: {abs(quantity_delta)}, "
                f"Available: {item.quantity_in_stock}"
            )
        
        item.quantity_in_stock = new_quantity
        item.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(item)
        
        return item
    
    async def create(self, **kwargs) -> Item:
        """Create new item"""
        item = Item(**kwargs)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item, ["category"])
        return item
    
    async def update(self, item_id: int, **kwargs) -> Optional[Item]:
        """Update item fields (non-stock related)"""
        item = await self.get_by_id(item_id)
        
        if not item:
            return None
        
        # Filter out None values (partial update)
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        for key, value in update_data.items():
            setattr(item, key, value)
        
        item.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(item, ["category"])
        
        return item
    
    async def delete(self, item_id: int) -> bool:
        """Soft delete item (set is_active = False)"""
        item = await self.get_by_id(item_id)
        
        if not item:
            return False
        
        item.is_active = False
        item.updated_at = datetime.utcnow()
        
        await self.session.commit()
        return True
