# Universal Stock - Fullstack Inventory Management

Sistem manajemen inventaris (stock management) tingkat produksi (*production-ready*) dengan arsitektur yang kuat dan aman. Repositori ini merupakan sebuah *Monorepo* yang berisi aplikasi **Backend (FastAPI)** dan **Frontend (Next.js)** secara bersamaan.

## 🌟 Tentang Proyek Ini

Sistem ini dibangun untuk menjamin performa, keamanan lapis ganda, serta integritas data yang optimal, dilengkapi dengan Dasbor Web modern untuk kemudahan operasional.

### 🖥️ Frontend (Web Dashboard)
Antarmuka pengguna dibangun menggunakan **Next.js (React)** dengan desain modern, cepat, dan responsif.

**Fitur Unggulan Frontend:**
- Dasbor pemantauan stok *real-time* dengan peringatan stok menipis.
- *My Log*: Pelacakan aktivitas pribadi dan riwayat transaksi pengguna.
- Antarmuka pembuatan dan pencabutan *API Key* secara mandiri.
- Terletak penuh di dalam folder `frontend/`.

👉 **[Baca selengkapnya di Dokumentasi Frontend](frontend/README.md)**

### ⚙️ Backend (API Server)
Sistem *backend* API dibangun menggunakan **Python & FastAPI** dengan penanganan asinkronus (*async*) murni.

**Fitur Unggulan Backend:**
- **Keamanan Lapis Ganda:** Mendukung token *JWT* (untuk *User Login*) dan *API Keys* (untuk integrasi aplikasi mesin kasir pihak ketiga).
- **Concurrency Safety:** Menggunakan penguncian baris database (*Row-Level Locking*) `FOR UPDATE` saat memotong stok untuk mencegah stok minus akibat aksi bersamaan.
- **Audit Trail Penuh:** Mencatat secara ketat siapa pengguna yang menambah atau mengurangi stok barang.

---

## 🛠️ Stack Teknologi Backend

- **Framework:** FastAPI (Asynchronous)
- **Database:** PostgreSQL
- **ORM / Driver:** SQLAlchemy 2.0 (Async) dengan `asyncpg`
- **Migrasi:** Alembic
- **Validasi Data:** Pydantic v2

## 📂 Struktur Direktori Utama

```text
/
├── app/             # Kode sumber Backend (API Routes, Services, Models)
├── frontend/        # Kode sumber Frontend Dasbor (Next.js App Router)
├── migrations/      # Berkas migrasi skema database (Alembic)
└── README.md        # Dokumentasi repositori utama (Berkas ini)
```

## 🚀 Cara Menjalankan Backend (Server)

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

*(Catatan: Untuk panduan menjalankan Web Frontend, silakan buka `frontend/README.md`)*
