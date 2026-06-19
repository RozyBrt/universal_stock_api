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

Sebuah script utilitas Python telah disediakan untuk melakukan pengecekan akun dan mereset password secara manual langsung pada database PostgreSQL (Neon DB).

### Prasyarat
Pastikan Anda menjalankan script ini dari **direktori root proyek** (di mana file `.env` berada) agar konfigurasi database termuat dengan benar:

### A. Menampilkan Semua User Terdaftar
Untuk melihat ID, username, email, role, dan status aktif seluruh akun:
```bash
python scripts/manage_users.py list
```

### B. Mereset Password User
Untuk mereset password pengguna secara aman (script akan otomatis meng-hash password baru dan menyimpannya ke database):
```bash
python scripts/manage_users.py reset <email_user> <password_baru>
```

**Contoh:**
```bash
python scripts/manage_users.py reset demo@example.com PasswordBaru123
```

---

## 3. Data Awal Database (`scripts/seed_test_db.py`)

Untuk mengisi database kosong dengan data pengujian (seperti kategori default, barang awal, dan satu akun admin default):
```bash
python scripts/seed_test_db.py
```
*Catatan: Script ini sangat berguna saat Anda baru saja melakukan migrasi database baru (`alembic upgrade head`) untuk memastikan sistem memiliki data awal yang siap diuji.*
