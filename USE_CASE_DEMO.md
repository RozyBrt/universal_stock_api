# Skenario Penggunaan & Panduan Demo (Use Case & Demo Guide)

Dokumen ini menjelaskan **mengapa** Universal Stock API dibangun, **masalah apa** yang dipecahkannya di dunia nyata, dan **bagaimana cara mendemonstrasikan** penggunaan proyek ini secara menyeluruh.

---

## 1. Latar Belakang Masalah
Banyak bisnis kecil menengah (UKM) seperti toko retail, grosir, atau toko elektronik yang mulai berekspansi dari berjualan *offline* (toko fisik) ke jualan *online* (website e-commerce atau marketplace). 

**Masalah utama mereka adalah Sinkronisasi Stok:**
Jika sebuah barang terjual di toko fisik, stok di website online tidak berkurang secara otomatis. Akibatnya, pelanggan online bisa saja memesan barang yang ternyata sudah habis di gudang, menyebabkan pembatalan pesanan dan kekecewaan pelanggan.

## 2. Solusi: Universal Stock API
Universal Stock API hadir sebagai **Sistem Manajemen Inventaris Terpusat berbasis Cloud (SaaS-like)**. 
Aplikasi ini bukan sekadar alat pencatat stok biasa, melainkan sebuah "Otak Pusat" yang memungkinkan berbagai sistem (Kasir, Website, Aplikasi Mobile) untuk terhubung secara *real-time* ke satu database stok yang sama secara aman.

---

## 3. Skenario Penggunaan (User Journey)
Untuk memahami bagaimana sistem ini bekerja, mari kita gunakan skenario fiktif dengan karakter bernama **Pak Budi**, pemilik "Toko Elektronik Sinar Jaya".

### Fase 1: Setup Awal (Untuk Pengguna Non-Teknis)
Pak Budi adalah pemilik bisnis yang tidak mengerti *coding*. Dia hanya ingin menggunakan sistem yang mudah.
1. **Login:** Pak Budi membuka Dashboard Frontend (Next.js) lewat browser dan login.
2. **Membuat Kategori:** Dia masuk ke menu **Categories**, lalu membuat kategori seperti "Televisi", "Kulkas", dan "Laptop".
3. **Memasukkan Barang:** Dia masuk ke menu **Inventory**, lalu mendaftarkan barang pertamanya: "TV Samsung 32 Inch" dengan kategori "Televisi" dan stok awal sebanyak 15 unit.

### Fase 2: Operasional Harian (Keluar-Masuk Barang)
Sistem digunakan untuk mencatat pergerakan barang sehari-hari.
1. **Stock In (Masuk):** Truk dari pabrik datang membawa 10 unit TV. Pak Budi masuk ke menu **Inventory**, menekan tombol transaksi pada "TV Samsung", memilih aksi *Masuk (+)*, mengisi jumlah 10, dan memberi catatan "Kiriman dari Pabrik". Stok otomatis menjadi 25.
2. **Stock Out (Keluar):** Seorang karyawan tak sengaja memecahkan 1 unit TV. Pak Budi kembali melakukan transaksi dengan aksi *Keluar (-)*, mengisi jumlah 1, dan catatan "Barang rusak". Stok menjadi 24.
3. **Audit Trail:** Kapan pun Pak Budi butuh laporan, dia cukup membuka menu **Transactions** untuk melihat riwayat keluar-masuk barang layaknya buku tabungan bank.

### Fase 3: Ekspansi & Integrasi (Untuk Programmer)
Setahun kemudian, Pak Budi menyewa seorang *programmer freelance* untuk membuat website toko online. Programmer ini butuh akses ke data stok Pak Budi agar website online bisa mengurangi stok otomatis setiap ada pesanan.
1. **Membuat Kunci:** Pak Budi masuk ke menu **API Keys** di Dashboard dan menekan "Create API Key".
2. **Menyerahkan Akses:** Dia menamai kunci itu "Akses Website Online" dan mendapatkan deretan kode rahasia (misal: `sk_live_123...`). Kode ini dia berikan ke si programmer.
3. **Integrasi Sistem:** Programmer tersebut menanamkan API Key itu ke dalam *header* aplikasi buatannya (`X-API-Key`). Sekarang, setiap kali ada pelanggan mengeklik tombol "Beli" di website, website tersebut akan mengirimkan permintaan API ke backend kita (FastAPI). 
4. **Hasil Akhir:** Stok TV Samsung di gudang Pak Budi akan berkurang secara otomatis dari jarak jauh dengan aman, tanpa Pak Budi harus memasukkannya secara manual.

---

## 4. Panduan Simulasi & Demonstrasi
Ikuti langkah-langkah berikut untuk mendemonstrasikan alur kerja sistem secara keseluruhan:

1. **Buka Dashboard (Frontend):** Tunjukkan antarmuka UI yang modern (Next.js) dan jelaskan bahwa ini adalah "Ruang Kendali" bagi pemilik bisnis.
2. **Lakukan Satu Transaksi Manual:** Tambahkan barang baru, lalu lakukan satu transaksi *Stock In* dan *Stock Out* melalui layar Dashboard. Tunjukkan bahwa datanya langsung tersimpan dan terekam di menu *Transactions*.
3. **Pamerkan Fitur API Keys:** Pindah ke layar API Keys. Buat satu API Key baru di depan mereka. Jelaskan konsep Server-to-Server dan mengapa keamanan API Key ini sangat penting (nilai plus untuk *software architecture*).
4. **Simulasi Sistem Eksternal (API Client):** 
   - Buka aplikasi seperti **Postman**, **Insomnia**, atau ekstensi REST API.
   - Anggap aplikasi ini adalah "Aplikasi Kasir" milik Pak Budi.
   - Taruh API Key yang baru dibuat tadi di bagian *Headers* (`X-API-Key: ...`).
   - Tembak *endpoint* `POST /api/v1/transactions` untuk melakukan pengurangan stok.
   - Kembali ke browser (Dashboard Next.js), *refresh* atau perlihatkan bahwa stok barang telah berkurang dan tercatat di riwayat transaksi.
5. **Kesimpulan:** Simulasi ini membuktikan mengapa sistem ini disebut **Universal** Stock API. Sistem tidak hanya berdiri sendiri sebagai satu aplikasi, melainkan dirancang untuk terintegrasi dengan berbagai aplikasi kasir atau website lain secara bersamaan layaknya layanan berskala Enterprise.
