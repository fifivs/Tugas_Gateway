# 📋 Analisis Pelanggaran Prinsip SOLID — Project Tugas Gateway

**Mata Kuliah:** Rekayasa Perangkat Lunak II  
**Tugas:** P5.1 — Prinsip SOLID  
**Project:** API Gateway / Integrator UMKM  
**Kelompok:** Gateway  

---

## Daftar Isi

1. [Pelanggaran 1 — SRP: `log_service.py` God Module](#pelanggaran-1--srp-log_servicepy-god-module)
2. [Pelanggaran 2 — SRP: `main.py` Menangani Terlalu Banyak Hal](#pelanggaran-2--srp-mainpy-menangani-terlalu-banyak-hal)
3. [Pelanggaran 3 — SRP: Fungsi `autentikasi_user()` Multi-Tanggung Jawab](#pelanggaran-3--srp-fungsi-autentikasi_user-multi-tanggung-jawab)
4. [Pelanggaran 4 — OCP: Routing Table Hardcoded di `routing_service.py`](#pelanggaran-4--ocp-routing-table-hardcoded-di-routing_servicepy)
5. [Pelanggaran 5 — OCP: Fee Gateway Hardcoded 0.5%](#pelanggaran-5--ocp-fee-gateway-hardcoded-05)
6. [Pelanggaran 6 — OCP: Mapping Akses Endpoint Hardcoded di `cek_akses_app()`](#pelanggaran-6--ocp-mapping-akses-endpoint-hardcoded-di-cek_akses_app)
7. [Pelanggaran 7 — LSP: Penanganan Error Duplikat di `backtracking_route()`](#pelanggaran-7--lsp-penanganan-error-duplikat-di-backtracking_route)
8. [Pelanggaran 8 — ISP: `RequestFormat` Terlalu Generik untuk Semua Endpoint](#pelanggaran-8--isp-requestformat-terlalu-generik-untuk-semua-endpoint)
9. [Pelanggaran 9 — DIP: Koneksi Database Langsung Tanpa Abstraksi](#pelanggaran-9--dip-koneksi-database-langsung-tanpa-abstraksi)
10. [Pelanggaran 10 — DIP: Secret Key JWT Hardcoded di Modul](#pelanggaran-10--dip-secret-key-jwt-hardcoded-di-modul)
11. [Ringkasan & Kesimpulan](#ringkasan-pelanggaran)

---

## Pelanggaran 1 — SRP: `log_service.py` God Module

### Prinsip yang Dilanggar
**Single Responsibility Principle (SRP)**

> *"Sebuah class/modul hanya boleh punya satu alasan untuk berubah."*

### Penjelasan Pelanggaran
File `services/log_service.py` memiliki **937 baris** dan menangani **7+ tanggung jawab berbeda** sekaligus:

| # | Tanggung Jawab | Fungsi Terkait |
|---|---------------|----------------|
| 1 | Konfigurasi database | `DB_CONFIG`, `get_conn()` |
| 2 | Inisialisasi tabel | `init_db()`, `init_backtracking_table()`, `init_financial_table()` |
| 3 | Logging transaksi | `catat_log_mongo()`, `catat_request_log()`, `catat_health_log()` |
| 4 | Sistem pricing/paket | `get_all_paket()`, `registrasi_app()`, `cek_akses_app()` |
| 5 | Manajemen quota | `kurangi_quota()`, `tambah_fee_app()` |
| 6 | Pembukuan keuangan | `get_financial_ledger()`, `add_financial_entry()`, `get_financial_summary()` |
| 7 | Autentikasi user | `autentikasi_user()` |

Ini adalah contoh klasik **God Module** — satu file yang "tahu segalanya dan melakukan segalanya."

### Potongan Kode yang Melanggar

```python
# services/log_service.py — 937 baris, 7+ tanggung jawab!

# Tanggung Jawab 1: Konfigurasi Database
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "db": "tugasgateaway",
}

# Tanggung Jawab 2: Inisialisasi Tabel (50+ baris membuat 5 tabel)
async def init_db():
    ...
async def init_backtracking_table():
    ...
async def init_financial_table():
    ...

# Tanggung Jawab 3: Logging
async def catat_log_mongo(user_id, endpoint, data_tambahan):
    ...
async def catat_request_log(user_id, source_app, endpoint, ...):
    ...

# Tanggung Jawab 4: Pricing
async def get_all_paket():
    ...
async def registrasi_app(app_name, nama_paket):
    ...
async def cek_akses_app(api_key, endpoint):
    ...

# Tanggung Jawab 5: Quota
async def kurangi_quota(api_key):
    ...
async def tambah_fee_app(api_key, fee):
    ...

# Tanggung Jawab 6: Pembukuan Keuangan
async def get_financial_ledger():
    ...
async def add_financial_entry(...):
    ...
async def get_financial_summary():
    ...

# Tanggung Jawab 7: Autentikasi User
async def autentikasi_user(username, password_raw, ip_address, user_agent):
    ...
```

### Saran Refactor

Pecah `log_service.py` menjadi beberapa modul terpisah:

```
services/
├── db_config.py          → Konfigurasi & koneksi database
├── log_service.py        → Hanya fungsi logging
├── pricing_service.py    → Paket harga & registrasi app
├── quota_service.py      → Manajemen quota
├── financial_service.py  → Pembukuan & neraca
└── auth_service.py       → Autentikasi user
```

---

## Pelanggaran 2 — SRP: `main.py` Menangani Terlalu Banyak Hal

### Prinsip yang Dilanggar
**Single Responsibility Principle (SRP)**

### Penjelasan Pelanggaran
File `main.py` (675 baris) tidak hanya berisi definisi endpoint, tapi juga memuat berbagai tanggung jawab lain yang seharusnya terpisah:

| # | Tanggung Jawab | Baris |
|---|---------------|-------|
| 1 | Rate Limiter | 40–60 |
| 2 | Input Validation | 67–80 |
| 3 | Model Data (harusnya di `models/`) | 135–146 |
| 4 | Auth Dependency | 89–108 |
| 5 | Static File Serving (14 endpoint) | 126–210 |
| 6 | Business Logic Endpoint | 216–675 |

### Potongan Kode yang Melanggar

```python
# main.py — Campur aduk antara utilitas, model, dan endpoint

# ❌ Tanggung Jawab 1: Rate Limiter (harusnya di middleware/)
_rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_MAX    = 30
RATE_LIMIT_WINDOW = 60

def check_rate_limit(identifier: str):
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    _rate_limit_store[identifier] = [
        ts for ts in _rate_limit_store[identifier] if ts > window_start
    ]
    count = len(_rate_limit_store[identifier])
    if count >= RATE_LIMIT_MAX:
        reset_in = int(_rate_limit_store[identifier][0] + RATE_LIMIT_WINDOW - now)
        return False, f"Rate limit tercapai! ..."
    _rate_limit_store[identifier].append(now)
    return True, f"OK ({count + 1}/{RATE_LIMIT_MAX})"

# ❌ Tanggung Jawab 2: Validasi Input (harusnya di utils/)
def validasi_amount(raw_amount):
    try:
        amount = float(raw_amount)
    except (TypeError, ValueError):
        return False, "Amount harus berupa angka.", 0.0
    if amount < 0:
        return False, "Amount tidak boleh negatif.", 0.0
    if amount > 1_000_000_000:
        return False, "Amount melebihi batas maksimal sistem.", 0.0
    return True, "OK", amount

# ❌ Tanggung Jawab 3: Model Data (harusnya di models/schemas.py)
class LoginCredentials(BaseModel):
    username: str
    password: str

class FinancialEntrySchema(BaseModel):
    tipe: str
    kategori: str
    deskripsi: str
    jumlah: float
    user_id: str
    tanggal: str = None

# ❌ Tanggung Jawab 4: Auth Dependency (harusnya di middleware/)
def cek_role(required_roles: list):
    def _dependency(authorization: Optional[str] = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, ...)
        token = authorization.split(" ", 1)[1]
        auth = verifikasi_token(token)
        ...
    return _dependency
```

### Saran Refactor

```
project/
├── main.py                   → Hanya app init & route registration
├── middleware/
│   ├── rate_limiter.py       → check_rate_limit()
│   └── auth.py               → cek_role()
├── utils/
│   └── validators.py         → validasi_amount()
├── models/
│   └── schemas.py            → Semua model Pydantic
└── routes/
    ├── routing_routes.py     → Endpoint routing
    ├── pricing_routes.py     → Endpoint pricing
    ├── financial_routes.py   → Endpoint financial
    └── static_routes.py      → Endpoint halaman HTML
```

---

## Pelanggaran 3 — SRP: Fungsi `autentikasi_user()` Multi-Tanggung Jawab

### Prinsip yang Dilanggar
**Single Responsibility Principle (SRP)**

### Penjelasan Pelanggaran
Fungsi `autentikasi_user()` melakukan **4 hal sekaligus** dalam satu fungsi, padahal masing-masing adalah tanggung jawab berbeda yang bisa berubah secara independen.

### Potongan Kode yang Melanggar

```python
# services/log_service.py — baris 868-937

async def autentikasi_user(username: str, password_raw: str, ip_address: str = None, user_agent: str = None):
    import bcrypt, json
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:

            # ❌ Tanggung Jawab 1: Query user dari database
            await cur.execute("""
                SELECT u.id, u.username, u.email, u.password_hash, u.full_name, u.status, r.nama_role
                FROM users u JOIN roles r ON u.role_id = r.id
                WHERE u.username = %s
            """, (username,))
            user = await cur.fetchone()

            if not user:
                return {"sukses": False, "pesan": "Username tidak ditemukan."}

            # ❌ Tanggung Jawab 2: Verifikasi password + konversi format hash
            pw_input_bytes = password_raw.encode('utf-8')
            db_hash = user["password_hash"]
            if db_hash.startswith('$2y$'):
                db_hash = '$2b$' + db_hash[4:]   # Konversi format PHP → Python
            pw_hash_bytes = db_hash.encode('utf-8')
            if not bcrypt.checkpw(pw_input_bytes, pw_hash_bytes):
                return {"sukses": False, "pesan": "Password salah."}

            # ❌ Tanggung Jawab 3: Update last_login
            await cur.execute("""
                UPDATE users SET last_login = %s WHERE id = %s
            """, (datetime.now(), user["id"]))

            # ❌ Tanggung Jawab 4: Catat log aktivitas login
            detail_log = json.dumps({
                "ip": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.now().isoformat()
            })
            await cur.execute("""
                INSERT INTO user_activity_log (user_id, username, aksi, detail, ip_address)
                VALUES (%s, %s, 'login', %s, %s)
            """, (user["id"], user["username"], detail_log, ip_address))

        conn.close()
```

### Saran Refactor

```python
# Pecah menjadi fungsi-fungsi kecil dengan 1 tanggung jawab masing-masing

async def cari_user_by_username(username: str) -> dict:
    """Tanggung Jawab 1: Hanya query user dari database"""
    conn = await get_conn()
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT ... FROM users WHERE username = %s", (username,))
        return await cur.fetchone()

def verifikasi_password(password_raw: str, password_hash: str) -> bool:
    """Tanggung Jawab 2: Hanya verifikasi password bcrypt"""
    if password_hash.startswith('$2y$'):
        password_hash = '$2b$' + password_hash[4:]
    return bcrypt.checkpw(password_raw.encode('utf-8'), password_hash.encode('utf-8'))

async def update_last_login(user_id: int):
    """Tanggung Jawab 3: Hanya update timestamp last_login"""
    conn = await get_conn()
    async with conn.cursor() as cur:
        await cur.execute("UPDATE users SET last_login = %s WHERE id = %s", (datetime.now(), user_id))
    conn.close()

async def catat_aktivitas_login(user_id: int, username: str, ip: str, user_agent: str):
    """Tanggung Jawab 4: Hanya catat log aktivitas"""
    conn = await get_conn()
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO user_activity_log ...", (...))
    conn.close()

async def autentikasi_user(username, password_raw, ip_address, user_agent):
    """Orchestrator — memanggil fungsi-fungsi di atas (SRP compliant)"""
    user = await cari_user_by_username(username)
    if not user:
        return {"sukses": False, "pesan": "Username tidak ditemukan."}
    if not verifikasi_password(password_raw, user["password_hash"]):
        return {"sukses": False, "pesan": "Password salah."}
    await update_last_login(user["id"])
    await catat_aktivitas_login(user["id"], username, ip_address, user_agent)
    return {"sukses": True, "pesan": "Login berhasil!", "user": {...}}
```

---

## Pelanggaran 4 — OCP: Routing Table Hardcoded di `routing_service.py`

### Prinsip yang Dilanggar
**Open/Closed Principle (OCP)**

> *"Modul harus terbuka untuk ekstensi, tertutup untuk modifikasi."*

### Penjelasan Pelanggaran
Untuk menambah aplikasi baru ke ekosistem, developer harus **memodifikasi langsung 3 dictionary** di dalam `routing_service.py`. Setiap penambahan app = mengubah source code yang sudah berjalan.

### Potongan Kode yang Melanggar

```python
# services/routing_service.py — baris 8-35
# ❌ Harus edit file ini setiap kali ada app baru!

APP_URLS = {
    "smartbank":    "http://127.0.0.1:8000",   # Kelompok 1
    "marketplace":  "http://127.0.0.1:8002",   # Kelompok 2
    "pos":          "http://127.0.0.1:8003",   # Kelompok 3
    "supplierhub":  "http://127.0.0.1:8004",   # Kelompok 4
    "logistikita":  "http://127.0.0.1:8005",   # Kelompok 5
    "umkminsight":  "http://127.0.0.1:8006",   # Kelompok 6
    # Kalau ada app baru (kelompok 7?) → harus masuk sini dan edit
}

APP_DEFAULT_ENDPOINTS = {
    "smartbank":    "/smartbank/pembayaran_transaksi",
    "marketplace":  "/marketplace/checkout",
    # ... harus ditambah manual juga di sini
}

APP_INFO = {
    "smartbank":    {"kelompok": "Kelompok 1", "peran": "Core banking"},
    # ... harus ditambah manual juga di sini
}

# Dan di ROUTE_CANDIDATES juga harus ditambah! (baris 109-140)
ROUTE_CANDIDATES = {
    "smartbank": [
        {"label": "primary", "url": "http://127.0.0.1:8000", ...},
        # ...
    ],
    # ← App baru harus ditambah di sini juga
}
```

### Saran Refactor

```python
# Gunakan file konfigurasi eksternal atau database — tidak perlu ubah kode!

# config/app_routes.json
{
  "smartbank": {
    "url": "http://127.0.0.1:8000",
    "endpoint": "/smartbank/pembayaran_transaksi",
    "kelompok": "Kelompok 1",
    "peran": "Core banking, ledger, payment processor",
    "candidates": [
      {"label": "primary", "url": "http://127.0.0.1:8000", "priority": 1},
      {"label": "mirror",  "url": "http://127.0.0.1:9000", "priority": 2}
    ]
  }
}

# services/routing_service.py — OCP Compliant
import json

class RoutingRegistry:
    def __init__(self, config_path: str = "config/app_routes.json"):
        with open(config_path) as f:
            self._apps = json.load(f)

    def register_app(self, app_id: str, config: dict):
        """Tambah app baru TANPA modifikasi kode"""
        self._apps[app_id] = config

    def get_url(self, app_id: str) -> str:
        return self._apps.get(app_id, {}).get("url")
```

---

## Pelanggaran 5 — OCP: Fee Gateway Hardcoded 0.5%

### Prinsip yang Dilanggar
**Open/Closed Principle (OCP)**

### Penjelasan Pelanggaran
Persentase fee **di-hardcode langsung di kode** sebagai `0.005` (0.5%). Jika ingin mengubah struktur fee (fee bertingkat, diskon volume, fee per paket), seluruh fungsi harus dimodifikasi. Selain itu, string `"0.5%"` juga di-hardcode di response API.

### Potongan Kode yang Melanggar

```python
# services/log_service.py — baris 167-169

def hitung_fee_gateway(amount: float):
    """Hitung fee 0.5%"""
    return amount * 0.005   # ❌ Hardcoded! Tidak bisa di-extend tanpa modifikasi


# main.py — baris 315-321
# ❌ String "0.5%" juga hardcoded di response body!

return ResponseFormat(status="sukses", data={
    "jumlah_transaksi": amount,
    "fee_gateway_persen": "0.5%",       # ❌ Hardcoded string
    "fee_gateway_nominal": fee,
    "jumlah_diteruskan": net_amount,
    "keterangan": "Fee dipotong otomatis dari setiap transaksi via API Gateway"
})

# main.py — baris 588 (endpoint routing_universal)
    "fee_persen": "0.5%",               # ❌ Hardcoded lagi di tempat lain!
```

### Saran Refactor

```python
# Terapkan Strategy Pattern — OCP Compliant

from abc import ABC, abstractmethod

class FeeStrategy(ABC):
    """Abstraksi — terbuka untuk ekstensi"""
    @abstractmethod
    def hitung(self, amount: float) -> float: ...
    @abstractmethod
    def get_label(self) -> str: ...

class FlatFeeStrategy(FeeStrategy):
    """Fee flat 0.5% — implementasi default"""
    def __init__(self, persen: float = 0.5):
        self.persen = persen
    def hitung(self, amount: float) -> float:
        return amount * (self.persen / 100)
    def get_label(self) -> str:
        return f"{self.persen}%"

class TieredFeeStrategy(FeeStrategy):
    """Fee bertingkat — EXTEND tanpa ubah kode lama!"""
    def hitung(self, amount: float) -> float:
        if amount > 10_000_000:
            return amount * 0.003   # 0.3% untuk transaksi besar
        return amount * 0.005       # 0.5% default
    def get_label(self) -> str:
        return "0.3%-0.5% (tiered)"

# Penggunaan
fee_calc: FeeStrategy = FlatFeeStrategy()   # Bisa diganti strategy lain
fee = fee_calc.hitung(amount)
label = fee_calc.get_label()
```

---

## Pelanggaran 6 — OCP: Mapping Akses Endpoint Hardcoded di `cek_akses_app()`

### Prinsip yang Dilanggar
**Open/Closed Principle (OCP)**

### Penjelasan Pelanggaran
Fungsi `cek_akses_app()` memiliki dictionary `akses_map` yang **di-hardcode di dalam tubuh fungsi** itu sendiri. Setiap endpoint baru yang perlu kontrol akses membutuhkan modifikasi langsung pada fungsi ini.

### Potongan Kode yang Melanggar

```python
# services/log_service.py — baris 406-418 (di dalam fungsi cek_akses_app)

async def cek_akses_app(api_key: str, endpoint: str):
    ...
    # ❌ Mapping hardcoded di dalam fungsi — harus masuk ke sini setiap ada endpoint baru!
    akses_map = {
        "/integrator/routing_api":             "akses_routing",
        "/integrator/validasi_request":        "akses_validasi",
        "/integrator/logging":                 "akses_logging",
        "/integrator/biaya_layanan_integrasi": "akses_biaya",
        "/monitor/health-stats":               "akses_monitor",
        "/monitor/request-stats":              "akses_monitor",
        "/monitor/health-check":               "akses_monitor",
        # ← Endpoint baru? Harus edit isi fungsi ini!
    }
    kolom_akses = akses_map.get(endpoint)
    if kolom_akses and not app[kolom_akses]:
        return {"boleh": False, "pesan": f"Paket tidak bisa akses endpoint ini."}
```

### Saran Refactor

```python
# Pindahkan mapping ke konfigurasi terpisah — OCP Compliant

# config/endpoint_access.py
ENDPOINT_ACCESS_MAP = {
    "/integrator/routing_api":             "akses_routing",
    "/integrator/validasi_request":        "akses_validasi",
    "/integrator/logging":                 "akses_logging",
    "/integrator/biaya_layanan_integrasi": "akses_biaya",
    "/monitor/health-stats":               "akses_monitor",
    "/monitor/request-stats":              "akses_monitor",
    "/monitor/health-check":               "akses_monitor",
}
# Tambah endpoint baru? Cukup tambah di file config ini, tidak perlu ubah logika!

# services/log_service.py — OCP Compliant
from config.endpoint_access import ENDPOINT_ACCESS_MAP

async def cek_akses_app(api_key: str, endpoint: str):
    ...
    kolom_akses = ENDPOINT_ACCESS_MAP.get(endpoint)  # ← Dari config, bukan hardcode
    if kolom_akses and not app[kolom_akses]:
        return {"boleh": False, "pesan": "Paket tidak bisa akses endpoint ini."}
```

---

## Pelanggaran 7 — LSP: Penanganan Error Duplikat di `backtracking_route()`

### Prinsip yang Dilanggar
**Liskov Substitution Principle (LSP)**

> *"Objek dari subtype harus bisa menggantikan objek supertype tanpa mengubah perilaku."*

### Penjelasan Pelanggaran
Fungsi `backtracking_route()` memiliki **3 blok `except` yang nyaris identik**. Ketiganya melakukan hal yang **persis sama** (membuat step, memasukkan ke trace, memanggil rekursif), namun ditulis 3 kali secara terpisah. Ini menunjukkan pola yang seharusnya bisa disubstitusi secara seragam, namun justru diulang tanpa abstraksi.

### Potongan Kode yang Melanggar

```python
# services/routing_service.py — baris 221-264
# ❌ 3 blok except dengan logika IDENTIK — copy-paste!

    except httpx.ConnectError:
        step["status"] = "GAGAL_BACKTRACK"
        step["error"] = "ConnectError"
        step["error_detail"] = f"Tidak bisa konek ke {full_url}"
        if index + 1 < len(candidates):
            next_candidate = candidates[index + 1]
            step["aksi"] = f"BACKTRACK → coba kandidat #{index + 2} ({next_candidate['label']})"
        else:
            step["aksi"] = "Semua kandidat habis — tidak ada lagi yang bisa dicoba"
        trace.append(step)
        return await backtracking_route(app_id, data, candidates, index + 1, trace)

    except httpx.TimeoutException:
        step["status"] = "GAGAL_BACKTRACK"
        step["error"] = "TimeoutException"
        step["error_detail"] = f"Timeout setelah 5 detik menunggu {full_url}"
        # ↓↓↓ SAMA PERSIS dengan blok di atas! ↓↓↓
        if index + 1 < len(candidates):
            next_candidate = candidates[index + 1]
            step["aksi"] = f"BACKTRACK → coba kandidat #{index + 2} ({next_candidate['label']})"
        else:
            step["aksi"] = "Semua kandidat habis — tidak ada lagi yang bisa dicoba"
        trace.append(step)
        return await backtracking_route(app_id, data, candidates, index + 1, trace)

    except Exception as e:
        step["status"] = "GAGAL_BACKTRACK"
        step["error"] = type(e).__name__
        step["error_detail"] = str(e)
        # ↓↓↓ SAMA PERSIS lagi! ↓↓↓
        if index + 1 < len(candidates):
            next_candidate = candidates[index + 1]
            step["aksi"] = f"BACKTRACK → coba kandidat #{index + 2} ({next_candidate['label']})"
        else:
            step["aksi"] = "Semua kandidat habis — tidak ada lagi yang bisa dicoba"
        trace.append(step)
        return await backtracking_route(app_id, data, candidates, index + 1, trace)
```

### Saran Refactor

```python
# Gabungkan ke satu handler — LSP Compliant (semua error diperlakukan sama)

    except Exception as e:
        # Pesan error spesifik per tipe exception
        error_messages = {
            httpx.ConnectError:    f"Tidak bisa konek ke {full_url}",
            httpx.TimeoutException: f"Timeout setelah 5 detik menunggu {full_url}",
        }
        step["status"] = "GAGAL_BACKTRACK"
        step["error"] = type(e).__name__
        step["error_detail"] = error_messages.get(type(e), str(e))

        if index + 1 < len(candidates):
            next_label = candidates[index + 1]["label"]
            step["aksi"] = f"BACKTRACK → coba kandidat #{index + 2} ({next_label})"
        else:
            step["aksi"] = "Semua kandidat habis — tidak ada lagi yang bisa dicoba"

        trace.append(step)
        return await backtracking_route(app_id, data, candidates, index + 1, trace)
```

---

## Pelanggaran 8 — ISP: `RequestFormat` Terlalu Generik untuk Semua Endpoint

### Prinsip yang Dilanggar
**Interface Segregation Principle (ISP)**

> *"Client tidak boleh dipaksa bergantung pada interface yang tidak mereka gunakan."*

### Penjelasan Pelanggaran
Model `RequestFormat` hanya memiliki 2 field: `user_id` dan `parameter` (dict generik). **Semua endpoint** dipaksa menggunakan schema yang sama, padahal tiap endpoint butuh data yang berbeda-beda. Client harus "menebak" key apa saja yang harus diisi — tidak ada validasi tipe otomatis dari Pydantic.

### Potongan Kode yang Melanggar

```python
# models/schemas.py — Interface terlalu "gemuk" dan tidak spesifik

class RequestFormat(BaseModel):
    user_id: str
    parameter: Optional[Dict[str, Any]] = None   # ❌ Catch-all! Client harus tebak isinya


# main.py — Semua endpoint dipaksa pakai RequestFormat yang sama

@app.post("/apps/register")
async def register_app(req: RequestFormat):
    app_name = req.parameter.get("app_name", "")       # ← Client harus tahu key "app_name"
    nama_paket = req.parameter.get("nama_paket", "Starter")  # ← Tidak ada validasi tipe

@app.post("/integrator/routing_backtracking")
async def routing_backtracking(req: RequestFormat):
    token = req.parameter.get("token", "")              # ← Key berbeda lagi
    target_app = req.parameter.get("target_app", "")   # ← Tidak ada autocomplete/validasi

@app.post("/monitor/health-check")
async def health_check_endpoint(req: RequestFormat):
    app_name = req.parameter.get("app_name", "unknown")   # ← Key sama tapi semantik beda
    endpoint = req.parameter.get("endpoint", "/")
    status = req.parameter.get("status", "offline")
    response_time = req.parameter.get("response_time_ms", 0)  # ← 4 key yang harus ditebak!
```

### Saran Refactor

```python
# Buat schema spesifik per endpoint — ISP Compliant

class RegisterAppRequest(BaseModel):
    """Schema khusus untuk POST /apps/register"""
    app_name: str
    nama_paket: str = "Starter"

class BacktrackingRequest(BaseModel):
    """Schema khusus untuk POST /integrator/routing_backtracking"""
    user_id: str
    token: str
    target_app: str
    target_endpoint: Optional[str] = None
    amount: float = 0.0

class HealthCheckRequest(BaseModel):
    """Schema khusus untuk POST /monitor/health-check"""
    app_name: str
    endpoint: str = "/"
    status: str = "offline"
    response_time_ms: int = 0
    status_code: Optional[int] = None
    error_message: Optional[str] = None

# Sekarang tiap endpoint punya "interface" sendiri yang spesifik & tervalidasi!
@app.post("/apps/register")
async def register_app(req: RegisterAppRequest):
    hasil = await registrasi_app(req.app_name, req.nama_paket)  # ← Jelas & tervalidasi
```

---

## Pelanggaran 9 — DIP: Koneksi Database Langsung Tanpa Abstraksi

### Prinsip yang Dilanggar
**Dependency Inversion Principle (DIP)**

> *"Modul high-level tidak boleh bergantung pada modul low-level. Keduanya harus bergantung pada abstraksi."*

### Penjelasan Pelanggaran
Setiap fungsi di `log_service.py` **langsung membuat koneksi MySQL** dengan `aiomysql`. Logika bisnis (high-level) bergantung langsung pada implementasi database spesifik (low-level). Jika ingin migrasi ke PostgreSQL atau MongoDB, **seluruh file harus ditulis ulang**.

### Potongan Kode yang Melanggar

```python
# services/log_service.py — Pola berulang di 15+ fungsi!

async def catat_log_mongo(user_id, endpoint, data_tambahan):
    conn = await get_conn()              # ❌ Langsung ke MySQL!
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO logs_transaksi ...", (...))
    conn.close()

async def catat_request_log(user_id, source_app, endpoint, ...):
    conn = await get_conn()              # ❌ Lagi! Pola identik
    async with conn.cursor() as cur:
        await cur.execute("INSERT INTO api_request_log ...", (...))
    conn.close()

async def get_all_paket():
    conn = await get_conn()              # ❌ Lagi! 15+ kali pola yang sama
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT ... FROM pricing_plans ...")
        rows = await cur.fetchall()
    conn.close()
    return list(rows)

# Jika ganti database → semua 15+ fungsi harus diubah!
```

### Saran Refactor

```python
# Buat abstraksi Repository — DIP Compliant

from abc import ABC, abstractmethod

class ILogRepository(ABC):
    """Abstraksi (interface) — high-level module bergantung pada ini"""
    @abstractmethod
    async def simpan_log_transaksi(self, user_id: str, endpoint: str, detail: dict): ...

    @abstractmethod
    async def simpan_request_log(self, user_id: str, **kwargs): ...

    @abstractmethod
    async def ambil_request_stats(self) -> dict: ...


class MySQLLogRepository(ILogRepository):
    """Implementasi konkret MySQL"""
    def __init__(self, db_config: dict):
        self.db_config = db_config

    async def simpan_log_transaksi(self, user_id, endpoint, detail):
        conn = await aiomysql.connect(**self.db_config, autocommit=True)
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO logs_transaksi ...", (...))
        conn.close()


class MongoDBLogRepository(ILogRepository):
    """Implementasi alternatif MongoDB — tanpa ubah bisnis logic!"""
    async def simpan_log_transaksi(self, user_id, endpoint, detail):
        # Implementasi MongoDB ...
        pass


# main.py — Bisnis logic bergantung pada abstraksi
log_repo: ILogRepository = MySQLLogRepository(DB_CONFIG)  # ← Inject!
await log_repo.simpan_log_transaksi(user_id, endpoint, detail)
```

---

## Pelanggaran 10 — DIP: Secret Key JWT Hardcoded di Modul

### Prinsip yang Dilanggar
**Dependency Inversion Principle (DIP)**

### Penjelasan Pelanggaran
File `jwt_service.py` memiliki `SECRET_KEY` yang **di-hardcode langsung di source code**. Modul high-level (JWT service) bergantung langsung pada nilai konfigurasi low-level, bukan pada abstraksi konfigurasi. Ini juga merupakan **risiko keamanan serius** karena secret key masuk ke version control (Git).

### Potongan Kode yang Melanggar

```python
# services/jwt_service.py — baris 4-6

# ❌ Secret key hardcoded di source code! Masuk ke Git!
SECRET_KEY = "kunci_rahasia_umkm_rpl2"
ALGORITHM = "HS256"

def verifikasi_token(token: str):
    # ❌ Langsung pakai konstanta yang hardcoded
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return {
        "valid": True,
        "user_id": payload.get("user_id"),
        "role": payload.get("role", ""),
        "pesan": "Token aman, silakan lewat!"
    }

def bikin_token(user_id: str, role: str):
    batas_waktu = datetime.utcnow() + timedelta(minutes=30)
    payload = {"user_id": user_id, "role": role, "exp": batas_waktu}
    # ❌ Langsung pakai SECRET_KEY hardcoded
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

### Saran Refactor

```python
# Gunakan environment variable + dependency injection — DIP & Security Compliant

import os
from dataclasses import dataclass

# .env (file ini TIDAK masuk Git — tambahkan ke .gitignore!)
# JWT_SECRET_KEY=s3cr3t_k3y_pr0duct10n_y4ng_s4ng4t_p4nj4ng_d4n_4m4n
# JWT_ALGORITHM=HS256
# JWT_EXPIRE_MINUTES=30

@dataclass
class JWTConfig:
    """Abstraksi konfigurasi JWT"""
    secret_key: str
    algorithm: str = "HS256"
    expire_minutes: int = 30

    @classmethod
    def from_env(cls) -> "JWTConfig":
        """Baca dari environment variable"""
        return cls(
            secret_key=os.getenv("JWT_SECRET_KEY", "dev_only_key"),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
        )


class JWTService:
    """Service bergantung pada abstraksi config, bukan hardcoded value"""

    def __init__(self, config: JWTConfig):
        self._config = config    # ← Dependency di-inject!

    def verifikasi_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self._config.secret_key,          # ← Dari config, bukan hardcode
                algorithms=[self._config.algorithm]
            )
            return {"valid": True, "user_id": payload.get("user_id"), ...}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "pesan": "Token sudah kadaluarsa!"}
        except jwt.InvalidTokenError:
            return {"valid": False, "pesan": "Token tidak valid!"}

    def bikin_token(self, user_id: str, role: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self._config.expire_minutes)
        payload = {"user_id": user_id, "role": role, "exp": expire}
        return jwt.encode(payload, self._config.secret_key, algorithm=self._config.algorithm)


# Penggunaan di main.py
config = JWTConfig.from_env()     # Baca dari .env
jwt_service = JWTService(config)  # Inject dependency
```

---

## Ringkasan Pelanggaran

| No | Prinsip | File | Pelanggaran Singkat | Tingkat Keparahan |
|----|---------|------|---------------------|:-----------------:|
| 1 | **SRP** | `log_service.py` | God Module — 937 baris, 7+ tanggung jawab | 🔴 Berat |
| 2 | **SRP** | `main.py` | Campur aduk rate limiter, validasi, model, auth, endpoint | 🔴 Berat |
| 3 | **SRP** | `log_service.py` | `autentikasi_user()` melakukan 4 hal sekaligus | 🟡 Sedang |
| 4 | **OCP** | `routing_service.py` | Routing table hardcoded — harus edit kode untuk tambah app | 🟡 Sedang |
| 5 | **OCP** | `log_service.py` & `main.py` | Fee 0.5% hardcoded di kode & response | 🟡 Sedang |
| 6 | **OCP** | `log_service.py` | `akses_map` hardcoded di dalam fungsi `cek_akses_app()` | 🟡 Sedang |
| 7 | **LSP** | `routing_service.py` | 3 blok `except` duplikat di `backtracking_route()` | 🟡 Sedang |
| 8 | **ISP** | `schemas.py` + `main.py` | `RequestFormat` generik dipaksa ke semua endpoint | 🔴 Berat |
| 9 | **DIP** | `log_service.py` | Koneksi MySQL langsung — tidak ada abstraksi repository | 🔴 Berat |
| 10 | **DIP** | `jwt_service.py` | Secret key hardcoded di source code (risiko keamanan!) | 🔴 Berat |

---

## Kesimpulan

Project **Tugas Gateway** memiliki arsitektur yang fungsional dan fitur yang lengkap. Namun dari perspektif prinsip SOLID, ditemukan **10 pelanggaran** yang mencakup kelima prinsip:

| Prinsip | Jumlah Pelanggaran | Dampak Utama |
|---------|--------------------|--------------|
| **SRP** — Single Responsibility | 3 | Sulit di-maintain, perubahan satu fitur berdampak ke banyak hal |
| **OCP** — Open/Closed | 3 | Setiap penambahan fitur membutuhkan modifikasi kode yang sudah berjalan |
| **LSP** — Liskov Substitution | 1 | Kode duplikat, sulit di-refactor |
| **ISP** — Interface Segregation | 1 | Client harus "tebak" key yang dibutuhkan, tidak ada validasi otomatis |
| **DIP** — Dependency Inversion | 2 | Sulit di-test, sulit migrasi database, risiko keamanan |

Dengan menerapkan saran refactor yang disediakan untuk tiap pelanggaran, project ini akan lebih **mudah di-maintain**, **mudah di-test** (unit testing), **mudah di-extend** (tambah fitur baru), dan lebih **aman** secara keamanan.
