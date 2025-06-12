# Citilyst API Services

## Deskripsi

Citilyst adalah platform layanan untuk pelaporan masyarakat yang memungkinkan pengguna melaporkan berbagai masalah seperti pelayanan publik, infrastruktur rusak, tindakan korupsi, lingkungan, dan pelanggaran prosedur kepada instansi pemerintah yang berwenang.

## Struktur Folder

```
├── helpers/               # Fungsi-fungsi pembantu
│   ├── aiohttp.py         # Helper untuk HTTP client
│   ├── cloudinary.py      # Konfigurasi dan fungsi upload Cloudinary
│   ├── common.py          # Fungsi umum yang digunakan di seluruh aplikasi
│   ├── config.py          # Konfigurasi aplikasi
│   ├── cors.py            # Konfigurasi CORS
│   ├── db.py              # Konfigurasi database
│   ├── google_auth.py     # Autentikasi Google
│   ├── jwt.py             # Helper JWT untuk autentikasi
│   ├── log.py             # Konfigurasi logging
│   ├── mailer.py          # Fungsi untuk mengirim email
│   ├── pdf_generator.py   # Generator PDF untuk laporan
│   ├── rate_limiter.py    # Pembatasan rate request
│   ├── redis.py           # Konfigurasi dan fungsi Redis
│   ├── router.py          # Konfigurasi router
│   ├── scheduler.py       # Penjadwalan tugas
│   └── static.py          # Konfigurasi static files
│
├── jobs/                  # Pekerjaan terjadwal
│   └── __init__.py
│
├── middleware/            # Middleware aplikasi
│   └── rbac_middleware.py # Middleware untuk RBAC (Role-Based Access Control)
│
├── models/                # Model data (ORM)
│   ├── district.py        # Model untuk kecamatan
│   ├── feedback_user.py   # Model untuk umpan balik pengguna
│   ├── reports.py         # Model untuk laporan
│   ├── users.py           # Model untuk pengguna
│   └── village.py         # Model untuk kelurahan/desa
│
├── permissions/           # Konfigurasi izin
│   ├── base.py            # Kelas dasar untuk izin
│   ├── model_permission.py# Izin pada level model
│   └── roles.py           # Definisi peran pengguna
│
├── public/                # File statis publik
│   └── index.html         # Halaman landing
│
├── routes/                # Definisi endpoint API
│   ├── auth.py            # Endpoint autentikasi
│   ├── district.py        # Endpoint kecamatan
│   ├── feedback_user.py   # Endpoint umpan balik pengguna
│   ├── reports.py         # Endpoint laporan
│   ├── users.py           # Endpoint pengguna
│   └── villages.py        # Endpoint kelurahan/desa
│
├── schemas/               # Skema validasi data
│   ├── auth.py            # Skema autentikasi
│   ├── district.py        # Skema kecamatan dan kelurahan
│   ├── feedback_user.py   # Skema umpan balik pengguna
│   ├── otp.py             # Skema OTP
│   ├── reports.py         # Skema laporan
│   └── users.py           # Skema pengguna
│
├── services/              # Layanan bisnis
│   ├── auth.py            # Layanan autentikasi
│   ├── district.py        # Layanan kecamatan
│   ├── feedback_user.py   # Layanan umpan balik pengguna
│   ├── reports.py         # Layanan laporan
│   ├── users.py           # Layanan pengguna
│   └── village.py         # Layanan kelurahan/desa
│
├── templates/             # Template HTML
│   ├── email_verification.html   # Template verifikasi email
│   ├── otp_email.html            # Template email OTP
│   ├── report.html               # Template laporan
│   └── status_report_email.html  # Template email status laporan
│
├── tests/                 # Unit tests
│
├── .env                   # File konfigurasi lingkungan
├── .env.example           # Contoh file konfigurasi lingkungan
├── main.py                # Entry point aplikasi
├── Makefile               # Makefile untuk otomatisasi tugas
└── requirements.txt       # Dependensi Python
```

## Fitur Utama

1. **Autentikasi Pengguna**
   - Login/Registrasi via email dan password
   - OAuth dengan Google
   - Sistem OTP untuk verifikasi

2. **Pengelolaan Laporan**
   - Pembuatan laporan dengan kategori
   - Upload gambar ke Cloudinary
   - Generasi PDF laporan
   - Pelacakan status laporan

3. **Pengelolaan Wilayah**
   - Manajemen data kecamatan
   - Manajemen data kelurahan/desa

4. **Sistem Umpan Balik**
   - Pengguna dapat memberikan umpan balik

## Prasyarat

- Python 3.9+
- PostgreSQL
- Redis
- Akun Cloudinary
- Akun Google Cloud Platform (untuk OAuth dan Google Drive)

## Konfigurasi

1. Salin file `.env.example` menjadi `.env` dan sesuaikan nilai-nilai konfigurasi.

```bash
cp .env.example .env
```

2. Install dependensi yang diperlukan

```bash
pip install -r requirements.txt
```

## Menjalankan Aplikasi

### Menjalankan Secara Lokal

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug --reload
```

atau

```bash
make start
```

### Menggunakan Docker (Single Container)

```bash
docker build -f Dockerfile.web -t citilyst-app .
docker run --rm -v ./:/app -p 8000:8000 citilyst-app
```

atau

```bash
make docker-single-build
make docker-single-start
```

### Menggunakan Docker Compose

Untuk membangun dan menjalankan aplikasi beserta database:

```bash
docker compose build
docker compose up -d
```

atau

```bash
make docker-compose-build
make docker-compose-start
```

Untuk menghentikan aplikasi:

```bash
docker compose down
```

atau

```bash
make docker-compose-stop
```

## Dokumentasi API

Setelah menjalankan aplikasi, Anda dapat mengakses dokumentasi Swagger di:
```
http://localhost:8000/docs
```

Dan dokumentasi ReDoc di:
```
http://localhost:8000/redoc
```

