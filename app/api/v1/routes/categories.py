from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.rate_limit import limiter
from app.config import settings
from app.api.v1.dependencies import require_admin
from app.models.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("", response_model=list[CategoryResponse])
@limiter.limit(settings.RATE_LIMIT_CATEGORIES_GET)
async def get_categories(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all categories (Public)"""
    service = CategoryService(db)
    return await service.get_categories(skip=skip, limit=limit)

@router.get("/{category_id}", response_model=CategoryResponse)
@limiter.limit(settings.RATE_LIMIT_CATEGORIES_GET)
async def get_category(request: Request, category_id: int, db: AsyncSession = Depends(get_db)):
    """Get category by ID (Public)"""
    service = CategoryService(db)
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_CATEGORIES_MODIFY)
async def create_category(
    request: Request,
    data: CategoryCreate,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new category (Admin only)"""
    service = CategoryService(db)
    try:
        return await service.create_category(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{category_id}", response_model=CategoryResponse)
@limiter.limit(settings.RATE_LIMIT_CATEGORIES_MODIFY)
async def update_category(
    request: Request,
    category_id: int,
    data: CategoryUpdate,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update category (Admin only)"""
    service = CategoryService(db)
    category = await service.update_category(category_id, data)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(settings.RATE_LIMIT_CATEGORIES_MODIFY)
async def delete_category(
    request: Request,
    category_id: int,
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete category (Admin only)"""
    service = CategoryService(db)
    success = await service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return None
