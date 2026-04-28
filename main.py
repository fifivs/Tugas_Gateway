from fastapi import FastAPI
from models.schemas import RequestFormat, ResponseFormat
from services.jwt_service import verifikasi_token, bikin_token_dummy
# Update di sini: panggil catat_log_mongo, bukan catat_log
from services.log_service import catat_log_mongo, hitung_fee_gateway
from services.routing_service import teruskan_ke_smartbank

app = FastAPI(title="API Gateway / Integrator UMKM")

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