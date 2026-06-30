import httpx
import asyncio
import time
from collections import defaultdict
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


# ==========================================
# ROUND ROBIN — Distribusi Beban (primary + mirror)
# Hanya mencakup kandidat yang identik fungsinya.
# Fallback tetap sebagai last resort backtracking.
# ==========================================

RR_POOL = {
    "smartbank": [
        {"label": "primary", "url": "http://127.0.0.1:8000", "endpoint": "/smartbank/pembayaran_transaksi"},
        {"label": "mirror",  "url": "http://127.0.0.1:9000", "endpoint": "/smartbank/pembayaran_transaksi"},
    ],
    "marketplace": [
        {"label": "primary", "url": "http://127.0.0.1:8002", "endpoint": "/marketplace/checkout"},
        {"label": "mirror",  "url": "http://127.0.0.1:9002", "endpoint": "/marketplace/checkout"},
    ],
    "pos": [
        {"label": "primary", "url": "http://127.0.0.1:8003", "endpoint": "/pos/transaksi"},
        {"label": "mirror",  "url": "http://127.0.0.1:9003", "endpoint": "/pos/transaksi"},
    ],
    "supplierhub": [
        {"label": "primary", "url": "http://127.0.0.1:8004", "endpoint": "/supplier/order_bahan"},
        {"label": "mirror",  "url": "http://127.0.0.1:9004", "endpoint": "/supplier/order_bahan"},
    ],
    "logistikita": [
        {"label": "primary", "url": "http://127.0.0.1:8005", "endpoint": "/logistik/request_pengiriman"},
        {"label": "mirror",  "url": "http://127.0.0.1:9005", "endpoint": "/logistik/request_pengiriman"},
    ],
    "umkminsight": [
        {"label": "primary", "url": "http://127.0.0.1:8006", "endpoint": "/insight/data_transaksi"},
        {"label": "mirror",  "url": "http://127.0.0.1:9006", "endpoint": "/insight/data_transaksi"},
    ],
}

# Counter giliran Round Robin per app (in-memory, reset saat server restart)
_rr_index: dict = defaultdict(int)


def get_next_rr_candidate(app_id: str) -> Optional[dict]:
    """
    Ambil kandidat berikutnya dari RR_POOL berdasarkan giliran.
    Thread-safe untuk single-process async (asyncio tidak multithreaded).

    Returns:
        dict kandidat {label, url, endpoint} atau None jika app tidak ada di pool
    """
    pool = RR_POOL.get(app_id, [])
    if not pool:
        return None
    idx = _rr_index[app_id] % len(pool)
    _rr_index[app_id] += 1
    return pool[idx]


def get_rr_stats() -> dict:
    """Kembalikan statistik Round Robin — berapa kali tiap index dipakai per app"""
    return {
        app_id: {
            "total_requests": count,
            "pool_size": len(RR_POOL.get(app_id, [])),
            "current_index": count % len(RR_POOL.get(app_id, [1])),
        }
        for app_id, count in _rr_index.items()
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


# ==========================================
# SMART SCORE — Heuristik Informed Backtracking
# Probe kandidat paralel + historis error rate
# untuk menentukan urutan optimal sebelum backtracking
# ==========================================

async def probe_single_candidate(candidate: dict) -> dict:
    """
    Probe satu kandidat route: ukur latency GET /health.
    Timeout 2 detik agar tidak menghambat terlalu lama.

    Returns:
        dict {label, url, latency_ms, alive}
    """
    health_url = f"{candidate['url']}/health"
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.get(health_url)
        latency_ms = (time.monotonic() - start) * 1000
        return {
            "label": candidate["label"],
            "url": candidate["url"],
            "latency_ms": round(latency_ms, 1),
            "alive": True,
        }
    except Exception:
        latency_ms = (time.monotonic() - start) * 1000
        return {
            "label": candidate["label"],
            "url": candidate["url"],
            "latency_ms": round(min(latency_ms, 2000), 1),  # cap di 2000ms
            "alive": False,
        }


async def smart_sort_candidates(candidates: list) -> tuple:
    """
    =========================================
    SMART SCORE HEURISTIC — Informed Backtracking
    =========================================

    Formula:
        score = (latency_norm x 0.4) + (error_rate x 0.4) + (priority_norm x 0.2)

        - latency_norm  = latency_ms / max_latency_semua_kandidat  [0.0 - 1.0]
        - error_rate    = dari api_health_log historis              [0.0 - 1.0]
        - priority_norm = priority / jumlah_kandidat               [0.0 - 1.0]

    Score RENDAH = kandidat LEBIH BAIK (dicoba pertama oleh backtracking)

    Returns:
        tuple (sorted_candidates, probe_results)
        - sorted_candidates : list kandidat terurut berdasarkan score
        - probe_results     : list dict berisi detail score tiap kandidat (untuk trace frontend)
    """
    from services.log_service import get_error_rate_for_url

    # ── PROBE SEMUA PARALEL ─────────────────────────────────
    probe_tasks = [probe_single_candidate(c) for c in candidates]
    probes = await asyncio.gather(*probe_tasks)

    # ── AMBIL ERROR RATE HISTORIS PARALEL ──────────────────
    error_rate_tasks = [get_error_rate_for_url(c["url"]) for c in candidates]
    error_rates = await asyncio.gather(*error_rate_tasks)

    # ── NORMALISASI & KALKULASI SCORE ──────────────────────
    max_latency = max((p["latency_ms"] for p in probes), default=1) or 1
    max_priority = len(candidates) or 1

    scored = []
    for i, candidate in enumerate(candidates):
        latency_norm  = probes[i]["latency_ms"] / max_latency
        error_rate    = error_rates[i]
        priority_norm = candidate["priority"] / max_priority

        score = (latency_norm * 0.4) + (error_rate * 0.4) + (priority_norm * 0.2)

        scored.append({
            "candidate": candidate,
            "score": round(score, 4),
            "probe": {
                "label":       candidate["label"],
                "url":         candidate["url"],
                "latency_ms":  probes[i]["latency_ms"],
                "alive":       probes[i]["alive"],
                "error_rate":  round(error_rate * 100, 1),   # dalam persen untuk frontend
                "priority":    candidate["priority"],
                "score":       round(score, 4),
                "latency_norm": round(latency_norm, 4),
                "priority_norm": round(priority_norm, 4),
            }
        })

    # ── SORT: score terkecil = kandidat pertama ─────────────
    scored.sort(key=lambda x: x["score"])

    sorted_candidates = [s["candidate"] for s in scored]
    probe_results     = [s["probe"] for s in scored]

    return sorted_candidates, probe_results


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
    =========================================
    INFORMED BACKTRACKING dengan SMART SCORE
    =========================================

    Wrapper utama yang menjalankan 2 phase:

    PHASE 1 — Smart Score Probe (paralel):
      - Probe GET /health semua kandidat sekaligus
      - Ambil historis error rate dari api_health_log
      - Hitung score gabungan (latency + error_rate + priority)
      - Sort kandidat dari score terkecil (terbaik)

    PHASE 2 — Backtracking (sequential):
      - Coba kandidat urutan Smart Score
      - Backtrack jika gagal
      - Return trace + probe_results untuk visualisasi

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
                "trace": [],
                "probe_results": [],
            }
        # Buat single candidate dari APP_URLS
        endpoint = custom_endpoint or APP_DEFAULT_ENDPOINTS.get(target_app, "/")
        candidates = [
            {"label": "primary", "url": base_url, "endpoint": endpoint, "priority": 1}
        ]

    # Override endpoint kalau user kasih custom
    if custom_endpoint:
        candidates = [{**c, "endpoint": custom_endpoint} for c in candidates]

    # ── PHASE 1: SMART SCORE — sort kandidat secara cerdas ──
    try:
        sorted_candidates, probe_results = await smart_sort_candidates(candidates)
    except Exception as e:
        print(f"[WARN] Smart Score gagal ({e}), fallback ke priority sort")
        sorted_candidates = sorted(candidates, key=lambda c: c["priority"])
        probe_results = []

    # ── PHASE 2: BACKTRACKING dengan urutan Smart Score ──────
    result = await backtracking_route(target_app, data, sorted_candidates)

    # Inject probe_results ke dalam result untuk frontend
    result["probe_results"] = probe_results
    result["algoritma"] = "informed_backtracking_smart_score"

    return result


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


async def route_dengan_round_robin(app_id: str, data: dict) -> dict:
    """
    =========================================
    ROUND ROBIN ROUTING dengan BACKTRACKING FALLBACK
    =========================================

    Cara kerja:
    1. Pilih kandidat berikutnya dari RR_POOL (primary ↔ mirror, bergantian)
    2. Coba kirim request ke kandidat terpilih
    3. Sukses → return result + info RR
    4. Gagal → backtrack ke kandidat lain di ROUTE_CANDIDATES
       (termasuk fallback yang tidak ada di RR pool)

    Args:
        app_id : ID aplikasi target
        data   : Payload request

    Returns:
        dict response + rr_candidate_used + routing_mode
    """
    import time as _time

    # Ambil kandidat giliran Round Robin
    rr_candidate = get_next_rr_candidate(app_id)

    if not rr_candidate:
        # App tidak ada di RR_POOL — fallback ke routing biasa
        return await teruskan_ke_app(app_id, data)

    full_url = f"{rr_candidate['url']}{rr_candidate['endpoint']}"
    rr_label = rr_candidate["label"]

    start = _time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(full_url, json=data)
            result = response.json()
        latency_ms = round((_time.monotonic() - start) * 1000, 1)

        return {
            "status": "sukses",
            "data": result,
            "routing_mode": "round_robin",
            "rr_candidate_used": rr_label,
            "rr_url": full_url,
            "latency_ms": latency_ms,
            "rr_stats": get_rr_stats().get(app_id, {}),
        }

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        latency_ms = round((_time.monotonic() - start) * 1000, 1)
        print(f"[WARN] RR candidate '{rr_label}' ({full_url}) gagal: {type(e).__name__}. Fallback ke backtracking.")

        # ── BACKTRACKING FALLBACK ──────────────────────────────
        # Ambil semua kandidat kecuali yang sudah dicoba RR
        all_candidates = ROUTE_CANDIDATES.get(app_id, [])
        fallback_candidates = [
            c for c in all_candidates
            if c["url"] != rr_candidate["url"]
        ]

        if not fallback_candidates:
            return {
                "status": "gagal",
                "pesan": f"RR candidate '{rr_label}' gagal dan tidak ada fallback tersedia.",
                "routing_mode": "round_robin",
                "rr_candidate_used": rr_label,
                "error": type(e).__name__,
                "latency_ms": latency_ms,
            }

        # Sortir fallback berdasarkan priority
        fallback_candidates = sorted(fallback_candidates, key=lambda c: c["priority"])

        # Jalankan backtracking dari fallback candidates
        fallback_result = await backtracking_route(app_id, data, fallback_candidates)
        fallback_result["routing_mode"] = "round_robin+backtracking_fallback"
        fallback_result["rr_candidate_tried"] = rr_label
        fallback_result["rr_url_tried"] = full_url
        return fallback_result

    except Exception as e:
        return {
            "status": "gagal",
            "pesan": f"Error tidak terduga di RR routing: {str(e)}",
            "routing_mode": "round_robin",
            "rr_candidate_used": rr_label,
            "error": type(e).__name__,
        }