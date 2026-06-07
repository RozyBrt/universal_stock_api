# Universal Stock - Frontend Web Dashboard

Proyek Antarmuka Pengguna (Frontend) untuk **Universal Stock API**, sebuah sistem manajemen inventaris canggih dan modern. Web Dasbor ini dibangun dengan memprioritaskan estetika, kecepatan *(responsiveness)*, serta kemudahan navigasi bagi pengguna.

## ✨ Fitur Utama

- **Dashboard Real-time:** Menampilkan antarmuka bersih dan minimalis untuk memantau performa inventaris secara menyeluruh.
- **Manajemen Kategori Terpusat:** Layar khusus untuk menambah, mengubah, dan menghapus kategori barang (*Categories Management*).
- **Inventaris Dinamis:** Lacak barang dengan sistem *Advanced Pagination* dan fitur Filter Pintar untuk segera menemukan produk yang ada di rak, lengkap dengan status peringatan jika stok menipis.
- **Aktivitas Pribadi (My Log):** Melacak jejak audit / log operasi yang HANYA pernah dilakukan oleh akun Anda untuk pertanggungjawaban pribadi.
- **Pembangkit Kunci API (Developer Keys):** Antarmuka aman untuk men- *generate* (menghasilkan) atau men- *revoke* (mematikan) akses API Key sistem ketiga langsung dari halaman profil.
- **Micro-Animations & Visual Cues:** Seluruh proses memiliki *feedback* visual, animasi halus pada *hover*, serta desain komponen bergaya premium.

## 🛠️ Stack Teknologi

- **Framework:** Next.js (React)
- **Styling:** CSS Modular / Vanilla CSS (dengan desain *custom-tailored* menghindari komponen *generic*)
- **Routing:** Next.js App Router API
- **Ikon:** Lucide React Icon Library
- **State Management:** React Hooks (useState, useEffect) dipadukan dengan API wrapper berbasis fetch.

## 📂 Struktur Penting

```text
app/
├── (auth)/          # Rute terkait akses masuk (Login, Registrasi)
├── (dashboard)/     # Halaman utama (Inventory, Categories, Transactions, API Keys)
├── components/      # Komponen UI yang dapat digunakan kembali (Sidebar, Navbar, Modal)
├── lib/             # Konfigurasi & Klien API Fetcher yang terpusat (apiClient.ts)
└── globals.css      # Variabel warna dasar (Design System) dan Global Utilities
```

## 🚀 Cara Menjalankan (Development)

1. Pastikan Anda sudah menginstal Node.js (versi 18+ direkomendasikan).
2. Instal semua dependensi proyek:
   ```bash
   npm install
   ```
3. Sesuaikan URL Backend (jika perlu) di dalam berkas konfigurasi *Frontend* (`lib/apiClient.ts` atau `next.config.js`).
4. Jalankan *Development Server*:
   ```bash
   npm run dev
   ```
5. Buka `http://localhost:3000` di peramban Anda untuk mulai mengeksplorasi panel kontrol.
