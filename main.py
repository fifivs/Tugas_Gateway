from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models.schemas import RequestFormat, ResponseFormat
from services.jwt_service import verifikasi_token, bikin_token_dummy
# Update di sini: panggil catat_log_mongo, bukan catat_log
from services.log_service import catat_log_mongo, hitung_fee_gateway
from services.routing_service import teruskan_ke_smartbank
import os

app = FastAPI(title="API Gateway / Integrator UMKM")

# CORS agar frontend bisa akses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount folder frontend sebagai static files
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Halaman utama -> Landing Page (publik)
@app.get("/")
def serve_landing():
    return FileResponse(os.path.join(frontend_dir, "landing.html"))

# Halaman login
@app.get("/login")
def serve_login():
    return FileResponse(os.path.join(frontend_dir, "login.html"))

# Halaman dashboard (setelah login)
@app.get("/dashboard")
def serve_dashboard():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.get("/generate_token_tester/{user_id}")
def generate_token(user_id: str):
    return {"token_buat_ngetes": bikin_token_dummy(user_id)}

@app.post("/integrator/routing_api", response_model=ResponseFormat)
async def routing_api(req: RequestFormat):
    # 1. VALIDASI REQUEST (Algoritma Kriptografi)
    token = req.parameter.get("token", "") if req.parameter else ""
    auth = verifikasi_token(token)
    if not auth["valid"]:
        return ResponseFormat(status="gagal", data={"pesan": auth["pesan"]})
    
    # 2. LOGGING (Simpan ke MongoDB Atlas)
    # Pakai await karena simpan ke cloud butuh waktu
    await catat_log_mongo(req.user_id, "/integrator/routing_api", req.parameter)
    
    # 3. BIAYA LAYANAN (Hitung Fee 0.5%)
    amount = req.parameter.get("amount", 0) if req.parameter else 0
    fee = hitung_fee_gateway(amount)
    
    # 4. ROUTING API (Teruskan ke SmartBank)
    data_untuk_bank = {
        "user_id": req.user_id,
        "amount": amount,
        "fee_gateway": fee,
        "metadata": req.parameter
    }
    
    hasil_bank = await teruskan_ke_smartbank(data_untuk_bank)
    
    return ResponseFormat(status="sukses", data={
        "integrator_note": "Request divalidasi & log tersimpan di Atlas",
        "fee_diambil": fee,
        "respons_dari_smartbank": hasil_bank
    })

# ===== ENDPOINT VALIDASI REQUEST =====
@app.post("/integrator/validasi_request", response_model=ResponseFormat)
async def validasi_request(req: RequestFormat):
    """Endpoint khusus untuk validasi token JWT"""
    token = req.parameter.get("token", "") if req.parameter else ""
    auth = verifikasi_token(token)
    
    if auth["valid"]:
        return ResponseFormat(status="sukses", data={
            "valid": True,
            "user_id": auth["user_id"],
            "pesan": auth["pesan"]
        })
    else:
        return ResponseFormat(status="gagal", data={
            "valid": False,
            "pesan": auth["pesan"]
        })

# ===== ENDPOINT LOGGING =====
@app.post("/integrator/logging", response_model=ResponseFormat)
async def logging_request(req: RequestFormat):
    """Endpoint khusus untuk mencatat log request ke MongoDB Atlas"""
    endpoint_target = req.parameter.get("endpoint", "/unknown") if req.parameter else "/unknown"
    
    await catat_log_mongo(req.user_id, endpoint_target, req.parameter)
    
    return ResponseFormat(status="sukses", data={
        "pesan": f"Log untuk user '{req.user_id}' berhasil dicatat di MongoDB Atlas",
        "endpoint_dicatat": endpoint_target
    })

# ===== ENDPOINT BIAYA LAYANAN INTEGRASI =====
@app.post("/integrator/biaya_layanan_integrasi", response_model=ResponseFormat)
async def biaya_layanan(req: RequestFormat):
    """Endpoint khusus untuk menghitung biaya layanan gateway (fee 0.5%)"""
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