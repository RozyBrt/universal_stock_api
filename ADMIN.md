# 🛡️ Administration & User Management Guide

Dokumen ini menjelaskan tata cara mengaudit akun pengguna, melakukan reset password manual, dan mengelola data awal (*database seeding*) pada sistem **Universal Stock API**.

---

## 1. Filosofi Keamanan: Password Hashing

Untuk mematuhi standar keamanan aplikasi modern:
*   Semua password pengguna **tidak pernah disimpan dalam bentuk teks biasa (plain text)**.
*   Password di-hash secara satu arah menggunakan algoritma **Bcrypt** (menggunakan package `passlib`) sebelum disimpan ke database.
*   **Dampaknya:** Baik Anda sebagai administrator, pengembang, maupun database administrator tidak dapat melihat atau membaca password asli pengguna. Jika pengguna lupa passwordnya, password tersebut harus di-reset dengan nilai baru.

---

## 2. Alat Manajemen Pengguna CLI (`scripts/manage_users.py`)

Sebuah script utilitas Python telah disediakan untuk melakukan audit akun, reset password, mengubah role, dan mengaktifkan/menonaktifkan status akun langsung pada database PostgreSQL.

### Prasyarat & Mode Target Database
Secara default, script akan berjalan pada database **Lokal** Anda. Namun, Anda dapat menargetkan database **Produksi** online menggunakan flag `--prod` (mengambil kredensial aman dari file rahasia lokal `.env.production.local`):

*   **Mode Database Lokal:** Cukup jalankan perintah biasa.
*   **Mode Database Produksi:** Tambahkan flag `--prod` di akhir perintah.

---

### Perintah yang Tersedia:

### A. Menampilkan Semua User Terdaftar (`list`)
Untuk melihat ID, username, email, role, dan status aktif seluruh akun:
```bash
# Target Lokal
python scripts/manage_users.py list

# Target Produksi Online
python scripts/manage_users.py list --prod
```

### B. Mereset Password User (`reset`)
Untuk mengubah password pengguna (script otomatis meng-hash password baru menggunakan Bcrypt):
```bash
# Target Lokal
python scripts/manage_users.py reset <email_user> <password_baru>

# Target Produksi Online
python scripts/manage_users.py reset <email_user> <password_baru> --prod
```

**Contoh:**
```bash
python scripts/manage_users.py reset demo@example.com PasswordBaru123 --prod
```

### C. Mengubah Peran User (`role`)
Untuk mempromosikan atau mendemosikan hak akses user (`admin` atau `user`):
```bash
# Target Lokal
python scripts/manage_users.py role <email_user> <admin|user>

# Target Produksi Online
python scripts/manage_users.py role <email_user> <admin|user> --prod
```

**Contoh:**
```bash
python scripts/manage_users.py role demo@example.com admin --prod
```

### D. Mengubah Status Keaktifan Akun (`status`)
Untuk memblokir (deactivate) atau mengaktifkan kembali (activate) akun pengguna:
```bash
# Target Lokal
python scripts/manage_users.py status <email_user> <activate|deactivate>

# Target Produksi Online
python scripts/manage_users.py status <email_user> <activate|deactivate> --prod
```

**Contoh:**
```bash
python scripts/manage_users.py status demo@example.com deactivate --prod
```

---

## 3. Data Awal Database (`scripts/seed_test_db.py`)

Untuk mengisi database kosong dengan data pengujian (seperti kategori default, barang awal, dan satu akun admin default):
```bash
python scripts/seed_test_db.py
```
*Catatan: Script ini sangat berguna saat Anda baru saja melakukan migrasi database baru (`alembic upgrade head`) untuk memastikan sistem memiliki data awal yang siap diuji.*
