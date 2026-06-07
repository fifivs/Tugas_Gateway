# 🏦 API Gateway / Integrator UMKM

Middleware orchestrator yang menjadi pintu masuk semua request antar aplikasi dalam ekosistem ekonomi UMKM. Bertanggung jawab untuk routing, validasi token JWT, logging, dan standarisasi komunikasi.

---

## 📋 Daftar Isi
- [Tech Stack](#tech-stack)
- [Struktur Folder](#struktur-folder)
- [Instalasi & Setup](#instalasi--setup)
- [Cara Menjalankan](#cara-menjalankan)
- [API Endpoints](#api-endpoints)
- [Konfigurasi](#konfigurasi)
- [Fitur Utama](#fitur-utama)

---

## 🛠️ Tech Stack

| Kategori | Teknologi |
|----------|-----------|
| **Backend Framework** | FastAPI 0.104+ |
| **Language** | Python 3.9+ |
| **Authentication** | JWT (PyJWT) |
| **Database** | MongoDB Atlas (Cloud) |
| **HTTP Client** | HTTPX (Async) |
| **CORS** | FastAPI CORSMiddleware |
| **Frontend** | HTML5, CSS3, JavaScript Vanilla |
| **Server** | Uvicorn |

### Dependencies
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.4.2
pyjwt==2.8.1
motor==3.3.2
httpx==0.25.1
```

---

## 📁 Struktur Folder

```
Tugas_Gateway/
│
├── main.py                          # Main application (FastAPI entry point)
├── README.md                        # Dokumentasi ini
├── requirements.txt                 # Python dependencies
│
├── models/
│   ├── __init__.py
│   └── schemas.py                  # Pydantic models (RequestFormat, ResponseFormat)
│
├── services/
│   ├── __init__.py
│   ├── jwt_service.py              # JWT token validation & generation
│   ├── log_service.py              # MongoDB logging service
│   └── routing_service.py          # HTTP routing ke SmartBank & apps
│
├── controllers/                     # (Kosong - siap untuk MVC expansion)
│   └── __init__.py
│
├── frontend/
│   ├── landing.html                # Landing page publik
│   ├── login.html                  # Login page
│   ├── index.html                  # Dashboard (setelah login)
│   ├── style.css                   # Global CSS
│   ├── landing.css                 # Landing page styling
│   └── script.js                   # Frontend JavaScript
│
├── Context/                         # Dokumentasi requirement tugas
│   ├── Deskripsi Aplikasi RPL - 1. Deskripsi Aplikasi.csv
│   ├── Kebutuhan Fungsional Aplikasi RPL - 2. Fungsional.csv
│   ├── Aturan Pengerjaan Tugas Besar RPL - 4. Aturan Pengerjaan.csv
│   ├── Dokumentasi Desain RPL - 5. Dokumentasi.csv
│   └── Aturan Keuangan Dalam Ekosistem RPL - 6. Aturan Keuangan.csv
│
└── venv/                           # Python virtual environment
    └── (dependencies installed here)
```

---

## ⚙️ Instalasi & Setup

### Prerequisites
- Python 3.9 atau lebih tinggi
- Virtual Environment (venv)
- MongoDB Atlas account (untuk logging)
- Internet connection (untuk koneksi ke MongoDB Atlas)

### Step 1: Clone / Download Project
```bash
cd "c:\semester 4\Rekayasa Perangkat Lunak II\Tugas_Gateway"
```

### Step 2: Buat Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Aktivasi Virtual Environment
**Windows (PowerShell):**
```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& ".\venv\Scripts\Activate.ps1")
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

Jika belum ada `requirements.txt`, buat dengan:
```bash
pip install fastapi uvicorn pydantic pyjwt motor httpx
pip freeze > requirements.txt
```

### Step 5: Konfigurasi MongoDB Atlas
Edit `services/log_service.py`, ganti:
```python
MONGO_DETAILS = "mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?appName=Cluster0"
```

### Step 6: Konfigurasi URL SmartBank
Edit `services/routing_service.py`, sesuaikan port SmartBank:
```python
URL_SMARTBANK = "http://127.0.0.1:8000/smartbank/pembayaran_transaksi"  # Ganti port jika perlu
```

---

## 🚀 Cara Menjalankan

### Mode Development (dengan auto-reload)
```bash
uvicorn main:app --reload --port 8001
```

### Mode Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

**Output Expected:**
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Application startup complete
```

### Buka di Browser
- **Landing Page:** http://127.0.0.1:8001/
- **Login Page:** http://127.0.0.1:8001/login
- **Dashboard:** http://127.0.0.1:8001/dashboard
- **API Docs:** http://127.0.0.1:8001/docs (Swagger UI)

---

## 🔌 API Endpoints

### 1️⃣ Routing API (Main Orchestrator)
```
POST /integrator/routing_api
```
**Request Body:**
```json
{
  "user_id": "user123",
  "parameter": {
    "token": "jwt_token_here",
    "amount": 100000,
    "recipient_id": "user456"
  }
}
```

**Response:**
```json
{
  "status": "sukses",
  "data": {
    "integrator_note": "Request divalidasi & log tersimpan di Atlas",
    "fee_diambil": 500,
    "respons_dari_smartbank": {...}
  }
}
```

---

### 2️⃣ Validasi Request
```
POST /integrator/validasi_request
```
**Deskripsi:** Validasi token JWT tanpa forward ke apps lain

**Request Body:**
```json
{
  "user_id": "user123",
  "parameter": {
    "token": "jwt_token_here"
  }
}
```

---

### 3️⃣ Logging
```
POST /integrator/logging
```
**Deskripsi:** Mencatat request ke MongoDB Atlas

**Request Body:**
```json
{
  "user_id": "user123",
  "parameter": {
    "endpoint": "/marketplace/checkout",
    "action": "purchase"
  }
}
```

---

### 4️⃣ Biaya Layanan Integrasi
```
POST /integrator/biaya_layanan_integrasi
```
**Deskripsi:** Hitung fee gateway 0.5% per transaksi

**Request Body:**
```json
{
  "user_id": "user123",
  "parameter": {
    "amount": 100000
  }
}
```

**Response:**
```json
{
  "status": "sukses",
  "data": {
    "jumlah_transaksi": 100000,
    "fee_gateway_persen": "0.5%",
    "fee_gateway_nominal": 500,
    "jumlah_diteruskan": 99500,
    "keterangan": "Fee dipotong otomatis dari setiap transaksi via API Gateway"
  }
}
```

---

### Utility Endpoints
```
GET /generate_token_tester/{user_id}
```
**Deskripsi:** Generate dummy JWT token untuk testing (berlaku 30 menit)

**Response:**
```json
{
  "token_buat_ngetes": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

## ⚙️ Konfigurasi

### JWT Secret Key
File: `services/jwt_service.py`
```python
SECRET_KEY = "kunci_rahasia_umkm_rpl2"
ALGORITHM = "HS256"
```
⚠️ Ubah ke secret key yang lebih aman di production!

### MongoDB Connection
File: `services/log_service.py`
```python
MONGO_DETAILS = "mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0"
database = client.TugasGateway  # Nama database
log_collection = database.get_collection("logs_transaksi")  # Nama collection
```

### CORS Settings
File: `main.py`
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ubah ke domain spesifik di production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### SmartBank URL
File: `services/routing_service.py`
```python
URL_SMARTBANK = "http://127.0.0.1:8000/smartbank/pembayaran_transaksi"
```

---

## ✨ Fitur Utama

### 1. JWT Token Validation
- Validasi token dari request sebelum forward
- Response jelas jika token invalid/expired
- Generate dummy token untuk testing

### 2. MongoDB Logging
- Setiap request dicatat ke MongoDB Atlas (cloud)
- Timestamp otomatis
- Termasuk user_id, endpoint, dan request data

### 3. Fee Calculation
- Hitung biaya layanan gateway 0.5% per transaksi
- Transparan dalam response
- Dipotong otomatis

### 4. API Routing
- Forward request ke SmartBank (payments)
- Forward request ke apps lain (Marketplace, POS, etc)
- Standardized request/response format

### 5. Frontend Pages
- **Landing Page** - Public info
- **Login Page** - UI login (backend di SmartBank)
- **Dashboard** - Monitoring (belum fully implemented)

---

## 📊 Request/Response Format

### Standard Request Format
```json
{
  "user_id": "string (required)",
  "parameter": {
    "token": "string (required)",
    "amount": "number (optional)",
    "recipient_id": "string (optional)",
    "additional_field": "any (optional)"
  }
}
```

### Standard Response Format
```json
{
  "status": "sukses | gagal",
  "data": {
    "pesan": "string",
    "jumlah_transaksi": "number (optional)",
    "fee_gateway_nominal": "number (optional)",
    "respons_dari_smartbank": "object (optional)"
  }
}
```

---

## 🧪 Testing Workflow

### 1. Generate Token
```bash
curl http://127.0.0.1:8001/generate_token_tester/user123
```

### 2. Test Validasi Request
```bash
curl -X POST http://127.0.0.1:8001/integrator/validasi_request \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "parameter": {
      "token": "PASTE_TOKEN_HERE"
    }
  }'
```

### 3. Test Routing API
```bash
curl -X POST http://127.0.0.1:8001/integrator/routing_api \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "parameter": {
      "token": "PASTE_TOKEN_HERE",
      "amount": 100000
    }
  }'
```

---

## 📝 Persyaratan Requirement (Checklist)

- ✅ Routing API - Routing request antar service
- ✅ Validasi request - Validasi token JWT
- ✅ Logging - Mencatat request ke MongoDB Atlas
- ✅ Biaya layanan integrasi - Fee 0.5% per transaksi
- ✅ MVC/Clean Code - Architecture terstruktur
- ✅ Validasi input - Token, user_id validation
- ✅ Integrasi SmartBank - Forward ke SmartBank
- ✅ JSON Format - Request/Response standardized
- ⚠️ Input validation lengkap - Perlu tambahan untuk amount & user_id

---

## 🐛 Troubleshooting

### Error: ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Error: MongoDB Connection Failed
- Cek internet connection
- Verify MongoDB Atlas connection string
- Cek IP whitelist di MongoDB Atlas

### Error: SmartBank Connection Failed
- Verify SmartBank URL di `routing_service.py`
- Pastikan SmartBank sudah running di port yang benar

### Port Already in Use
```bash
uvicorn main:app --reload --port 8002
```

---

## 👨‍💻 Struktur File Penting

| File | Fungsi |
|------|--------|
| `main.py` | Entry point FastAPI, semua endpoints didefinisikan |
| `models/schemas.py` | Pydantic models untuk request/response validation |
| `services/jwt_service.py` | JWT token handling |
| `services/log_service.py` | MongoDB logging & fee calculation |
| `services/routing_service.py` | HTTP routing ke SmartBank |
| `frontend/*.html` | UI pages |
| `frontend/script.js` | Frontend logic |

---

## 📚 Referensi Eksternal

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [Motor (Async MongoDB)](https://motor.readthedocs.io/)
- [HTTPX Documentation](https://www.python-httpx.org/)

---

## 👥 Tim Pengembang

**Mata Kuliah:** Rekayasa Perangkat Lunak II  
**Dosen:** M. Yusril Helmi Setyawan, S.Kom., M.Kom.  
**Kelompok:** 7 - API Gateway / Integrator UMKM

---

## 📄 License

Project ini adalah bagian dari tugas besar mata kuliah RPL II.

---

**Last Updated:** May 2026  
**Version:** 1.0.0
