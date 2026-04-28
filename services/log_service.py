from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Masukin lagi kabel koneksi Atlas lu yang tadi di sini
MONGO_DETAILS = "mongodb+srv://andikarizkia4231_db_user:DTWwFy4eumByGWm8@cluster0.ku2sqzl.mongodb.net/?appName=Cluster0"

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.TugasGateway 
log_collection = database.get_collection("logs_transaksi")

async def catat_log_mongo(user_id: str, endpoint: str, data_tambahan: dict = None):
    """Fungsi murni buat nyatet ke MongoDB"""
    document = {
        "user_id": user_id,
        "endpoint": endpoint,
        "waktu": datetime.now(),
        "detail": data_tambahan
    }
    try:
        await log_collection.insert_one(document)
        print(f"✅ Log {user_id} berhasil disimpan ke MongoDB Atlas!")
    except Exception as e:
        print(f"❌ Gagal simpan log: {e}")

def hitung_fee_gateway(amount: float):
    """Algoritma hitung fee 0.5%"""
    return amount * 0.005