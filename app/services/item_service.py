from app.repositories.item_repository import ItemRepository
from app.repositories.transaction_repository import TransactionRepository
from app.models.database import Item, Transaction
from app.models.schemas import ItemCreate, ItemUpdate, TransactionType
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional, List, Tuple

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
        # Check SKU not already exist
        existing = await self.item_repo.get_by_sku(item_data.sku)
        if existing:
            raise ValueError(
                f"SKU '{item_data.sku}' sudah terdaftar. "
                f"Gunakan PATCH untuk update item yang ada."
            )
        
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
        
        return await self.item_repo.update(item_id, **data_to_update)
    
    # ============= DELETE OPERATION =============
    
    async def delete_item(self, item_id: int) -> bool:
        """Soft delete item"""
        return await self.item_repo.delete(item_id)
    
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
            
            return item
            
        except Exception as e:
            await self.session.rollback()
            raise
