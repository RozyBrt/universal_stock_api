import asyncio
import sys
import os

# Menambahkan root folder ke python path agar app module bisa diimport
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cek flag --prod untuk menggunakan database produksi dari .env.production.local
if "--prod" in sys.argv:
    sys.argv.remove("--prod")
    prod_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.production.local")
    if os.path.exists(prod_env_path):
        with open(prod_env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")
        print("[INFO] Menggunakan database PRODUKSI (Neon DB) dari .env.production.local")
    else:
        print("[WARNING] File .env.production.local tidak ditemukan! Menggunakan database lokal.")

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.database import User
from app.core.security import hash_password

async def list_users():
    """Menampilkan daftar seluruh user yang terdaftar di database"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print("\n=== DAFTAR USER ===")
        print(f"{'ID':<5} | {'Username':<15} | {'Email':<30} | {'Role':<10} | {'Status':<10}")
        print("-" * 80)
        for u in users:
            status = "Aktif" if u.is_active else "Nonaktif"
            print(f"{u.id:<5} | {u.username:<15} | {u.email:<30} | {u.role:<10} | {status:<10}")
        print("===================\n")

async def reset_password(email: str, new_password: str):
    """Mereset password user berdasarkan email secara manual di database"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"\n[ERROR] User dengan email '{email}' tidak ditemukan.\n")
            return
        
        hashed = hash_password(new_password)
        user.password_hash = hashed
        await session.commit()
        print(f"\n[SUCCESS] Password untuk user '{user.username}' ({email}) berhasil di-reset!\n")

async def main():
    if len(sys.argv) < 2:
        print("Penggunaan:")
        print("  python scripts/manage_users.py list")
        print("  python scripts/manage_users.py reset <email> <new_password>")
        return

    cmd = sys.argv[1].lower()
    if cmd == "list":
        await list_users()
    elif cmd == "reset":
        if len(sys.argv) < 4:
            print("Error: Argumen kurang. Gunakan: python scripts/manage_users.py reset <email> <new_password>")
            return
        email = sys.argv[2]
        new_pwd = sys.argv[3]
        await reset_password(email, new_pwd)
    else:
        print(f"Error: Perintah '{cmd}' tidak dikenali.")

if __name__ == "__main__":
    # Dukungan Windows event loop policy untuk asyncpg di Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
