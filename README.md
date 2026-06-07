# Universal Stock API - Backend

Sistem manajemen inventaris (stock management) tingkat produksi (*production-ready*) dengan arsitektur yang kuat dan aman. Backend ini dibangun menggunakan stack modern berbasis Python untuk menjamin performa, keamanan, serta integritas data yang optimal.

## ✨ Fitur Utama

- **Keamanan Lapis Ganda (Dual Authentication):**
  - **JWT (JSON Web Tokens):** Untuk autentikasi pengguna manusia/operator melalui *Login*.
  - **API Keys:** Manajemen akses yang terpisah untuk integrasi dengan sistem/perangkat pihak ketiga (seperti Aplikasi Mesin Kasir/Point of Sales). Bisa di- *revoke* kapan saja.
- **Role-Based Access Control (RBAC):** Pemisahan hak akses (Admin vs Staf Biasa) untuk membatasi aksi-aksi krusial.
- **Concurrency Safety:** Implementasi fitur *Database Row-Level Locking* (`FOR UPDATE`) pada transaksi pengeluaran stok. Ini menjamin akurasi stok tidak akan pernah menjadi negatif, bahkan ketika puluhan kasir memotong stok barang yang sama di detik yang bersamaan.
- **Audit Trail Penuh:** Setiap perubahan stok (barang masuk/keluar) dicatat dalam tabel transaksi yang mereferensikan ke akun siapa pelakunya. Tidak ada manipulasi "jumlah stok" secara diam-diam.
- **Pagination & Advanced Search:** Endpoint API dirancang untuk menangani jutaan data dengan pagination, serta fitur *Advanced Search* untuk pencarian berbasis nama, kategori, maupun harga.

## 🛠️ Stack Teknologi (Layered Architecture)

Sistem ini menerapkan konsep *Separation of Concerns* untuk memisahkan antara rute, layanan (logika bisnis), dan repositori (basis data):

- **Framework:** FastAPI (Asynchronous)
- **Database:** PostgreSQL
- **ORM / Driver:** SQLAlchemy 2.0 (Async) dengan `asyncpg`
- **Migrasi:** Alembic
- **Validasi Data:** Pydantic v2
- **Enkripsi Password & Hashing:** Passlib & hashlib

## 📂 Struktur Direktori

```text
app/
├── api/v1/          # Kumpulan Router/Endpoint API dan Dependencies
├── core/            # Pengaturan global (config), Security, Exception Handlers
├── models/          # Definisi Tabel (SQLAlchemy Declarative Base) & Pydantic Schemas
├── repositories/    # Logika kueri database (Layer Akses Data)
├── services/        # Logika bisnis inti dan aturan-aturan aplikasi
├── main.py          # Titik masuk (Entry Point) utama FastAPI
└── database.py      # Pengaturan koneksi Async Engine
```

## 🚀 Cara Menjalankan

1. Pastikan Anda memiliki Python 3.9+ dan PostgreSQL yang sedang berjalan.
2. Atur konfigurasi database di file `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/universal_stock_db
   SECRET_KEY=kunci-rahasia-anda
   ```
3. Lakukan Migrasi Database:
   ```bash
   alembic upgrade head
   ```
4. Jalankan *Development Server*:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Buka `http://localhost:8000/docs` untuk menjelajahi *Interactive API Documentation* (Swagger UI).
