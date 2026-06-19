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

async def change_role(email: str, new_role: str):
    """Mengubah role user (misal: 'admin' atau 'user')"""
    new_role = new_role.lower()
    if new_role not in ["admin", "user"]:
        print(f"\n[ERROR] Role '{new_role}' tidak valid. Role yang diizinkan: admin, user.\n")
        return
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"\n[ERROR] User dengan email '{email}' tidak ditemukan.\n")
            return
        
        user.role = new_role
        await session.commit()
        print(f"\n[SUCCESS] Role untuk user '{user.username}' ({email}) berhasil diubah menjadi '{new_role}'!\n")

async def change_status(email: str, action: str):
    """Mengaktifkan atau menonaktifkan status user"""
    action = action.lower()
    if action not in ["activate", "deactivate"]:
        print(f"\n[ERROR] Aksi '{action}' tidak valid. Gunakan: activate atau deactivate.\n")
        return
        
    is_active = (action == "activate")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"\n[ERROR] User dengan email '{email}' tidak ditemukan.\n")
            return
        
        user.is_active = is_active
        await session.commit()
        status_text = "AKTIF" if is_active else "NONAKTIF"
        print(f"\n[SUCCESS] Status user '{user.username}' ({email}) berhasil diubah menjadi '{status_text}'!\n")

async def main():
    if len(sys.argv) < 2:
        print("Penggunaan:")
        print("  python scripts/manage_users.py list")
        print("  python scripts/manage_users.py reset <email> <new_password>")
        print("  python scripts/manage_users.py role <email> <admin|user>")
        print("  python scripts/manage_users.py status <email> <activate|deactivate>")
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
    elif cmd == "role":
        if len(sys.argv) < 4:
            print("Error: Argumen kurang. Gunakan: python scripts/manage_users.py role <email> <admin|user>")
            return
        email = sys.argv[2]
        new_role = sys.argv[3]
        await change_role(email, new_role)
    elif cmd == "status":
        if len(sys.argv) < 4:
            print("Error: Argumen kurang. Gunakan: python scripts/manage_users.py status <email> <activate|deactivate>")
            return
        email = sys.argv[2]
        action = sys.argv[3]
        await change_status(email, action)
    else:
        print(f"Error: Perintah '{cmd}' tidak dikenali.")

if __name__ == "__main__":
    # Dukungan Windows event loop policy untuk asyncpg di Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
