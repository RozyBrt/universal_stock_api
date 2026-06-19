from app.repositories.item_repository import ItemRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.category_repository import CategoryRepository
from app.models.database import Item, Transaction, Category
from app.models.schemas import ItemCreate, ItemUpdate, TransactionType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, cast, Date
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from app.core.websocket import manager
from app.core.exceptions import DuplicateSKUException, CategoryNotFoundException

class ItemService:
    """
    Service layer untuk Item business logic.
    
    Responsibility:
    - Validate input data
    - Enforce business rules
    - Coordinate dengan repositories
    - Handle transactions (inventory movements)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.item_repo = ItemRepository(session)
        self.transaction_repo = TransactionRepository(session, Transaction)
    
    # ============= READ OPERATIONS =============
    
    async def get_item_by_id(self, item_id: int) -> Optional[Item]:
        """Get single item by ID"""
        return await self.item_repo.get_by_id(item_id)
    
    async def list_items(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Item], int]:
        """
        List semua items dengan pagination.
        
        Returns:
            (items, total_count)
        """
        return await self.item_repo.get_all_with_pagination(skip=skip, limit=limit)
    
    async def search_items(
        self,
        search_term: Optional[str] = None,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        low_stock_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Item], int]:
        """
        Advanced search dengan filters.
        
        Business Rules:
        - Only return active items
        - low_stock_only filter: qty < reorder_level
        """
        return await self.item_repo.search_items(
            search_term=search_term,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            low_stock_only=low_stock_only,
            skip=skip,
            limit=limit
        )
    
    async def get_low_stock_items(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Item], int]:
        """Get items dengan stock di bawah reorder_level"""
        return await self.item_repo.get_low_stock_items(skip=skip, limit=limit)
    
    async def get_items_by_category(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Item], int]:
        """Get items by specific category"""
        return await self.item_repo.get_by_category(
            category_id=category_id,
            skip=skip,
            limit=limit
        )
    
    # ============= CREATE OPERATION =============
    
    async def create_item(
        self,
        item_data: ItemCreate,
        created_by_user_id: int
    ) -> Item:
        """
        Create item baru dengan validation.
        
        Business Rules:
        - SKU harus unique
        - Initial quantity >= 0
        - unit_price > 0
        """
        # Check Category exists
        category_repo = CategoryRepository(self.session, Category)
        category = await category_repo.get_by_id(item_data.category_id)
        if not category:
            raise CategoryNotFoundException(item_data.category_id)

        # Check SKU not already exist
        existing = await self.item_repo.get_by_sku(item_data.sku)
        if existing:
            raise DuplicateSKUException(item_data.sku)
        
        # Validate price
        if item_data.unit_price <= 0:
            raise ValueError("unit_price harus > 0")
        
        # Create item
        item = await self.item_repo.create(
            name=item_data.name,
            description=item_data.description,
            sku=item_data.sku,
            category_id=item_data.category_id,
            unit_price=item_data.unit_price,
            quantity_in_stock=item_data.quantity_in_stock or 0,
            reorder_level=item_data.reorder_level or 10,
            created_by=created_by_user_id,
            is_active=True
        )
        
        # Broadcast creation
        await manager.broadcast({
            "type": "ITEM_CHANGED",
            "action": "CREATE",
            "item_id": item.id,
            "sku": item.sku,
            "name": item.name
        })
        
        return item
    
    # ============= UPDATE OPERATION =============
    
    async def update_item(
        self,
        item_id: int,
        update_data: ItemUpdate
    ) -> Optional[Item]:
        """
        Update item (non-stock fields).
        
        Stock updates harus via add_stock / remove_stock (audit trail)
        """
        # Prepare update dict (exclude None values)
        data_to_update = update_data.dict(exclude_unset=True)
        
        if not data_to_update:
            return await self.item_repo.get_by_id(item_id)
        
        # Validate price jika di-update
        if 'unit_price' in data_to_update and data_to_update['unit_price']:
            if data_to_update['unit_price'] <= 0:
                raise ValueError("unit_price harus > 0")
        
        updated_item = await self.item_repo.update(item_id, **data_to_update)
        if updated_item:
            await manager.broadcast({
                "type": "ITEM_CHANGED",
                "action": "UPDATE",
                "item_id": item_id,
                "sku": updated_item.sku,
                "name": updated_item.name
            })
        return updated_item
    
    # ============= DELETE OPERATION =============
    
    async def delete_item(self, item_id: int) -> bool:
        """Soft delete item"""
        success = await self.item_repo.delete(item_id)
        if success:
            await manager.broadcast({
                "type": "ITEM_CHANGED",
                "action": "DELETE",
                "item_id": item_id
            })
        return success
    
    # ============= INVENTORY OPERATIONS (CRITICAL) =============
    
    async def add_stock(
        self,
        item_id: int,
        quantity: int,
        reference_number: Optional[str],
        notes: Optional[str],
        performed_by_user_id: int
    ) -> Item:
        """
        Add stock IN dengan atomic transaction dan audit trail.
        
        Process:
        1. Lock item row di database (prevent concurrent updates)
        2. Validate quantity > 0
        3. Update stock quantity
        4. Record transaction di audit trail
        5. Commit atomically (keduanya succeed atau keduanya fail)
        
        Args:
            item_id: Item ID yang mau di-add stock
            quantity: Jumlah yang ditambah (harus > 0)
            reference_number: PO number, invoice, etc (opsional tapi recommended)
            notes: Additional notes
            performed_by_user_id: User yang perform action
        
        Returns:
            Updated item
        
        Raises:
            ValueError: Jika item tidak ditemukan atau quantity invalid
        
        Why atomic?
            - Item stock dan transaction log HARUS selalu consistent
            - Kalau hanya item diupdate tapi transaction tidak terecord, audit trail broken
            - PostgreSQL transaction semantics guarantee ini dengan ACID
        """
        try:
            # Step 1: Validate quantity
            if quantity <= 0:
                raise ValueError("Quantity harus > 0")
            
            # Step 2: Update stock (dengan locking di dalam function)
            item = await self.item_repo.update_stock(item_id, quantity)
            
            if not item:
                raise ValueError(f"Item {item_id} tidak ditemukan")
            
            # Step 3: Create transaction record
            await self.transaction_repo.create(
                item_id=item_id,
                transaction_type=TransactionType.IN,
                quantity=quantity,
                reference_number=reference_number,
                notes=notes,
                performed_by=performed_by_user_id
            )
            
            # Step 4: Commit (both queries dalam satu transaction)
            await self.session.commit()
            
            # Refresh untuk get updated values
            await self.session.refresh(item, ["category"])
            
            # Broadcast stock update
            await manager.broadcast({
                "type": "STOCK_UPDATE",
                "item_id": item.id,
                "sku": item.sku,
                "name": item.name,
                "quantity_in_stock": item.quantity_in_stock,
                "reorder_level": item.reorder_level,
                "action": "IN",
                "quantity": quantity
            })
            
            return item
            
        except Exception as e:
            # Rollback jika ada error (automatic, tapi explicit untuk clarity)
            await self.session.rollback()
            raise
    
    async def remove_stock(
        self,
        item_id: int,
        quantity: int,
        reference_number: Optional[str],
        notes: Optional[str],
        performed_by_user_id: int
    ) -> Item:
        """
        Remove stock OUT dengan atomic transaction dan audit trail.
        
        Process SAMA SEPERTI add_stock, tapi quantity dikurang.
        
        Business Rules:
        - Tidak boleh stock menjadi negative
        - Minimum validation: qty > 0, available qty >= requested qty
        
        Args:
            item_id: Item yang mau di-remove stock
            quantity: Jumlah yang dikurang (harus > 0)
            reference_number: Sales order, delivery, etc
            notes: Reason for removal
            performed_by_user_id: User yang perform action
        
        Returns:
            Updated item
        
        Raises:
            ValueError: Insufficient stock, item not found, quantity invalid
        
        Why THIS adalah critical yang lu paling perlu locknya:
            - Kalau 2 user simultaneous remove stock dari item yang sama
            - Tanpa locking, BOTH bisa remove beyond available qty
            - Inventory jadi negative (disaster untuk F&B)
        """
        try:
            # Step 1: Validate quantity
            if quantity <= 0:
                raise ValueError("Quantity harus > 0")
            
            # Step 2: Get item dengan row lock
            # INI KUNCI: dengan FOR UPDATE, transaction lain akan WAIT
            item = await self.item_repo.get_for_update(item_id)
            
            if not item:
                raise ValueError(f"Item {item_id} tidak ditemukan")
            
            # Step 3: Check stock availability SETELAH lock acquired
            # Ini dijamin accurate karena row di-lock
            if item.quantity_in_stock < quantity:
                raise ValueError(
                    f"Stok tidak cukup. Diperlukan: {quantity}, "
                    f"Tersedia: {item.quantity_in_stock}"
                )
            
            # Step 4: Update stock via repository (applies locking pattern)
            item = await self.item_repo.update_stock(item_id, -quantity)
            
            # Step 5: Record transaction
            await self.transaction_repo.create(
                item_id=item_id,
                transaction_type=TransactionType.OUT,
                quantity=quantity,
                reference_number=reference_number,
                notes=notes,
                performed_by=performed_by_user_id
            )
            
            # Step 6: Atomic commit
            await self.session.commit()
            await self.session.refresh(item, ["category"])
            
            # Broadcast stock update
            await manager.broadcast({
                "type": "STOCK_UPDATE",
                "item_id": item.id,
                "sku": item.sku,
                "name": item.name,
                "quantity_in_stock": item.quantity_in_stock,
                "reorder_level": item.reorder_level,
                "action": "OUT",
                "quantity": quantity
            })
            
            # Check if low stock
            if item.quantity_in_stock <= item.reorder_level:
                await manager.broadcast({
                    "type": "LOW_STOCK_ALERT",
                    "item_id": item.id,
                    "sku": item.sku,
                    "name": item.name,
                    "quantity_in_stock": item.quantity_in_stock,
                    "reorder_level": item.reorder_level,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            return item
            
        except Exception as e:
            await self.session.rollback()
            raise

    async def get_analytics_metrics(self) -> dict:
        """
        Mengagregasikan data analitik dari database Neon PostgreSQL.
        
        Kalkulasi yang dilakukan:
        1. Total Items (aktif)
        2. Total Stock Volume (aktif)
        3. Total Asset Value: SUM(qty * unit_price)
        4. Low Stock Ratio: Persentase barang di bawah reorder level
        5. Stock Turnover: Jumlah transaksi 7 hari terakhir
        6. Transaction Trends: Total IN dan OUT harian selama 7 hari terakhir
        7. Top Moving Items: 5 barang paling aktif keluar dalam 30 hari terakhir
        """
        # 1, 2, 3. Total Items, Stock, dan Nilai Aset
        stmt = select(
            func.count(Item.id),
            func.sum(Item.quantity_in_stock),
            func.sum(Item.quantity_in_stock * Item.unit_price)
        ).where(Item.is_active == True)
        
        res = await self.session.execute(stmt)
        total_items, total_stock_volume, total_asset_value = res.fetchone()
        
        total_items = total_items or 0
        total_stock_volume = total_stock_volume or 0
        total_asset_value = float(total_asset_value or 0.0)
        
        # 4. Low stock ratio
        low_stock_stmt = select(func.count(Item.id)).where(
            and_(Item.quantity_in_stock < Item.reorder_level, Item.is_active == True)
        )
        low_stock_res = await self.session.execute(low_stock_stmt)
        low_stock_count = low_stock_res.scalar() or 0
        low_stock_ratio = float(low_stock_count / total_items) if total_items > 0 else 0.0
        
        # 5. Stock turnover (Transactions in the last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        turnover_stmt = select(func.count(Transaction.id)).where(
            Transaction.created_at >= seven_days_ago
        )
        turnover_res = await self.session.execute(turnover_stmt)
        stock_turnover = turnover_res.scalar() or 0
        
        # 6. Transaction Trends (7 days IN vs OUT)
        trend_stmt = (
            select(
                cast(Transaction.created_at, Date).label("date"),
                Transaction.transaction_type,
                func.sum(Transaction.quantity)
            )
            .where(Transaction.created_at >= seven_days_ago)
            .group_by(cast(Transaction.created_at, Date), Transaction.transaction_type)
            .order_by(cast(Transaction.created_at, Date))
        )
        trend_res = await self.session.execute(trend_stmt)
        trend_rows = trend_res.all()
        
        # Inisialisasi peta 7 hari terakhir agar data tanggal yang tidak bertransaksi tetap bernilai 0
        trends_map = {}
        for i in range(6, -1, -1):
            d_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            trends_map[d_str] = {"date": d_str, "total_in": 0, "total_out": 0}
            
        for row in trend_rows:
            d_str = row[0].strftime("%Y-%m-%d")
            if d_str in trends_map:
                if row[1] == "IN":
                    trends_map[d_str]["total_in"] = int(row[2] or 0)
                elif row[1] == "OUT":
                    trends_map[d_str]["total_out"] = int(row[2] or 0)
                    
        transaction_trends = list(trends_map.values())
        
        # 7. Top Moving Items (Top 5 barang keluar terbanyak dalam 30 hari terakhir)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        top_stmt = (
            select(
                Transaction.item_id,
                func.sum(Transaction.quantity).label("total_out")
            )
            .where(
                and_(
                    Transaction.transaction_type == "OUT",
                    Transaction.created_at >= thirty_days_ago
                )
            )
            .group_by(Transaction.item_id)
            .order_by(desc("total_out"))
            .limit(5)
        )
        top_res = await self.session.execute(top_stmt)
        top_rows = top_res.all()
        
        top_moving_items = []
        for row in top_rows:
            item_id, total_out = row
            item = await self.item_repo.get_by_id(item_id)
            if item:
                top_moving_items.append({
                    "id": item.id,
                    "name": item.name,
                    "sku": item.sku,
                    "total_out": int(total_out or 0)
                })
                
        return {
            "total_items": total_items,
            "total_stock_volume": total_stock_volume,
            "total_asset_value": total_asset_value,
            "low_stock_ratio": low_stock_ratio,
            "stock_turnover": stock_turnover,
            "transaction_trends": transaction_trends,
            "top_moving_items": top_moving_items
        }
