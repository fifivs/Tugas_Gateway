import httpx
from typing import Optional

# ==========================================
# DAFTAR URL SEMUA APLIKASI EKOSISTEM UMKM
# Ganti IP/port sesuai teman kelompok masing-masing
# ==========================================
APP_URLS = {
    "smartbank":    "http://127.0.0.1:8000",   # Kelompok 1
    "marketplace":  "http://127.0.0.1:8002",   # Kelompok 2
    "pos":          "http://127.0.0.1:8003",   # Kelompok 3
    "supplierhub":  "http://127.0.0.1:8004",   # Kelompok 4
    "logistikita":  "http://127.0.0.1:8005",   # Kelompok 5
    "umkminsight":  "http://127.0.0.1:8006",   # Kelompok 6
}

# Default endpoint masing-masing aplikasi
APP_DEFAULT_ENDPOINTS = {
    "smartbank":    "/smartbank/pembayaran_transaksi",
    "marketplace":  "/marketplace/checkout",
    "pos":          "/pos/transaksi",
    "supplierhub":  "/supplier/order_bahan",
    "logistikita":  "/logistik/request_pengiriman",
    "umkminsight":  "/insight/data_transaksi",
}

# Deskripsi singkat tiap app untuk dokumentasi
APP_INFO = {
    "smartbank":    {"kelompok": "Kelompok 1", "peran": "Core banking, ledger, payment processor"},
    "marketplace":  {"kelompok": "Kelompok 2", "peran": "Jual beli produk UMKM (PasarKita)"},
    "pos":          {"kelompok": "Kelompok 3", "peran": "Transaksi kasir offline (WarungPOS)"},
    "supplierhub":  {"kelompok": "Kelompok 4", "peran": "Supply chain B2B bahan baku"},
    "logistikita":  {"kelompok": "Kelompok 5", "peran": "Layanan pengiriman dan ongkir"},
    "umkminsight":  {"kelompok": "Kelompok 6", "peran": "Analytics dashboard (read-only)"},
}


async def teruskan_ke_app(target_app: str, data: dict, endpoint: Optional[str] = None):
    """
    Forward request ke aplikasi target di ekosistem UMKM.
    
    Args:
        target_app : ID aplikasi tujuan (lihat APP_URLS)
        data       : Payload yang akan dikirim
        endpoint   : Override endpoint tujuan (opsional, pakai default kalau None)
    
    Returns:
        dict response dari aplikasi tujuan, atau dict error
    """
    base_url = APP_URLS.get(target_app)
    if not base_url:
        return {
            "status": "gagal",
            "pesan": f"Aplikasi '{target_app}' tidak dikenali oleh Gateway.",
            "pilihan": list(APP_URLS.keys())
        }

    target_endpoint = endpoint or APP_DEFAULT_ENDPOINTS.get(target_app, "/")
    full_url = f"{base_url}{target_endpoint}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(full_url, json=data)
            return response.json()
        except httpx.ConnectError:
            return {
                "status": "gagal",
                "pesan": f"Gagal konek ke '{target_app}' ({full_url}). Pastikan service sudah running."
            }
        except httpx.TimeoutException:
            return {
                "status": "gagal",
                "pesan": f"Timeout! '{target_app}' tidak merespons dalam 10 detik."
            }
        except Exception as e:
            return {
                "status": "gagal",
                "pesan": f"Error routing ke '{target_app}': {str(e)}"
            }


async def teruskan_ke_smartbank(data_transaksi: dict):
    """Backward compatible — forward ke SmartBank endpoint pembayaran"""
    return await teruskan_ke_app("smartbank", data_transaksi, "/smartbank/pembayaran_transaksi")


def get_daftar_app():
    """Kembalikan daftar lengkap app yang terdaftar di routing table"""
    return [
        {
            "app_id": app_id,
            "kelompok": APP_INFO[app_id]["kelompok"],
            "peran": APP_INFO[app_id]["peran"],
            "base_url": base_url,
            "default_endpoint": APP_DEFAULT_ENDPOINTS.get(app_id, "/"),
            "url_lengkap": f"{base_url}{APP_DEFAULT_ENDPOINTS.get(app_id, '/')}"
        }
        for app_id, base_url in APP_URLS.items()
    ]