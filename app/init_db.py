import asyncio
from sqlalchemy import text
from app.database import engine, Base
from app.models.database import User, Category, Item, Transaction, ApiKey # Import to register models

async def init_db():
    print("Connecting to database to initialize tables...")
    try:
        async with engine.begin() as conn:
            # Drop all tables if you want a clean start (optional)
            # await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables defined in models
            await conn.run_sync(Base.metadata.create_all)
            
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nTips:")
        print("1. Pastikan PostgreSQL service sudah jalan (Port 5432).")
        print("2. Pastikan database 'universal_stock_db' sudah dibuat.")
        print("3. Cek username/password di file .env.")

if __name__ == "__main__":
    asyncio.run(init_db())
