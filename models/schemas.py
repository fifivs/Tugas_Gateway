from pydantic import BaseModel
from typing import Optional, Dict, Any

# Ini aturan baku buat data yang MASUK dari aplikasi lain
class RequestFormat(BaseModel):
    user_id: str
    parameter: Optional[Dict[str, Any]] = None

# Ini aturan baku buat data yang KELUAR dari Gateway lu
class ResponseFormat(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None