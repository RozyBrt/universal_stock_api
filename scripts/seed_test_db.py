"""
Seed script untuk E2E tests di CI.
Membuat demo admin user dan initial categories yang dibutuhkan oleh Playwright tests.

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

from app.models.database import User, Category
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


async def seed():
    """Create demo admin user and initial categories if they don't exist yet."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # --- Seed demo admin user ---
        result = await session.execute(
            select(User).where(User.email == DEMO_ADMIN["email"])
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"[seed] Demo user '{DEMO_ADMIN['email']}' already exists — skipping.")
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
            await session.commit()
            print(f"[seed] ✅ Demo user '{DEMO_ADMIN['email']}' created successfully.")

        # --- Seed categories ---
        for cat_data in DEMO_CATEGORIES:
            result = await session.execute(
                select(Category).where(Category.slug == cat_data["slug"])
            )
            existing_cat = result.scalar_one_or_none()

            if existing_cat:
                print(f"[seed] Category '{cat_data['name']}' already exists — skipping.")
            else:
                category = Category(
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    description=cat_data["description"],
                    is_active=cat_data["is_active"],
                )
                session.add(category)
                print(f"[seed] ✅ Category '{cat_data['name']}' created successfully.")

        await session.commit()

    await engine.dispose()
    print("[seed] ✅ Database seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())
