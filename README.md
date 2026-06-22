---
title: Universal Stock API
emoji: 📦
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Universal Stock - Enterprise Fullstack Inventory Management System

Sistem manajemen inventaris (stock management) tingkat produksi (*production-ready*) dengan arsitektur tangguh, observabilitas modern, keamanan lapis ganda, dan sinkronisasi real-time dua arah.

Proyek ini menggunakan pemisahan tanggung jawab (*separation of concerns*) yang ketat dengan arsitektur monorepo yang bersih, terbagi atas **Backend (FastAPI)** dan **Frontend (Next.js)**.

---

## 🛠️ Tech Stack

### Backend (Server)
* **Framework:** FastAPI (Asynchronous Python)
* **Database:** PostgreSQL (Driver `asyncpg` asinkronus murni)
* **ORM:** SQLAlchemy 2.0 (Async Style)
* **Migration:** Alembic
* **Validation:** Pydantic v2 (Strict validation)
* **Real-time:** WebSockets Protocol

### Frontend (Client Dashboard)
* **Framework:** Next.js 15+ (App Router, React 19)
* **Language:** TypeScript
* **Styling:** Custom Vanilla CSS (Design System modern bergaya *Glassmorphism* & *Dark Mode*)
* **Testing:** Playwright E2E

---

## ✨ Fitur Unggulan

### 📦 Manajemen Inventaris & Mutasi Aman (*Concurrency Safety*)
* **CRUD Lengkap:** Operasi pembuatan, pembaruan, pembacaan, dan penghapusan (*soft-delete*) untuk Item dan Kategori.
* **Concurrency Safety:** Menggunakan penguncian baris database (`FOR UPDATE` / *Row-Level Locking*) saat pemotongan stok untuk mencegah data tidak konsisten (*race condition*) akibat aksi transaksi stok masuk/keluar secara bersamaan.
* **Audit Trail Penuh:** Mencatat riwayat setiap transaksi mutasi stok beserta identitas pengguna pengubah dan referensi transaksi.

### 🛡️ Keamanan & Pembatasan Akses (*Security & Rate Limiting*)
* **Autentikasi Lapis Ganda:** Mendukung token **JWT** (untuk login pengguna via web dasbor) dan **API Key** (untuk integrasi aplikasi kasir/PIhak Ketiga).
* **Rate Limiting Cerdas:** Melindungi endpoint API kritis dari serangan brute-force atau DDoS dengan pembatasan dinamis (misal: login maks 5/menit, mutasi stok maks 50/menit, dsb).
* **Retry-After Header:** Memberikan informasi waktu tunggu kepada client jika terkena rate limit (HTTP 429).

### ⚡ Komunikasi Real-time (WebSocket)
* **Sinkronisasi Otomatis:** Pembaruan stok pada tabel inventaris frontend dirender secara instan dengan efek transisi visual (`flash-in` hijau/merah) saat pengguna lain melakukan mutasi stok.
* **Toast Notification:** Peringatan instan berupa *low-stock alerts* melayang jika kuantitas barang jatuh di bawah *reorder level*.
* **Isolasi Notifikasi:** Riwayat notifikasi tersimpan secara independen berdasarkan ID Pengguna untuk keamanan privasi multi-user.
* **Auto-Reconnect:** Menangani diskoneksi jaringan dengan mekanisme *exponential backoff*.

### 📊 Observabilitas & Tracing (*Observability*)
* **Structured Logging:** Seluruh aktivitas server dicatat dalam format JSON terstruktur yang siap diintegrasikan dengan ELK Stack atau Datadog.
* **Request Tracing:** Menyematkan `X-Request-ID` unik di setiap request untuk melacak alur *error* dengan cepat.
* **Performance Metric:** Mencatat durasi pemrosesan di setiap endpoint (`duration_ms`) untuk memudahkan identifikasi kemacetan performa (*bottleneck*).

---

## ⚙️ Environment-Specific Configuration

Aplikasi mendukung pemuatan konfigurasi dinamis berdasarkan variabel lingkungan `APP_ENV`. Berkas `.env` default akan dimuat pertama kali, kemudian akan ditimpa secara hierarkis oleh berkas berikut sesuai nilai variabel `APP_ENV`:

* **Development (`APP_ENV=development`)**: Menggunakan [.env.development](file:///d:/Documents/python_projects/universal_stock_api/.env.development) (DEBUG=True).
* **Staging (`APP_ENV=staging`)**: Menggunakan [.env.staging](file:///d:/Documents/python_projects/universal_stock_api/.env.staging).
* **Production (`APP_ENV=production`)**: Menggunakan [.env.production](file:///d:/Documents/python_projects/universal_stock_api/.env.production) (DEBUG=False, token pendek, limit rate ketat).

---

## 🚀 Cara Menjalankan Aplikasi secara Lokal

### Prerequisites
* Python 3.9+
* PostgreSQL dengan database kosong bernama `universal_stock_db`

### 1. Menjalankan Backend (FastAPI)
```bash
# Aktifkan virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/macOS

# Install dependensi
pip install -r requirements.txt

# Lakukan migrasi database menggunakan Alembic
alembic upgrade head

# Jalankan server uvicorn (secara default memuat .env.development jika APP_ENV tidak diatur)
uvicorn app.main:app --reload
```
Akses API Documentation (Swagger UI) di [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Menjalankan Frontend (Next.js)
```bash
cd frontend

# Install dependensi
npm install

# Jalankan development server
npm run dev
```
Buka dasbor di [http://localhost:3000](http://localhost:3000). Gunakan kredensial demo admin:
* **Email:** `demo@example.com`
* **Password:** `Password1`

---

## 🧪 Pengujian Otomatis (Testing)

Proyek ini dilengkapi dengan skenario tes otomatis yang komprehensif dari unit backend hingga antarmuka pengguna frontend.

### 1. Backend Unit Tests (pytest)
Menjalankan tes fungsional API server dan koneksi WebSocket di backend:
```bash
pytest
```

### 2. End-to-End Tests (Playwright)
Tes otomatis E2E mensimulasikan aksi pengguna nyata di browser Chromium untuk menguji autentikasi, operasional inventaris, dan sinkronisasi real-time multi-jendela.
```bash
cd frontend
# Menjalankan tes E2E
npm run test:e2e
```
*Catatan: Tes E2E dikonfigurasi secara sekuensial (`workers: 1`) untuk menjamin tidak ada race condition data pada PostgreSQL.*

---

## 🔌 Dokumentasi Integrasi WebSocket

Untuk menyambungkan client eksternal ke feed real-time stok:

```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("WebSocket Event:", message);
  
  if (message.event === 'STOCK_UPDATE') {
    // Tangani perubahan stok
  }
};
```

---

## 📚 Panduan Tambahan (Extra Guides)

Untuk membantu pemahaman mendalam tentang proyek ini, Anda dapat merujuk ke dokumen panduan berikut:
*   **[Buku Panduan Developer (Junior Guide)](file:///d:/Documents/python_projects/universal_stock_api/JUNIOR_GUIDE.md):** Penjelasan alur data, tech stack, peta struktur folder, aturan penulisan kode (*DOs & DON'Ts*), serta cara memulai bagi pengembang baru atau junior programmer.
*   **[Panduan Admin & Pengguna CLI (Admin Guide)](file:///d:/Documents/python_projects/universal_stock_api/ADMIN.md):** Cara mengaudit akun, mereset password, mengubah hak akses (*role*), serta mengisi data awal database (*seeding*) baik di lokal maupun produksi online.
*   **[Dokumentasi Desain & UI (Design Guide)](file:///d:/Documents/python_projects/universal_stock_api/DESIGN.md):** Informasi sistem visual, skema warna glassmorphism dark-mode, micro-animations, dan grafik SVG interaktif.
*   **[Arsitektur Sistem (Architecture Guide)](file:///d:/Documents/python_projects/universal_stock_api/ARCHITECTURE.md):** Penjelasan detail topologi multi-cloud, penanganan race conditions (*row-level locking*), dan diagram alur sinkronisasi real-time WebSockets.
