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


# ==========================================
# BACKTRACKING ROUTING FAILOVER
# Algoritma Backtracking untuk resilient routing
# ==========================================

# Routing table dengan MULTIPLE candidates per app
# Setiap app punya primary, mirror, dan fallback route
ROUTE_CANDIDATES = {
    "smartbank": [
        {"label": "primary",  "url": "http://127.0.0.1:8000", "endpoint": "/smartbank/pembayaran_transaksi", "priority": 1},
        {"label": "mirror",   "url": "http://127.0.0.1:9000", "endpoint": "/smartbank/pembayaran_transaksi", "priority": 2},
        {"label": "fallback", "url": "http://127.0.0.1:8000", "endpoint": "/smartbank/health",               "priority": 3},
    ],
    "marketplace": [
        {"label": "primary",  "url": "http://127.0.0.1:8002", "endpoint": "/marketplace/checkout",  "priority": 1},
        {"label": "mirror",   "url": "http://127.0.0.1:9002", "endpoint": "/marketplace/checkout",  "priority": 2},
        {"label": "fallback", "url": "http://127.0.0.1:8002", "endpoint": "/marketplace/fallback",  "priority": 3},
    ],
    "pos": [
        {"label": "primary",  "url": "http://127.0.0.1:8003", "endpoint": "/pos/transaksi",  "priority": 1},
        {"label": "mirror",   "url": "http://127.0.0.1:9003", "endpoint": "/pos/transaksi",  "priority": 2},
        {"label": "fallback", "url": "http://127.0.0.1:8003", "endpoint": "/pos/fallback",   "priority": 3},
    ],
    "supplierhub": [
        {"label": "primary",  "url": "http://127.0.0.1:8004", "endpoint": "/supplier/order_bahan",  "priority": 1},
        {"label": "mirror",   "url": "http://127.0.0.1:9004", "endpoint": "/supplier/order_bahan",  "priority": 2},
        {"label": "fallback", "url": "http://127.0.0.1:8004", "endpoint": "/supplier/fallback",     "priority": 3},
    ],
    "logistikita": [
        {"label": "primary",  "url": "http://127.0.0.1:8005", "endpoint": "/logistik/request_pengiriman", "priority": 1},
        {"label": "mirror",   "url": "http://127.0.0.1:9005", "endpoint": "/logistik/request_pengiriman", "priority": 2},
        {"label": "fallback", "url": "http://127.0.0.1:8005", "endpoint": "/logistik/fallback",          "priority": 3},
    ],
    "umkminsight": [
        {"label": "primary",  "url": "http://127.0.0.1:8006", "endpoint": "/insight/data_transaksi", "priority": 1},
        {"label": "mirror",   "url": "http://127.0.0.1:9006", "endpoint": "/insight/data_transaksi", "priority": 2},
        {"label": "fallback", "url": "http://127.0.0.1:8006", "endpoint": "/insight/fallback",       "priority": 3},
    ],
}


async def backtracking_route(app_id: str, data: dict, candidates: list, index: int = 0, trace: list = None):
    """
    ========================================
    ALGORITMA BACKTRACKING — Routing Failover
    ========================================

    Cara kerja:
    1. Coba candidate[index] (kirim HTTP request)
    2. Jika SUKSES → return hasil + trace perjalanan
    3. Jika GAGAL (timeout/connection error) → BACKTRACK
       → Panggil rekursif dengan index + 1
    4. BASE CASE: index >= len(candidates) → semua gagal

    Pruning:
    - Skip candidates yang diketahui mati (opsional, bisa ditambahkan)

    Complexity: O(n) dimana n = jumlah kandidat route per app

    Args:
        app_id     : ID aplikasi target (misal "smartbank")
        data       : Payload request yang akan dikirim
        candidates : List route candidates [{label, url, endpoint, priority}]
        index      : Index kandidat saat ini (untuk rekursi)
        trace      : Riwayat percobaan routing (untuk logging)

    Returns:
        dict berisi status, data response, trace backtracking, dll
    """
    if trace is None:
        trace = []

    # ── BASE CASE ──────────────────────────────────
    # Semua kandidat sudah dicoba, semuanya gagal
    if index >= len(candidates):
        return {
            "status": "gagal",
            "pesan": f"Semua {len(candidates)} route untuk '{app_id}' gagal setelah backtracking.",
            "kode": "ALL_ROUTES_EXHAUSTED",
            "trace": trace,
            "total_attempts": len(candidates),
            "algoritma": "backtracking"
        }

    candidate = candidates[index]
    full_url = f"{candidate['url']}{candidate['endpoint']}"

    # Step info untuk trace
    step = {
        "step": index + 1,
        "label": candidate["label"],
        "url": full_url,
        "priority": candidate["priority"],
    }

    try:
        # ── CONSTRAINT CHECK ──────────────────────
        # Coba kirim request ke candidate ini
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(full_url, json=data)
            result = response.json()

        # ── SOLUSI DITEMUKAN ──────────────────────
        step["status"] = "SUKSES"
        step["response_code"] = response.status_code
        step["aksi"] = "Route berhasil — solusi ditemukan!"
        trace.append(step)

        return {
            "status": "sukses",
            "data": result,
            "route_used": candidate["label"],
            "route_url": full_url,
            "trace": trace,
            "total_attempts": index + 1,
            "total_candidates": len(candidates),
            "algoritma": "backtracking"
        }

    except httpx.ConnectError:
        # ── BACKTRACK: Connection refused ─────────
        step["status"] = "GAGAL_BACKTRACK"
        step["error"] = "ConnectError"
        step["error_detail"] = f"Tidak bisa konek ke {full_url}"
        if index + 1 < len(candidates):
            next_candidate = candidates[index + 1]
            step["aksi"] = f"BACKTRACK → coba kandidat #{index + 2} ({next_candidate['label']})"
        else:
            step["aksi"] = "Semua kandidat habis — tidak ada lagi yang bisa dicoba"
        trace.append(step)

        # ── RECURSIVE CALL: Backtrack ke kandidat berikutnya ──
        return await backtracking_route(app_id, data, candidates, index + 1, trace)

    except httpx.TimeoutException:
        # ── BACKTRACK: Timeout ────────────────────
        step["status"] = "GAGAL_BACKTRACK"
        step["error"] = "TimeoutException"
        step["error_detail"] = f"Timeout setelah 5 detik menunggu {full_url}"
        if index + 1 < len(candidates):
            next_candidate = candidates[index + 1]
            step["aksi"] = f"BACKTRACK → coba kandidat #{index + 2} ({next_candidate['label']})"
        else:
            step["aksi"] = "Semua kandidat habis — tidak ada lagi yang bisa dicoba"
        trace.append(step)

        # ── RECURSIVE CALL: Backtrack ke kandidat berikutnya ──
        return await backtracking_route(app_id, data, candidates, index + 1, trace)

    except Exception as e:
        # ── BACKTRACK: Error lain ─────────────────
        step["status"] = "GAGAL_BACKTRACK"
        step["error"] = type(e).__name__
        step["error_detail"] = str(e)
        if index + 1 < len(candidates):
            next_candidate = candidates[index + 1]
            step["aksi"] = f"BACKTRACK → coba kandidat #{index + 2} ({next_candidate['label']})"
        else:
            step["aksi"] = "Semua kandidat habis — tidak ada lagi yang bisa dicoba"
        trace.append(step)

        # ── RECURSIVE CALL: Backtrack ke kandidat berikutnya ──
        return await backtracking_route(app_id, data, candidates, index + 1, trace)


async def route_dengan_backtracking(target_app: str, data: dict, custom_endpoint: str = None):
    """
    Wrapper utama — panggil backtracking_route() dengan candidates dari ROUTE_CANDIDATES.
    
    Jika target_app tidak ada di ROUTE_CANDIDATES, fallback ke single-route dari APP_URLS.
    """
    candidates = ROUTE_CANDIDATES.get(target_app)

    if not candidates:
        # Fallback: app tidak punya multi-route, pakai APP_URLS biasa
        base_url = APP_URLS.get(target_app)
        if not base_url:
            return {
                "status": "gagal",
                "pesan": f"Aplikasi '{target_app}' tidak dikenali oleh Gateway.",
                "pilihan": list(APP_URLS.keys()),
                "algoritma": "backtracking",
                "trace": []
            }
        # Buat single candidate dari APP_URLS
        endpoint = custom_endpoint or APP_DEFAULT_ENDPOINTS.get(target_app, "/")
        candidates = [
            {"label": "primary", "url": base_url, "endpoint": endpoint, "priority": 1}
        ]

    # Override endpoint kalau user kasih custom
    if custom_endpoint:
        candidates = [
            {**c, "endpoint": custom_endpoint} for c in candidates
        ]

    # Sortir berdasarkan priority (ascending)
    candidates = sorted(candidates, key=lambda c: c["priority"])

    # Jalankan algoritma backtracking
    return await backtracking_route(target_app, data, candidates)


def get_route_candidates_info():
    """Kembalikan info routing table backtracking untuk frontend"""
    result = []
    for app_id, candidates in ROUTE_CANDIDATES.items():
        info = APP_INFO.get(app_id, {})
        result.append({
            "app_id": app_id,
            "kelompok": info.get("kelompok", "—"),
            "peran": info.get("peran", "—"),
            "total_candidates": len(candidates),
            "candidates": [
                {
                    "label": c["label"],
                    "url": f"{c['url']}{c['endpoint']}",
                    "priority": c["priority"]
                }
                for c in sorted(candidates, key=lambda x: x["priority"])
            ]
        })
    return result