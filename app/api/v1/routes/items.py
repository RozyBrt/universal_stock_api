from fastapi import APIRouter, Depends, Query, Path, status, Request
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter
from app.config import settings
from app.api.v1.dependencies import get_current_user, require_admin
from app.models.schemas import (
    ItemCreate, ItemUpdate, ItemResponse, PaginatedItemResponse,
    StockOperationRequest, StockOperationResponse,
    PaginatedLowStockResponse
)
from app.services.item_service import ItemService
from app.models.database import User
from app.database import get_db
from app.core.exceptions import (
    ItemNotFoundException,
    InsufficientStockException,
    InvalidInputException,
    DuplicateSKUException,
    StockMovementFailedException,
    InternalServerErrorException
)

router = APIRouter(prefix="/items", tags=["items"])

# ============= GET ALL ITEMS (PAGINATED) =============

@router.get(
    "",
    response_model=PaginatedItemResponse,
    summary="List all items",
    responses={
        200: {
            "description": "Successfully retrieved paginated items",
            "content": {
                "application/json": {
                    "example": {
                        "data": [],
                        "pagination": {
                            "total": 100,
                            "skip": 0,
                            "limit": 50,
                            "has_next": True
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": "Internal server error",
                            "timestamp": "2024-01-21T10:30:00Z",
                            "path": "/api/v1/items"
                        }
                    }
                }
            }
        }
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_GET)
async def get_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=500, description="Items per page (max 500)"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of active items.
    
    **Query Parameters:**
    - `skip`: Number of items to skip (untuk pagination)
    - `limit`: Number of items per page (default 50, max 500)
    
    **Returns:**
    - Paginated items dengan category relationship eager-loaded
    - Pagination metadata untuk UI rendering
    
    **Error Responses:**
    - 500: Database atau server error
    
    **Example Request:**
GET /api/v1/items?skip=0&limit=25
    """
    try:
        service = ItemService(db)
        items, total = await service.list_items(skip=skip, limit=limit)
        
        return PaginatedItemResponse(
            data=items,
            pagination={
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total
            }
        )
    except Exception as e:
        # Catch unexpected errors dan convert ke standardized response
        raise InternalServerErrorException(
            message=f"Error fetching items: {str(e)}"
        )

# ============= SEARCH ITEMS (ADVANCED FILTERING) =============

@router.get(
    "/search",
    response_model=PaginatedItemResponse,
    summary="Search items with filters",
    responses={
        200: {"description": "Search results"},
        400: {"description": "Invalid search parameters"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_SEARCH)
async def search_items(
    q: Optional[str] = Query(None, min_length=2, max_length=100, description="Search by name or SKU"),
    category_id: Optional[int] = Query(None, gt=0, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced search dengan multiple filters.
    
    **Query Parameters:**
    - `q`: Search term (name or SKU, case-insensitive)
    - `category_id`: Filter by specific category
    - `min_price`: Filter items >= min_price
    - `max_price`: Filter items <= max_price
    - `low_stock_only`: Show items di bawah reorder_level
    - `skip`, `limit`: Pagination parameters
    
    **Example Request:**
GET /api/v1/items/search?q=laptop&low_stock_only=true&min_price=1000000
    
    **Returns:**
    Paginated search results dengan pagination metadata
    """
    try:
        # Validate price range
        if min_price and max_price and min_price > max_price:
            raise InvalidInputException(
                field="price_range",
                message="min_price tidak boleh lebih besar dari max_price",
                details={"min_price": min_price, "max_price": max_price}
            )
        
        service = ItemService(db)
        items, total = await service.search_items(
            search_term=q,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            low_stock_only=low_stock_only,
            skip=skip,
            limit=limit
        )
        
        return PaginatedItemResponse(
            data=items,
            pagination={
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total
            }
        )
    except InvalidInputException:
        raise  # Re-raise validation errors
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Search failed: {str(e)}"
        )

# ============= GET LOW STOCK ITEMS =============

@router.get(
    "/alerts/low-stock",
    response_model=PaginatedLowStockResponse,
    summary="Get low stock items",
    responses={
        200: {"description": "Low stock items"},
        401: {"description": "Unauthorized"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_GET)
async def get_low_stock_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get items dengan stock di bawah reorder_level.
    
    **Authentication:** Required
    
    **Returns:**
    Items yang perlu reorder dengan pagination metadata
    
    **Use Case:**
    - Inventory dashboard alerts
    - Stock replenishment planning
    """
    try:
        service = ItemService(db)
        items, total = await service.get_low_stock_items(skip=skip, limit=limit)
        
        return PaginatedLowStockResponse(
            data=items,
            pagination={
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total
            }
        )
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error fetching low stock items: {str(e)}"
        )

# ============= GET ITEM BY ID =============

@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get item by ID",
    responses={
        200: {"description": "Item found"},
        404: {"description": "Item not found"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_GET)
async def get_item(
    item_id: int = Path(..., gt=0, description="Item ID"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single item detail by ID.
    
    **Path Parameters:**
    - `item_id`: ID of the item to retrieve
    
    **Returns:**
    Complete item object dengan category relationship
    
    **Errors:**
    - 404: Item tidak ditemukan
    """
    try:
        service = ItemService(db)
        item = await service.get_item_by_id(item_id)
        
        if not item:
            raise ItemNotFoundException(item_id)
        
        return item
    except ItemNotFoundException:
        raise  # Re-raise not found errors
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error fetching item: {str(e)}"
        )

# ============= CREATE ITEM (ADMIN ONLY) =============

@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new item",
    responses={
        201: {"description": "Item created successfully"},
        400: {"description": "Invalid input or duplicate SKU"},
        401: {"description": "Unauthorized"},
        403: {"description": "Permission denied (admin only)"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_CREATE)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(require_admin),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new item dengan initial stock.
    
    **Authentication:** Required
    **Authorization:** Admin role
    
    **Request Body:**
```json
    {
        "name": "Laptop ThinkPad X1",
        "sku": "LAP-001",
        "category_id": 2,
        "unit_price": 12000000,
        "quantity_in_stock": 10,
        "reorder_level": 5,
        "description": "Business laptop"
    }
```
    
    **Returns:**
    Created item dengan auto-generated ID dan timestamps
    
    **Errors:**
    - 400: Invalid input data atau SKU already exists
    - 403: User tidak punya admin role
    - 409: SKU sudah terdaftar
    """
    try:
        service = ItemService(db)
        item = await service.create_item(item_data, created_by_user_id=current_user.id)
        return item
        
    except ValueError as e:
        error_msg = str(e)
        
        # Detect specific error types
        if "SKU" in error_msg and ("already exists" in error_msg or "sudah terdaftar" in error_msg):
            raise DuplicateSKUException(item_data.sku)
        elif "price" in error_msg.lower():
            raise InvalidInputException(
                field="unit_price",
                message=error_msg
            )
        else:
            raise InvalidInputException(
                field="item",
                message=error_msg
            )
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error creating item: {str(e)}"
        )

# ============= UPDATE ITEM (ADMIN ONLY) =============

@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Update item",
    responses={
        200: {"description": "Item updated"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
        403: {"description": "Permission denied"},
        404: {"description": "Item not found"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_UPDATE)
async def update_item(
    item_id: int = Path(..., gt=0),
    item_data: ItemUpdate = None,
    current_user: User = Depends(require_admin),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update item fields (name, price, reorder_level, etc).
    
    **Note:** Untuk update stock, gunakan `/add-stock` atau `/remove-stock`
    
    **Returns:**
    Updated item object
    """
    try:
        service = ItemService(db)
        item = await service.update_item(item_id, item_data)
        
        if not item:
            raise ItemNotFoundException(item_id)
        
        return item
    except ItemNotFoundException:
        raise
    except ValueError as e:
        raise InvalidInputException(
            field="item",
            message=str(e)
        )
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error updating item: {str(e)}"
        )

# ============= DELETE ITEM (ADMIN ONLY) =============

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    responses={
        204: {"description": "Item deleted"},
        401: {"description": "Unauthorized"},
        403: {"description": "Permission denied"},
        404: {"description": "Item not found"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_DELETE)
async def delete_item(
    item_id: int = Path(..., gt=0),
    current_user: User = Depends(require_admin),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete item (mark as inactive).
    
    **Note:** Item data tetap tersimpan di database (audit trail)
    """
    try:
        service = ItemService(db)
        success = await service.delete_item(item_id)
        
        if not success:
            raise ItemNotFoundException(item_id)
        
        return None
    except ItemNotFoundException:
        raise
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error deleting item: {str(e)}"
        )

# ============= ADD STOCK (AUTHENTICATED) =============

@router.post(
    "/{item_id}/add-stock",
    response_model=StockOperationResponse,
    summary="Add item stock",
    responses={
        200: {"description": "Stock added"},
        400: {"description": "Invalid input or item not found"},
        401: {"description": "Unauthorized"},
        404: {"description": "Item not found"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_STOCK)
async def add_stock(
    item_id: int = Path(..., gt=0, description="Item ID"),
    operation: StockOperationRequest = None,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Add stock (IN transaction) dengan audit trail.
    
    **Authentication:** Required
    
    **Request Body:**
```json
    {
        "quantity": 20,
        "reference_number": "PO-2024-001",
        "notes": "Purchase from supplier XYZ"
    }
```
    
    **Returns:**
    - Updated item dengan new quantity
    - Transaction ID untuk reference
    - Success message
    
    **Errors:**
    - 400: Invalid quantity atau item not found
    - 404: Item tidak ditemukan
    
    **Example:**
POST /api/v1/items/1/add-stock
{
    "quantity": 20,
    "reference_number": "PO-2024-001"
}
    """
    try:
        # Validate quantity
        if operation.quantity <= 0:
            raise InvalidInputException(
                field="quantity",
                message="Quantity harus > 0"
            )
        
        service = ItemService(db)
        item = await service.add_stock(
            item_id=item_id,
            quantity=operation.quantity,
            reference_number=operation.reference_number,
            notes=operation.notes,
            performed_by_user_id=current_user.id
        )
        
        # Get transaction ID (get latest transaction untuk item ini)
        transaction = await service.transaction_repo.get_latest_by_item(item_id)
        
        return StockOperationResponse(
            item=item,
            transaction_id=transaction.id if transaction else 0,
            message=f"Stock ditambah {operation.quantity} unit. Stok sekarang: {item.quantity_in_stock}"
        )
        
    except InvalidInputException:
        raise
    except ItemNotFoundException:
        raise
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise ItemNotFoundException(item_id)
        else:
            raise StockMovementFailedException(
                operation="add-stock",
                reason=error_msg
            )
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error adding stock: {str(e)}"
        )

# ============= REMOVE STOCK (AUTHENTICATED) - CRITICAL FOR CONCURRENCY =============

@router.post(
    "/{item_id}/remove-stock",
    response_model=StockOperationResponse,
    summary="Remove item stock",
    responses={
        200: {"description": "Stock removed"},
        400: {"description": "Insufficient stock atau invalid input"},
        401: {"description": "Unauthorized"},
        404: {"description": "Item not found"},
        500: {"description": "Server error"}
    }
)
@limiter.limit(settings.RATE_LIMIT_ITEMS_STOCK)
async def remove_stock(
    item_id: int = Path(..., gt=0, description="Item ID"),
    operation: StockOperationRequest = None,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Remove stock (OUT transaction) dengan row-level locking.
    
    **CRITICAL:** Menggunakan database-level locking (FOR UPDATE) untuk prevent race condition.
    Ini guarantee inventory accuracy bahkan saat concurrent requests.
    
    **Authentication:** Required
    
    **Request Body:**
```json
    {
        "quantity": 5,
        "reference_number": "SO-2024-001",
        "notes": "Sold to customer ABC"
    }
```
    
    **Returns:**
    - Updated item dengan new quantity
    - Transaction ID untuk reference
    - Success message
    
    **Errors:**
    - 400: Insufficient stock atau invalid quantity
    - 404: Item tidak ditemukan
    
    **Concurrency Guarantee:**
    Jika 2 requests concurrent mencoba remove stock dari item yang sama:
    - Request 1: Acquire row lock, validate stock, update, commit
    - Request 2: WAIT untuk row lock release, then validate (fail jika insufficient)
    - Result: Tidak bisa negative stock
    
    **Example:**
POST /api/v1/items/1/remove-stock
{
    "quantity": 5,
    "reference_number": "SO-2024-001",
    "notes": "Customer order"
}
    """
    try:
        # Validate quantity
        if operation.quantity <= 0:
            raise InvalidInputException(
                field="quantity",
                message="Quantity harus > 0"
            )
        
        service = ItemService(db)
        item = await service.remove_stock(
            item_id=item_id,
            quantity=operation.quantity,
            reference_number=operation.reference_number,
            notes=operation.notes,
            performed_by_user_id=current_user.id
        )
        
        # Get transaction ID
        transaction = await service.transaction_repo.get_latest_by_item(item_id)
        
        return StockOperationResponse(
            item=item,
            transaction_id=transaction.id if transaction else 0,
            message=f"Stock dikurangi {operation.quantity} unit. Sisa stok: {item.quantity_in_stock}"
        )
        
    except InvalidInputException:
        raise
    except ItemNotFoundException:
        raise
    except ValueError as e:
        error_msg = str(e)
        
        # Detect specific error types
        if "not found" in error_msg.lower():
            raise ItemNotFoundException(item_id)
        elif "Stok tidak cukup" in error_msg or "Insufficient stock" in error_msg:
            # Parse error message untuk extract numbers
            available = 0
            if "Tersedia:" in error_msg:
                try: available = int(error_msg.split("Tersedia:")[1].strip())
                except: pass
            elif "Available:" in error_msg:
                try: available = int(error_msg.split("Available:")[1].strip())
                except: pass

            raise InsufficientStockException(
                required=operation.quantity,
                available=available,
                item_id=item_id
            )
        else:
            raise StockMovementFailedException(
                operation="remove-stock",
                reason=error_msg
            )
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error removing stock: {str(e)}"
        )

# ============= GET ITEMS BY CATEGORY =============

@router.get(
    "/category/{category_id}",
    response_model=PaginatedItemResponse,
    summary="Get items by category"
)
@limiter.limit(settings.RATE_LIMIT_CATEGORIES_GET)
async def get_items_by_category(
    category_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get items filtered by specific category dengan pagination.
    """
    try:
        service = ItemService(db)
        items, total = await service.get_items_by_category(
            category_id=category_id,
            skip=skip,
            limit=limit
        )
        
        if total == 0:
            raise ItemNotFoundException(category_id)
        
        return PaginatedItemResponse(
            data=items,
            pagination={
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total
            }
        )
    except ItemNotFoundException:
        raise
    except Exception as e:
        raise InternalServerErrorException(
            message=f"Error fetching items: {str(e)}"
        )
