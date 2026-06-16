"""
Seed script untuk E2E tests di CI.
Membuat demo admin user, categories, dan initial items
yang dibutuhkan oleh Playwright tests.

Usage: python scripts/seed_test_db.py
"""
import asyncio
import sys
import os

# Tambahkan root project ke sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.database import User, Category, Item
from app.core.security import hash_password


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:asdasdasd@localhost:5432/universal_stock_db"
)

DEMO_ADMIN = {
    "username": "demoadmin",
    "email": "demo@example.com",
    "password": "Password1",
    "full_name": "Demo Admin",
    "role": "admin",
    "is_active": True,
}

DEMO_CATEGORIES = [
    {
        "name": "General",
        "slug": "general",
        "description": "General items category",
        "is_active": True,
    },
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic devices and components",
        "is_active": True,
    },
]

# Item ini diperlukan oleh websocket.spec.ts yang langsung membaca
# baris pertama di tabel inventaris tanpa membuat item sendiri.
DEMO_ITEMS = [
    {
        "name": "Seed Item A",
        "sku": "SEED-ITEM-001",
        "description": "Initial item seeded for E2E tests",
        "unit_price": 10000,
        "quantity_in_stock": 50,
        "reorder_level": 10,
        "is_active": True,
    },
]


async def seed():
    """Create demo admin user, categories, and items if they don't exist yet."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # --- 1. Seed demo admin user ---
        result = await session.execute(
            select(User).where(User.email == DEMO_ADMIN["email"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"[seed] Demo user '{DEMO_ADMIN['email']}' already exists — skipping.")
            user_id = existing_user.id
        else:
            user = User(
                username=DEMO_ADMIN["username"],
                email=DEMO_ADMIN["email"],
                password_hash=hash_password(DEMO_ADMIN["password"]),
                full_name=DEMO_ADMIN["full_name"],
                role=DEMO_ADMIN["role"],
                is_active=DEMO_ADMIN["is_active"],
            )
            session.add(user)
            await session.flush()  # flush untuk mendapatkan user.id sebelum commit
            user_id = user.id
            print(f"[seed] ✅ Demo user '{DEMO_ADMIN['email']}' created successfully.")

        # --- 2. Seed categories ---
        category_id = None
        for cat_data in DEMO_CATEGORIES:
            result = await session.execute(
                select(Category).where(Category.slug == cat_data["slug"])
            )
            existing_cat = result.scalar_one_or_none()

            if existing_cat:
                print(f"[seed] Category '{cat_data['name']}' already exists — skipping.")
                if category_id is None:
                    category_id = existing_cat.id
            else:
                category = Category(
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    description=cat_data["description"],
                    is_active=cat_data["is_active"],
                )
                session.add(category)
                await session.flush()
                if category_id is None:
                    category_id = category.id
                print(f"[seed] ✅ Category '{cat_data['name']}' created successfully.")

        # --- 3. Seed initial items (needed by websocket.spec.ts) ---
        for item_data in DEMO_ITEMS:
            result = await session.execute(
                select(Item).where(Item.sku == item_data["sku"])
            )
            existing_item = result.scalar_one_or_none()

            if existing_item:
                print(f"[seed] Item '{item_data['sku']}' already exists — skipping.")
            else:
                item = Item(
                    name=item_data["name"],
                    sku=item_data["sku"],
                    description=item_data["description"],
                    category_id=category_id,
                    unit_price=item_data["unit_price"],
                    quantity_in_stock=item_data["quantity_in_stock"],
                    reorder_level=item_data["reorder_level"],
                    is_active=item_data["is_active"],
                    created_by=user_id,
                )
                session.add(item)
                print(f"[seed] ✅ Item '{item_data['name']}' ({item_data['sku']}) created successfully.")

        await session.commit()

    await engine.dispose()
    print("[seed] ✅ Database seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
