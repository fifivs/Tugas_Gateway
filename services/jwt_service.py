import jwt
from datetime import datetime, timedelta

# Kunci gembok rahasia server
SECRET_KEY = "kunci_rahasia_umkm_rpl2" 
ALGORITHM = "HS256"

def verifikasi_token(token: str):
    """Fungsi cek keaslian token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "user_id": payload.get("user_id"),
            "role": payload.get("role", ""),       # ← tambah role
            "pesan": "Token aman, silakan lewat!"
        }
    except jwt.ExpiredSignatureError:
        return {"valid": False, "pesan": "Akses ditolak: Token lu udah kadaluarsa bang!"}
    except jwt.InvalidTokenError:
        return {"valid": False, "pesan": "Akses ditolak: Token palsu atau format salah!"}

def bikin_token(user_id: str, role: str):
    """Buat JWT token dengan role"""
    batas_waktu = datetime.utcnow() + timedelta(minutes=30)
    payload = {"user_id": user_id, "role": role, "exp": batas_waktu}  # ← role disimpan di token
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def bikin_token_dummy(user_id: str, role: str = ""):
    """Fungsi bantuan buat ngetes (backward compatible)"""
    return bikin_token(user_id, role)