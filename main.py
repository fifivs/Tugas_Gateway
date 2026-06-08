from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models.schemas import RequestFormat, ResponseFormat
from services.jwt_service import verifikasi_token, bikin_token_dummy
from services.log_service import (
    catat_log_mongo,
    hitung_fee_gateway,
    catat_request_log,
    catat_health_log,
    get_request_stats,
    get_health_stats,
    init_db,
    get_all_paket,
    registrasi_app,
    cek_akses_app,
    kurangi_quota,
    tambah_fee_app,
    get_status_app,
    upgrade_paket_app,
    catat_backtracking_log,
    get_backtracking_stats
)
from services.routing_service import teruskan_ke_smartbank, teruskan_ke_app, get_daftar_app, route_dengan_backtracking, get_route_candidates_info
from collections import defaultdict
import time
import os

# ==========================================
# RATE LIMITER — Simple in-memory per user
# ==========================================
_rate_limit_store: dict = defaultdict(list)
RATE_LIMIT_MAX    = 30   # max request
RATE_LIMIT_WINDOW = 60   # per 60 detik

def check_rate_limit(identifier: str):
    """Cek rate limit per user_id. Return (boleh: bool, pesan: str)"""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    # Buang timestamps yang sudah di luar window
    _rate_limit_store[identifier] = [
        ts for ts in _rate_limit_store[identifier] if ts > window_start
    ]
    count = len(_rate_limit_store[identifier])
    if count >= RATE_LIMIT_MAX:
        reset_in = int(_rate_limit_store[identifier][0] + RATE_LIMIT_WINDOW - now)
        return False, (
            f"Rate limit tercapai! Maks {RATE_LIMIT_MAX} request per {RATE_LIMIT_WINDOW} detik. "
            f"Reset dalam ±{reset_in} detik."
        )
    _rate_limit_store[identifier].append(now)
    return True, f"OK ({count + 1}/{RATE_LIMIT_MAX})"


# ==========================================
# VALIDASI INPUT
# ==========================================

def validasi_amount(raw_amount):
    """Validasi nilai amount transaksi. Return (valid: bool, pesan: str, amount: float)"""
    try:
        amount = float(raw_amount)
    except (TypeError, ValueError):
        return False, "Amount harus berupa angka (contoh: 50000).", 0.0
    if amount < 0:
        return False, "Amount tidak boleh negatif.", 0.0
    if amount == 0:
        # Amount 0 diizinkan (misal: request non-finansial), warning saja
        pass
    if amount > 1_000_000_000:
        return False, "Amount melebihi batas maksimal sistem (Rp 1.000.000.000).", 0.0
    return True, "OK", amount

app = FastAPI(title="API Gateway / Integrator UMKM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Buat tabel MySQL otomatis saat server start
@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
def serve_landing():
    return FileResponse(os.path.join(frontend_dir, "landing.html"))

@app.get("/login")
def serve_login():
    return FileResponse(os.path.join(frontend_dir, "login.html"))

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/marketplace")
def serve_marketplace():
    return FileResponse(os.path.join(frontend_dir, "marketplace.html"))

@app.get("/monitor")
def serve_monitor():
    return FileResponse(os.path.join(frontend_dir, "api_monitor.html"))


@app.get("/apps/manage")
def serve_apps_manage():
    return FileResponse(os.path.join(frontend_dir, "apps.html"))


@app.get("/integrator/manage/routing")
def serve_routing_manage():
    return FileResponse(os.path.join(frontend_dir, "routing.html"))


@app.get("/pricing/manage")
def serve_pricing_manage():
    return FileResponse(os.path.join(frontend_dir, "pricing.html"))


@app.get("/token/manage")
def serve_token_manage():
    return FileResponse(os.path.join(frontend_dir, "token.html"))


@app.get("/integrator/fee/manage")
def serve_fee_manage():
    return FileResponse(os.path.join(frontend_dir, "fee.html"))


@app.get("/integrator/logging/manage")
def serve_logging_manage():
    return FileResponse(os.path.join(frontend_dir, "logging.html"))


@app.get("/monitor/health-check/manage")
def serve_health_check_manage():
    return FileResponse(os.path.join(frontend_dir, "health_check.html"))

@app.get("/generate_token_tester/{user_id}")
def generate_token(user_id: str):
    return {"token_buat_ngetes": bikin_token_dummy(user_id)}

@app.post("/integrator/routing_api", response_model=ResponseFormat)
async def routing_api(req: RequestFormat):
    start_time = time.time()

    # --- Rate Limit Check ---
    rl_ok, rl_pesan = check_rate_limit(req.user_id)
    if not rl_ok:
        return ResponseFormat(status="gagal", data={"pesan": rl_pesan, "kode": "RATE_LIMIT"})

    # --- Validasi JWT ---
    token = req.parameter.get("token", "") if req.parameter else ""
    auth = verifikasi_token(token)
    if not auth["valid"]:
        return ResponseFormat(status="gagal", data={"pesan": auth["pesan"]})

    await catat_log_mongo(req.user_id, "/integrator/routing_api", req.parameter)

    # --- Validasi Amount ---
    raw_amount = req.parameter.get("amount", 0) if req.parameter else 0
    amount_valid, amount_pesan, amount = validasi_amount(raw_amount)
    if not amount_valid:
        return ResponseFormat(status="gagal", data={"pesan": amount_pesan, "kode": "INVALID_AMOUNT"})

    # Jika pemanggil menyertakan api_key, cek paket & fee dari paket itu
    api_key = req.parameter.get("api_key", "") if req.parameter else ""
    fee = hitung_fee_gateway(amount)
    # Default: gunakan freme hitung_fee_gateway; tapi jika ada api_key dan paketnya valid,
    # override fee berdasarkan persentase paket (nilai di DB adalah misal 0.5 untuk 0.5%)
    if api_key:
        akses = await cek_akses_app(api_key, "/integrator/routing_api")
        if not akses.get("boleh"):
            return ResponseFormat(status="gagal", data={"pesan": akses.get("pesan")})
        try:
            fee_persen = float(akses.get("fee_persen", 0))
            # fee_persen seperti 0.5 (representasi persen), konversi ke desimal
            fee = amount * (fee_persen / 100.0)
        except Exception:
            fee = hitung_fee_gateway(amount)

    data_untuk_bank = {
        "user_id": req.user_id,
        "amount": amount,
        "fee_gateway": fee,
        "metadata": req.parameter
    }
    hasil_bank = await teruskan_ke_smartbank(data_untuk_bank)

    elapsed_ms = int((time.time() - start_time) * 1000)
    source_app = req.parameter.get("source_app", "unknown") if req.parameter else "unknown"
    smartbank_status = hasil_bank.get("status", "gagal") if isinstance(hasil_bank, dict) else "gagal"

    await catat_request_log(
        user_id=req.user_id,
        source_app=source_app,
        endpoint="/integrator/routing_api",
        amount=amount,
        fee=fee,
        jwt_valid=True,
        smartbank_status=smartbank_status,
        response_time_ms=elapsed_ms
    )

    # Jika ada api_key dan transaksi sukses, kurangi quota dan tambahkan catatan fee di app
    if api_key and smartbank_status == "sukses":
        try:
            await kurangi_quota(api_key)
            await tambah_fee_app(api_key, fee)
        except Exception as e:
            print(f"[WARN] Gagal update quota/fee untuk {api_key}: {e}")

    return ResponseFormat(status="sukses", data={
        "integrator_note": "Request divalidasi & log tersimpan di MySQL",
        "fee_diambil": fee,
        "respons_dari_smartbank": hasil_bank
    })

@app.post("/integrator/validasi_request", response_model=ResponseFormat)
async def validasi_request(req: RequestFormat):
    token = req.parameter.get("token", "") if req.parameter else ""
    auth = verifikasi_token(token)
    if auth["valid"]:
        return ResponseFormat(status="sukses", data={"valid": True, "user_id": auth["user_id"], "pesan": auth["pesan"]})
    else:
        return ResponseFormat(status="gagal", data={"valid": False, "pesan": auth["pesan"]})

@app.post("/integrator/logging", response_model=ResponseFormat)
async def logging_request(req: RequestFormat):
    endpoint_target = req.parameter.get("endpoint", "/unknown") if req.parameter else "/unknown"
    await catat_log_mongo(req.user_id, endpoint_target, req.parameter)
    return ResponseFormat(status="sukses", data={
        "pesan": f"Log untuk user '{req.user_id}' berhasil dicatat di MySQL",
        "endpoint_dicatat": endpoint_target
    })

@app.post("/integrator/biaya_layanan_integrasi", response_model=ResponseFormat)
async def biaya_layanan(req: RequestFormat):
    amount = req.parameter.get("amount", 0) if req.parameter else 0
    fee = hitung_fee_gateway(amount)
    net_amount = amount - fee
    return ResponseFormat(status="sukses", data={
        "jumlah_transaksi": amount,
        "fee_gateway_persen": "0.5%",
        "fee_gateway_nominal": fee,
        "jumlah_diteruskan": net_amount,
        "keterangan": "Fee dipotong otomatis dari setiap transaksi via API Gateway"
    })

@app.get("/monitor/request-stats")
async def request_stats():
    data = await get_request_stats()
    return {"status": "sukses", "data": data}

@app.get("/monitor/health-stats")
async def health_stats():
    data = await get_health_stats()
    return {"status": "sukses", "data": data}

@app.post("/monitor/health-check")
async def health_check_endpoint(req: RequestFormat):
    app_name = req.parameter.get("app_name", "unknown") if req.parameter else "unknown"
    endpoint = req.parameter.get("endpoint", "/") if req.parameter else "/"
    status = req.parameter.get("status", "offline") if req.parameter else "offline"
    response_time = req.parameter.get("response_time_ms", 0) if req.parameter else 0
    status_code = req.parameter.get("status_code", None) if req.parameter else None
    error_msg = req.parameter.get("error_message", None) if req.parameter else None

    await catat_health_log(
        app_name=app_name,
        endpoint=endpoint,
        status=status,
        response_time_ms=response_time,
        status_code=status_code,
        error_message=error_msg
    )
    return ResponseFormat(status="sukses", data={"pesan": f"Health log {app_name} berhasil dicatat"})


# ==========================================
# PRICING ENDPOINTS — Sistem Paket Harga
# ==========================================

@app.get("/paket/list")
async def list_paket():
    """Lihat semua paket harga yang tersedia"""
    data = await get_all_paket()
    return {"status": "sukses", "data": data}


@app.post("/apps/register", response_model=ResponseFormat)
async def register_app(req: RequestFormat):
    """Daftarkan app ke gateway & pilih paket langganan"""
    app_name = req.parameter.get("app_name", "") if req.parameter else ""
    nama_paket = req.parameter.get("nama_paket", "Starter") if req.parameter else "Starter"

    if not app_name:
        return ResponseFormat(status="gagal", data={"pesan": "'app_name' wajib diisi"})

    hasil = await registrasi_app(app_name, nama_paket)
    status = "sukses" if hasil.get("sukses") else "gagal"
    return ResponseFormat(status=status, data=hasil)


@app.get("/apps/status")
async def status_app(api_key: str):
    """Cek status langganan & quota tersisa sebuah app"""
    data = await get_status_app(api_key)
    if not data:
        return {"status": "gagal", "data": {"pesan": "API Key tidak ditemukan"}}
    return {"status": "sukses", "data": data}


@app.post("/apps/upgrade", response_model=ResponseFormat)
async def upgrade_app(req: RequestFormat):
    """Upgrade paket langganan app"""
    api_key = req.parameter.get("api_key", "") if req.parameter else ""
    paket_baru = req.parameter.get("paket_baru", "") if req.parameter else ""

    if not api_key or not paket_baru:
        return ResponseFormat(status="gagal", data={"pesan": "'api_key' dan 'paket_baru' wajib diisi"})

    hasil = await upgrade_paket_app(api_key, paket_baru)
    status = "sukses" if hasil.get("sukses") else "gagal"
    return ResponseFormat(status=status, data=hasil)


# ==========================================
# BACKTRACKING ROUTING — Algoritma Backtracking
# ==========================================

@app.get("/integrator/backtracking/manage")
def serve_backtracking_manage():
    return FileResponse(os.path.join(frontend_dir, "backtracking.html"))


@app.post("/integrator/routing_backtracking", response_model=ResponseFormat)
async def routing_backtracking(req: RequestFormat):
    """
    Forward request ke app target menggunakan ALGORITMA BACKTRACKING.
    Jika route utama gagal, otomatis backtrack ke route alternatif.
    Wajib isi 'target_app' di parameter.
    """
    start_time = time.time()

    # Rate limit check
    rl_ok, rl_pesan = check_rate_limit(req.user_id)
    if not rl_ok:
        return ResponseFormat(status="gagal", data={"pesan": rl_pesan, "kode": "RATE_LIMIT"})

    # Validasi JWT
    token = req.parameter.get("token", "") if req.parameter else ""
    auth = verifikasi_token(token)
    if not auth["valid"]:
        return ResponseFormat(status="gagal", data={"pesan": auth["pesan"]})

    # Ambil target app
    target_app = req.parameter.get("target_app", "") if req.parameter else ""
    target_endpoint = req.parameter.get("target_endpoint", None) if req.parameter else None

    if not target_app:
        return ResponseFormat(status="gagal", data={
            "pesan": "'target_app' wajib diisi di dalam parameter.",
            "pilihan_app": ["smartbank", "marketplace", "pos", "supplierhub", "logistikita", "umkminsight"],
            "contoh": {
                "user_id": "user123",
                "parameter": {
                    "token": "...",
                    "target_app": "marketplace",
                    "amount": 50000
                }
            }
        })

    # Validasi amount (jika ada)
    raw_amount = req.parameter.get("amount", 0) if req.parameter else 0
    amount_valid, amount_pesan, amount = validasi_amount(raw_amount)
    if not amount_valid:
        return ResponseFormat(status="gagal", data={"pesan": amount_pesan, "kode": "INVALID_AMOUNT"})

    # Hitung fee Gateway
    fee = hitung_fee_gateway(amount)

    # Log request
    await catat_log_mongo(req.user_id, f"/integrator/routing_backtracking → {target_app}", req.parameter)

    # Forward dengan ALGORITMA BACKTRACKING
    data_forward = {
        "user_id": req.user_id,
        "amount": amount,
        "fee_gateway": fee,
        "source": "API_Gateway_Backtracking",
        "metadata": req.parameter
    }
    hasil = await route_dengan_backtracking(target_app, data_forward, target_endpoint)

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Catat backtracking log
    await catat_backtracking_log(
        user_id=req.user_id,
        target_app=target_app,
        total_candidates=hasil.get("total_candidates", len(hasil.get("trace", []))),
        total_attempts=hasil.get("total_attempts", 0),
        route_used=hasil.get("route_used", "none"),
        final_status=hasil.get("status", "gagal"),
        trace=hasil.get("trace", []),
        response_time_ms=elapsed_ms
    )

    return ResponseFormat(status=hasil.get("status", "gagal"), data={
        "algoritma": "backtracking",
        "target_app": target_app,
        "route_used": hasil.get("route_used", "none"),
        "route_url": hasil.get("route_url", "-"),
        "total_attempts": hasil.get("total_attempts", 0),
        "total_candidates": hasil.get("total_candidates", 0),
        "fee_gateway": fee,
        "response_time_ms": elapsed_ms,
        "trace": hasil.get("trace", []),
        "respons_dari_app": hasil.get("data", hasil.get("pesan", "No response"))
    })


@app.get("/monitor/backtracking-stats")
async def backtracking_stats_endpoint():
    """Lihat statistik dan riwayat backtracking routing"""
    data = await get_backtracking_stats()
    return {"status": "sukses", "data": data}


@app.get("/integrator/route-candidates")
def route_candidates_endpoint():
    """Lihat routing table backtracking — semua candidates per app"""
    data = get_route_candidates_info()
    return {"status": "sukses", "data": data}


# ==========================================
# ROUTING UNIVERSAL — Kirim ke App Manapun
# ==========================================

@app.post("/integrator/routing_universal", response_model=ResponseFormat)
async def routing_universal(req: RequestFormat):
    """
    Forward request ke app UMKM manapun via Gateway.
    Wajib isi 'target_app' di parameter (smartbank/marketplace/pos/supplierhub/logistikita/umkminsight).
    Opsional: 'target_endpoint' untuk override endpoint default.
    """
    start_time = time.time()

    # Rate limit check
    rl_ok, rl_pesan = check_rate_limit(req.user_id)
    if not rl_ok:
        return ResponseFormat(status="gagal", data={"pesan": rl_pesan, "kode": "RATE_LIMIT"})

    # Validasi JWT
    token = req.parameter.get("token", "") if req.parameter else ""
    auth = verifikasi_token(token)
    if not auth["valid"]:
        return ResponseFormat(status="gagal", data={"pesan": auth["pesan"]})

    # Ambil target app
    target_app = req.parameter.get("target_app", "") if req.parameter else ""
    target_endpoint = req.parameter.get("target_endpoint", None) if req.parameter else None

    if not target_app:
        return ResponseFormat(status="gagal", data={
            "pesan": "'target_app' wajib diisi di dalam parameter.",
            "pilihan_app": ["smartbank", "marketplace", "pos", "supplierhub", "logistikita", "umkminsight"],
            "contoh": {"user_id": "user123", "parameter": {"token": "...", "target_app": "marketplace", "amount": 50000}}
        })

    # Validasi amount (jika ada)
    raw_amount = req.parameter.get("amount", 0) if req.parameter else 0
    amount_valid, amount_pesan, amount = validasi_amount(raw_amount)
    if not amount_valid:
        return ResponseFormat(status="gagal", data={"pesan": amount_pesan, "kode": "INVALID_AMOUNT"})

    # Hitung fee Gateway
    fee = hitung_fee_gateway(amount)

    # Log request
    await catat_log_mongo(req.user_id, f"/integrator/routing_universal → {target_app}", req.parameter)

    # Forward ke app target
    data_forward = {
        "user_id": req.user_id,
        "amount": amount,
        "fee_gateway": fee,
        "source": "API_Gateway",
        "metadata": req.parameter
    }
    hasil = await teruskan_ke_app(target_app, data_forward, target_endpoint)

    elapsed_ms = int((time.time() - start_time) * 1000)
    target_status = hasil.get("status", "gagal") if isinstance(hasil, dict) else "gagal"
    source_app    = req.parameter.get("source_app", "unknown") if req.parameter else "unknown"

    await catat_request_log(
        user_id=req.user_id,
        source_app=source_app,
        endpoint=f"/integrator/routing_universal → {target_app}",
        amount=amount,
        fee=fee,
        jwt_valid=True,
        smartbank_status=target_status,
        response_time_ms=elapsed_ms
    )

    return ResponseFormat(status="sukses", data={
        "target_app": target_app,
        "target_endpoint": target_endpoint or f"(default {target_app})",
        "fee_gateway": fee,
        "fee_persen": "0.5%",
        "response_time_ms": elapsed_ms,
        "respons_dari_app": hasil
    })


@app.get("/integrator/daftar_route")
def daftar_route():
    """
    Tampilkan routing table — daftar semua app yang terdaftar di Gateway.
    Berguna untuk dokumentasi integrasi dan debug koneksi antar service.
    """
    apps = get_daftar_app()
    return {
        "status": "sukses",
        "data": {
            "total_app": len(apps),
            "daftar_app": apps,
            "catatan": "Ganti base_url sesuai IP/port teman kelompok saat integrasi.",
            "endpoint_universal": "POST /integrator/routing_universal"
        }
    }