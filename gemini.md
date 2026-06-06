# Panduan AI (AI Rules) untuk Universal Stock API

File ini berisi panduan, konteks arsitektur, dan standar penulisan kode untuk asisten AI (seperti saya) yang membantu pengembangan proyek `universal_stock_api`. Selalu ikuti panduan ini saat menulis, memodifikasi, atau memberikan saran kode.

## 1. Konteks Proyek
- **Nama Proyek:** Universal Stock API
- **Deskripsi:** Sistem manajemen inventaris (stock management) backend tingkat produksi (*production-ready*) dengan dukungan autentikasi ganda (JWT & API Key), safety concurrency, dsb.
- **Stack Backend:** Python, FastAPI, SQLAlchemy 2.0 (Async), Alembic, Pydantic v2.
- **Database:** PostgreSQL (menggunakan driver `asyncpg`).
- **Frontend:** Next.js (berada di folder `frontend/`).

## 2. Arsitektur Backend (Layered Architecture)
Proyek ini menggunakan pemisahan tanggung jawab (*separation of concerns*) yang ketat. Jangan mencampur logika!
- **`app/api/v1/routes/`**: Hanya berisi definisi endpoint API. Tugas router hanya menerima *request*, memanggil *service*, dan mengembalikan *response*.
- **`app/api/v1/dependencies.py`**: Tempat untuk fungsi *dependency injection* FastAPI, seperti validasi pengguna, token, dan otorisasi.
- **`app/core/`**: Menyimpan konfigurasi aplikasi (`settings`), penanganan *error* kustom (*exception handlers*), fungsi middleware, dan enkripsi.
- **`app/models/`**: Menyimpan definisi entitas tabel database menggunakan SQLAlchemy Declarative Base.
- **`app/repositories/`**: Layer Data Access. Semua *query* database (CRUD) WAJIB diletakkan di sini.
- **`app/services/`**: Layer Logika Bisnis. Service akan menerima data dari router, melakukan perhitungan/validasi kompleks, memanggil repository, dan mengembalikan hasil.

## 3. Standar Penulisan Kode (Coding Guidelines)

### A. FastAPI & Asynchronous
- Selalu gunakan `async def` untuk *endpoints*, *dependencies*, *services*, dan metode di *repositories*.
- Jangan ada operasi *blocking* yang berjalan di main thread.

### B. Database & SQLAlchemy 2.0
- Jangan gunakan pola lama (`session.query()`). Selalu gunakan gaya 2.0: `await db.execute(select(Model).where(...))` lalu panggil `scalar_one_or_none()` atau `scalars().all()`.
- Untuk memuat data berelasi dengan cepat (eager loading), gunakan `options(selectinload(...))` agar tidak terjadi *Lazy Loading Exception* di mode async.
- Session database (`AsyncSession`) dipanggil dari `get_db` dependency.

### C. Error Handling
- Hindari penggunaan `raise HTTPException` secara manual di dalam layer Service atau Repository.
- Gunakan `AppException` (dan class turunannya) yang di-import dari `app.core.exceptions`. Error ini secara otomatis di-handle oleh *exception handler* global di `main.py` sehingga format respons error tetap standar.

### D. Pydantic v2
- Selalu patuhi standar Pydantic v2.
- Gunakan `.model_dump()` bukan `.dict()`.
- Gunakan `Model.model_validate(obj)` bukan `Model.from_orm(obj)`.

### E. Security & Auth
- Lindungi *endpoint* dengan melakukan injeksi dependency seperti `Depends(get_current_user)` atau `Depends(require_admin)` di deklarasi *route*.

### F. Tipisasi (Type Hints) & Dokumentasi
- *Type hints* bersifat **Wajib** pada parameter dan *return type* di semua fungsi: `def do_something(param: str) -> bool:`.
- Berikan docstring singkat yang menjelaskan alur fungsi tersebut.
