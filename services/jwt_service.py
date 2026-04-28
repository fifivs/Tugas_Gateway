import jwt
from datetime import datetime, timedelta

# Kunci gembok rahasia server
SECRET_KEY = "kunci_rahasia_umkm_rpl2" 
ALGORITHM = "HS256"

def verifikasi_token(token: str):
    """Fungsi cek keaslian token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"valid": True, "user_id": payload.get("user_id"), "pesan": "Token aman, silakan lewat!"}
    
    except jwt.ExpiredSignatureError:
        return {"valid": False, "pesan": "Akses ditolak: Token lu udah kadaluarsa bang!"}
    except jwt.InvalidTokenError:
        return {"valid": False, "pesan": "Akses ditolak: Token palsu atau format salah!"}

def bikin_token_dummy(user_id: str):
    """Fungsi bantuan buat ngetes"""
    batas_waktu = datetime.utcnow() + timedelta(minutes=30)
    payload = {"user_id": user_id, "exp": batas_waktu}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token