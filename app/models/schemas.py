from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ============= AUTH SCHEMAS =============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

# ============= PAGINATION SCHEMAS =============

class PaginationMetadata(BaseModel):
    """Metadata untuk pagination"""
    total: int = Field(..., description="Total items dalam database")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Ada page berikutnya atau tidak")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "skip": 0,
                "limit": 50,
                "has_next": True
            }
        }

# ============= CATEGORY SCHEMAS =============

class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Electronics",
                "slug": "electronics",
                "description": "Electronic items",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = None
    is_active: Optional[bool] = None

# ============= ITEM SCHEMAS =============

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, description="Item name")
    description: Optional[str] = Field(None, description="Detailed description")
    sku: str = Field(..., min_length=3, max_length=100, description="Stock Keeping Unit (harus unique)")
    category_id: int = Field(..., gt=0, description="Category ID yang sudah exist")
    unit_price: float = Field(..., gt=0, description="Price per unit (dalam currency)")
    quantity_in_stock: int = Field(default=0, ge=0, description="Initial quantity")
    reorder_level: Optional[int] = Field(default=10, ge=0, description="Alert threshold")
    
    @validator('sku')
    def sku_format(cls, v):
        # SKU should be alphanumeric with hyphens/underscores
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('SKU hanya boleh alphanumeric, hyphen, underscore')
        return v.upper()

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = None
    unit_price: Optional[float] = Field(None, gt=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class ItemResponse(BaseModel):
    """Response schema untuk single item"""
    id: int
    name: str
    sku: str
    description: Optional[str]
    category_id: int
    category: Optional[CategoryResponse] = None  # ← Eager loaded dari repository
    unit_price: float
    quantity_in_stock: int
    reorder_level: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Laptop ThinkPad X1",
                "sku": "LAP-001",
                "description": "Business laptop",
                "category_id": 2,
                "category": {
                    "id": 2,
                    "name": "Electronics",
                    "slug": "electronics",
                    "description": None,
                    "is_active": True,
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00"
                },
                "unit_price": 12000000,
                "quantity_in_stock": 15,
                "reorder_level": 5,
                "is_active": True,
                "created_at": "2024-01-20T14:25:00",
                "updated_at": "2024-01-20T14:25:00"
            }
        }

# ============= PAGINATED RESPONSE SCHEMAS =============

class PaginatedItemResponse(BaseModel):
    """
    Paginated response untuk list items.
    
    Format ini standard di API design. Frontend bisa:
    - Render items list
    - Show pagination controls (current page, total pages)
    - Implement infinite scroll (gunakan skip untuk next request)
    """
    data: List[ItemResponse] = Field(..., description="Array of items")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": 1,
                        "name": "Laptop ThinkPad X1",
                        "sku": "LAP-001",
                        "description": "Business laptop",
                        "category_id": 2,
                        "category": None,
                        "unit_price": 12000000,
                        "quantity_in_stock": 15,
                        "reorder_level": 5,
                        "is_active": True,
                        "created_at": "2024-01-20T14:25:00",
                        "updated_at": "2024-01-20T14:25:00"
                    },
                    {
                        "id": 2,
                        "name": "USB Cable",
                        "sku": "CAB-001",
                        "description": "Type-C cable 2m",
                        "category_id": 3,
                        "category": None,
                        "unit_price": 50000,
                        "quantity_in_stock": 200,
                        "reorder_level": 50,
                        "is_active": True,
                        "created_at": "2024-01-18T09:15:00",
                        "updated_at": "2024-01-18T09:15:00"
                    }
                ],
                "pagination": {
                    "total": 150,
                    "skip": 0,
                    "limit": 50,
                    "has_next": True
                }
            }
        }

class PaginatedLowStockResponse(BaseModel):
    """Paginated response untuk low stock alerts"""
    data: List[ItemResponse]
    pagination: PaginationMetadata

# ============= TRANSACTION SCHEMAS =============

class TransactionType(str, Enum):
    IN = "IN"      # Stock masuk (purchase, return, etc)
    OUT = "OUT"    # Stock keluar (sales, usage, etc)

class TransactionCreate(BaseModel):
    item_id: int = Field(..., gt=0)
    transaction_type: TransactionType
    quantity: int = Field(..., gt=0, description="Quantity yang ditransaction")
    reference_number: Optional[str] = Field(
        None,
        min_length=3,
        description="PO/SO/Delivery number untuk traceability"
    )
    notes: Optional[str] = Field(None, description="Additional notes/reason")

class TransactionResponse(BaseModel):
    id: int
    item_id: int
    transaction_type: TransactionType
    quantity: int
    reference_number: Optional[str]
    notes: Optional[str]
    performed_by: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "item_id": 1,
                "transaction_type": "OUT",
                "quantity": 5,
                "reference_number": "SO-2024-001",
                "notes": "Sold to customer ABC",
                "performed_by": 3,
                "created_at": "2024-01-20T14:25:00"
            }
        }

class PaginatedTransactionResponse(BaseModel):
    data: List[TransactionResponse]
    pagination: PaginationMetadata

# ============= STOCK OPERATION SCHEMAS =============

class StockOperationRequest(BaseModel):
    """Request body untuk add_stock / remove_stock"""
    quantity: int = Field(..., gt=0, description="Quantity yang di-add/remove")
    reference_number: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="PO number, SO number, atau reference apapun"
    )
    notes: Optional[str] = Field(None, description="Reason atau additional info")

class StockOperationResponse(BaseModel):
    """Response dari stock operation (return updated item)"""
    item: ItemResponse = Field(..., description="Updated item after operation")
    transaction_id: int = Field(..., description="Transaction ID yang di-record")
    message: str = Field(..., description="Operation success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item": {
                    "id": 1,
                    "name": "Laptop ThinkPad X1",
                    "sku": "LAP-001",
                    "description": "Business laptop",
                    "category_id": 2,
                    "category": None,
                    "unit_price": 12000000,
                    "quantity_in_stock": 10,  # Changed from 15
                    "reorder_level": 5,
                    "is_active": True,
                    "created_at": "2024-01-20T14:25:00",
                    "updated_at": "2024-01-20T14:25:10"
                },
                "transaction_id": 1,
                "message": "Stock removed successfully"
            }
        }

# ============= ERROR RESPONSE SCHEMAS =============

class ErrorDetail(BaseModel):
    """Standardized error response"""
    code: str = Field(..., description="Error code untuk client handling")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(..., description="When error occurred")
    path: Optional[str] = Field(None, description="API endpoint yang error")

class ValidationErrorDetail(BaseModel):
    field: str
    message: str

class ValidationError(BaseModel):
    code: str = "VALIDATION_ERROR"
    message: str = "Invalid request data"
    errors: List[ValidationErrorDetail]
    timestamp: datetime
