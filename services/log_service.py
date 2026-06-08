import aiomysql
from datetime import datetime

# ==========================================
# KONFIGURASI MySQL (Laragon)
# ==========================================
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "db": "TugasGateway",
}

# ==========================================
# INISIALISASI — Buat tabel otomatis
# ==========================================
async def init_db():
    """Buat database dan tabel kalau belum ada"""
    try:
        # Konek dulu tanpa specify database
        conn = await aiomysql.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            autocommit=True
        )
        async with conn.cursor() as cur:
            # Buat database kalau belum ada
            await cur.execute("CREATE DATABASE IF NOT EXISTS TugasGateway")
            await cur.execute("USE TugasGateway")

            # Tabel 1: logs_transaksi (lama)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS logs_transaksi (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(100),
                    endpoint VARCHAR(200),
                    waktu DATETIME,
                    detail JSON
                )
            """)

            # Tabel 2: api_request_log (baru)
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS api_request_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME,
                    user_id VARCHAR(100),
                    source_app VARCHAR(100),
                    endpoint VARCHAR(200),
                    amount DECIMAL(15,2),
                    fee DECIMAL(15,2),
                    jwt_valid BOOLEAN,
                    smartbank_status VARCHAR(50),
                    response_time_ms INT,
                    status_gateway VARCHAR(20)
                )
            """)

            # Tabel 3: api_health_log
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS api_health_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME,
                    app_name VARCHAR(100),
                    endpoint VARCHAR(200),
                    status VARCHAR(20),
                    response_time_ms INT,
                    status_code INT,
                    error_message TEXT
                )
            """)

            # Tabel 4: pricing_plans — definisi paket harga
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS pricing_plans (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nama_paket VARCHAR(50) UNIQUE NOT NULL,
                    harga_per_bulan DECIMAL(12,2) NOT NULL DEFAULT 0,
                    quota_per_bulan INT NOT NULL DEFAULT 500,
                    fee_transaksi_persen DECIMAL(5,3) NOT NULL DEFAULT 0.500,
                    akses_routing BOOLEAN NOT NULL DEFAULT FALSE,
                    akses_validasi BOOLEAN NOT NULL DEFAULT TRUE,
                    akses_logging BOOLEAN NOT NULL DEFAULT TRUE,
                    akses_biaya BOOLEAN NOT NULL DEFAULT TRUE,
                    akses_monitor BOOLEAN NOT NULL DEFAULT FALSE,
                    deskripsi TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabel 5: registered_apps — app yang berlangganan
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS registered_apps (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    app_name VARCHAR(100) NOT NULL,
                    api_key VARCHAR(64) UNIQUE NOT NULL,
                    nama_paket VARCHAR(50) NOT NULL DEFAULT 'Starter',
                    quota_sisa INT NOT NULL DEFAULT 500,
                    quota_reset_date DATE,
                    aktif_sampai DATE,
                    total_request INT NOT NULL DEFAULT 0,
                    total_fee_dibayar DECIMAL(15,2) NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'aktif',
                    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (nama_paket) REFERENCES pricing_plans(nama_paket)
                )
            """)

            # Seed data paket harga (kalau belum ada)
            await cur.execute("SELECT COUNT(*) as c FROM pricing_plans")
            row = await cur.fetchone()
            if row[0] == 0:
                await cur.executemany("""
                    INSERT INTO pricing_plans 
                    (nama_paket, harga_per_bulan, quota_per_bulan, fee_transaksi_persen,
                     akses_routing, akses_validasi, akses_logging, akses_biaya, akses_monitor, deskripsi)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    ('Starter',    0,      500,    0.500, False, True,  True,  True,  False, 'Paket gratis untuk coba-coba. Akses endpoint validasi & logging saja.'),
                    ('Basic',      50000,  5000,   0.500, True,  True,  True,  True,  False, 'Paket harian untuk UMKM kecil. Sudah bisa routing transaksi ke SmartBank.'),
                    ('Pro',        200000, 50000,  0.400, True,  True,  True,  True,  True,  'Paket profesional. Fee lebih hemat & akses monitor penuh.'),
                    ('Enterprise', 500000, -1,     0.300, True,  True,  True,  True,  True,  'Kuota unlimited. Fee terendah. Cocok untuk platform besar.'),
                ])
                print("[OK] Seed data 4 paket harga berhasil dimasukkan!")

        conn.close()
        print("[OK] Database TugasGateway & semua tabel siap!")
        # Buat tabel backtracking_log
        await init_backtracking_table()
    except Exception as e:
        print(f"[ERROR] Gagal init database: {e}")


async def get_conn():
    """Helper: buat koneksi MySQL"""
    # Pastikan kita tidak mengirimkan `autocommit` dua kali jika sudah ada
    cfg = DB_CONFIG.copy()
    cfg.pop("autocommit", None)
    return await aiomysql.connect(**cfg, autocommit=True)


# ==========================================
# FUNGSI LAMA (tetap jalan seperti biasa)
# ==========================================

async def catat_log_mongo(user_id: str, endpoint: str, data_tambahan: dict = None):
    """Catat log ke tabel logs_transaksi"""
    import json
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO logs_transaksi (user_id, endpoint, waktu, detail) VALUES (%s, %s, %s, %s)",
                (user_id, endpoint, datetime.now(), json.dumps(data_tambahan) if data_tambahan else None)
            )
        conn.close()
        print(f"[OK] Log {user_id} berhasil disimpan ke MySQL!")
    except Exception as e:
        print(f"[ERROR] Gagal simpan log: {e}")


def hitung_fee_gateway(amount: float):
    """Hitung fee 0.5%"""
    return amount * 0.005


# ==========================================
# FUNGSI BARU #1 — Catat request detail
# ==========================================

async def catat_request_log(
    user_id: str, source_app: str, endpoint: str,
    amount: float, fee: float, jwt_valid: bool,
    smartbank_status: str, response_time_ms: int
):
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO api_request_log 
                (timestamp, user_id, source_app, endpoint, amount, fee, jwt_valid, smartbank_status, response_time_ms, status_gateway)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.now(), user_id, source_app, endpoint,
                amount, fee, jwt_valid, smartbank_status, response_time_ms,
                "SUCCESS" if smartbank_status == "sukses" else "FAILED"
            ))
        conn.close()
        print(f"[OK] Request log {user_id} dari {source_app} tersimpan di MySQL!")
    except Exception as e:
        print(f"[ERROR] Gagal simpan request log: {e}")


# ==========================================
# FUNGSI BARU #2 — Catat hasil cek API
# ==========================================

async def catat_health_log(
    app_name: str, endpoint: str, status: str,
    response_time_ms: int, status_code: int = None, error_message: str = None
):
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO api_health_log 
                (timestamp, app_name, endpoint, status, response_time_ms, status_code, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.now(), app_name, endpoint,
                status, response_time_ms, status_code, error_message
            ))
        conn.close()
        print(f"[OK] Health log {app_name} → {status} tersimpan di MySQL!")
    except Exception as e:
        print(f"[ERROR] Gagal simpan health log: {e}")


# ==========================================
# FUNGSI BARU #3 — Ambil statistik dashboard
# ==========================================

async def get_request_stats():
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT COUNT(*) as total FROM api_request_log")
            total = (await cur.fetchone())["total"]

            await cur.execute("SELECT COUNT(*) as c FROM api_request_log WHERE status_gateway = 'SUCCESS'")
            sukses = (await cur.fetchone())["c"]

            await cur.execute("SELECT COUNT(*) as c FROM api_request_log WHERE status_gateway = 'FAILED'")
            gagal = (await cur.fetchone())["c"]

            await cur.execute("SELECT COALESCE(SUM(fee), 0) as total_fee FROM api_request_log")
            total_fee = float((await cur.fetchone())["total_fee"])

            await cur.execute("SELECT COALESCE(AVG(response_time_ms), 0) as avg_ms FROM api_request_log")
            avg_ms = float((await cur.fetchone())["avg_ms"])

            await cur.execute("""
                SELECT source_app, COUNT(*) as c FROM api_request_log 
                GROUP BY source_app ORDER BY c DESC LIMIT 1
            """)
            top_row = await cur.fetchone()
            top_source = top_row["source_app"] if top_row else "—"

            await cur.execute("SELECT COUNT(*) as c FROM api_request_log WHERE jwt_valid = 1")
            jwt_valid = (await cur.fetchone())["c"]

            await cur.execute("SELECT COUNT(*) as c FROM api_request_log WHERE jwt_valid = 0")
            jwt_invalid = (await cur.fetchone())["c"]

            await cur.execute("SELECT COUNT(*) as c FROM api_request_log WHERE smartbank_status = 'sukses'")
            smartbank_ok = (await cur.fetchone())["c"]

            await cur.execute("""
                SELECT * FROM api_request_log 
                ORDER BY timestamp DESC LIMIT 10
            """)
            recent = await cur.fetchall()
            for r in recent:
                if r.get("timestamp"):
                    r["timestamp"] = r["timestamp"].isoformat()
                r["amount"] = float(r["amount"] or 0)
                r["fee"] = float(r["fee"] or 0)

        conn.close()
        return {
            "total_requests": total,
            "sukses": sukses,
            "gagal": gagal,
            "total_fee": total_fee,
            "avg_response_ms": avg_ms,
            "top_source_app": top_source,
            "jwt_valid_count": jwt_valid,
            "jwt_invalid_count": jwt_invalid,
            "smartbank_ok": smartbank_ok,
            "recent_logs": list(recent)
        }
    except Exception as e:
        return {"error": str(e)}


async def get_health_stats():
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT * FROM api_health_log 
                ORDER BY timestamp DESC LIMIT 20
            """)
            rows = await cur.fetchall()
            for r in rows:
                if r.get("timestamp"):
                    r["timestamp"] = r["timestamp"].isoformat()
        conn.close()
        return list(rows)
    except Exception as e:
        return []


# ==========================================
# FUNGSI PRICING — Sistem Paket Harga
# ==========================================

import secrets
from datetime import date, timedelta

async def get_all_paket():
    """Ambil semua paket harga yang tersedia"""
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT nama_paket, harga_per_bulan, quota_per_bulan, fee_transaksi_persen,
                       akses_routing, akses_validasi, akses_logging, akses_biaya, akses_monitor, deskripsi
                FROM pricing_plans ORDER BY harga_per_bulan ASC
            """)
            rows = await cur.fetchall()
        conn.close()
        for r in rows:
            r["harga_per_bulan"] = float(r["harga_per_bulan"])
            r["fee_transaksi_persen"] = float(r["fee_transaksi_persen"])
            r["quota_label"] = "Unlimited" if r["quota_per_bulan"] == -1 else str(r["quota_per_bulan"])
        return list(rows)
    except Exception as e:
        print(f"[ERROR] Gagal ambil paket: {e}")
        return []


async def registrasi_app(app_name: str, nama_paket: str):
    """Daftarkan app baru, generate API key, set quota awal"""
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Cek paket ada atau tidak
            await cur.execute("SELECT * FROM pricing_plans WHERE nama_paket = %s", (nama_paket,))
            paket = await cur.fetchone()
            if not paket:
                conn.close()
                return {"sukses": False, "pesan": f"Paket '{nama_paket}' tidak ditemukan"}

            # Generate API key unik
            api_key = f"{app_name[:3].lower()}_{secrets.token_hex(16)}"

            # Hitung tanggal aktif (30 hari ke depan)
            tgl_reset = date.today() + timedelta(days=30)
            quota_awal = paket["quota_per_bulan"]

            await cur.execute("""
                INSERT INTO registered_apps 
                (app_name, api_key, nama_paket, quota_sisa, quota_reset_date, aktif_sampai, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'aktif')
            """, (app_name, api_key, nama_paket, quota_awal, tgl_reset, tgl_reset))

        conn.close()
        print(f"[OK] App '{app_name}' berhasil daftar paket {nama_paket}!")
        return {
            "sukses": True,
            "pesan": f"App '{app_name}' berhasil didaftarkan!",
            "api_key": api_key,
            "paket": nama_paket,
            "quota_awal": quota_awal if quota_awal != -1 else "Unlimited",
            "aktif_sampai": tgl_reset.isoformat()
        }
    except Exception as e:
        print(f"[ERROR] Gagal registrasi app: {e}")
        return {"sukses": False, "pesan": str(e)}


async def cek_akses_app(api_key: str, endpoint: str):
    """Cek apakah app boleh akses endpoint tertentu & masih ada quota"""
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Ambil data app + paketnya
            await cur.execute("""
                SELECT ra.*, pp.quota_per_bulan, pp.fee_transaksi_persen,
                       pp.akses_routing, pp.akses_validasi, pp.akses_logging,
                       pp.akses_biaya, pp.akses_monitor, pp.harga_per_bulan
                FROM registered_apps ra
                JOIN pricing_plans pp ON ra.nama_paket = pp.nama_paket
                WHERE ra.api_key = %s
            """, (api_key,))
            app = await cur.fetchone()

        conn.close()

        if not app:
            return {"boleh": False, "pesan": "API Key tidak dikenali. Daftar dulu di /apps/register", "app": None}

        if app["status"] != "aktif":
            return {"boleh": False, "pesan": "Langganan tidak aktif. Perpanjang paket Anda.", "app": app}

        # Cek apakah paket sudah expired
        if app["aktif_sampai"] and app["aktif_sampai"] < date.today():
            return {"boleh": False, "pesan": "Paket sudah expired. Silakan perpanjang.", "app": app}

        # Mapping endpoint ke kolom akses
        akses_map = {
            "/integrator/routing_api":            "akses_routing",
            "/integrator/validasi_request":       "akses_validasi",
            "/integrator/logging":                "akses_logging",
            "/integrator/biaya_layanan_integrasi":"akses_biaya",
            "/monitor/health-stats":              "akses_monitor",
            "/monitor/request-stats":             "akses_monitor",
            "/monitor/health-check":              "akses_monitor",
        }
        kolom_akses = akses_map.get(endpoint)
        if kolom_akses and not app[kolom_akses]:
            return {"boleh": False, "pesan": f"Paket '{app['nama_paket']}' tidak bisa akses endpoint ini. Upgrade paket Anda!", "app": app}

        # Cek quota (skip kalau unlimited / -1)
        if app["quota_per_bulan"] != -1 and app["quota_sisa"] <= 0:
            return {"boleh": False, "pesan": f"Quota habis! Sisa: 0 dari {app['quota_per_bulan']} req/bulan. Upgrade paket atau tunggu reset bulan depan.", "app": app}

        return {
            "boleh": True,
            "pesan": "Akses diizinkan",
            "app": app,
            "fee_persen": float(app["fee_transaksi_persen"])
        }
    except Exception as e:
        print(f"[ERROR] Gagal cek akses: {e}")
        return {"boleh": False, "pesan": str(e), "app": None}


async def kurangi_quota(api_key: str):
    """Kurangi quota app sebanyak 1 setelah request berhasil"""
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            # Hanya kurangi kalau bukan unlimited (-1)
            await cur.execute("""
                UPDATE registered_apps 
                SET quota_sisa = GREATEST(quota_sisa - 1, 0),
                    total_request = total_request + 1
                WHERE api_key = %s 
                AND (SELECT quota_per_bulan FROM pricing_plans WHERE nama_paket = registered_apps.nama_paket) != -1
            """, (api_key,))
            # Untuk unlimited, hanya update total_request
            await cur.execute("""
                UPDATE registered_apps 
                SET total_request = total_request + 1
                WHERE api_key = %s 
                AND (SELECT quota_per_bulan FROM pricing_plans WHERE nama_paket = registered_apps.nama_paket) = -1
            """, (api_key,))
        conn.close()
    except Exception as e:
        print(f"[ERROR] Gagal kurangi quota: {e}")


async def tambah_fee_app(api_key: str, fee: float):
    """Catat total fee yang sudah dibayar app"""
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute("""
                UPDATE registered_apps SET total_fee_dibayar = total_fee_dibayar + %s
                WHERE api_key = %s
            """, (fee, api_key))
        conn.close()
    except Exception as e:
        print(f"[ERROR] Gagal update fee app: {e}")


async def get_status_app(api_key: str):
    """Ambil info lengkap status langganan sebuah app"""
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT ra.app_name, ra.api_key, ra.nama_paket, ra.quota_sisa,
                       ra.quota_reset_date, ra.aktif_sampai, ra.total_request,
                       ra.total_fee_dibayar, ra.status, ra.registered_at,
                       pp.harga_per_bulan, pp.quota_per_bulan, pp.fee_transaksi_persen,
                       pp.akses_routing, pp.akses_validasi, pp.akses_logging,
                       pp.akses_biaya, pp.akses_monitor
                FROM registered_apps ra
                JOIN pricing_plans pp ON ra.nama_paket = pp.nama_paket
                WHERE ra.api_key = %s
            """, (api_key,))
            app = await cur.fetchone()
        conn.close()

        if not app:
            return None

        # Serialize tanggal & decimal
        for field in ["quota_reset_date", "aktif_sampai", "registered_at"]:
            if app.get(field):
                app[field] = app[field].isoformat() if hasattr(app[field], 'isoformat') else str(app[field])
        app["harga_per_bulan"] = float(app["harga_per_bulan"])
        app["fee_transaksi_persen"] = float(app["fee_transaksi_persen"])
        app["total_fee_dibayar"] = float(app["total_fee_dibayar"])
        app["quota_label"] = "Unlimited" if app["quota_per_bulan"] == -1 else str(app["quota_per_bulan"])
        return dict(app)
    except Exception as e:
        print(f"[ERROR] Gagal get status app: {e}")
        return None


async def upgrade_paket_app(api_key: str, paket_baru: str):
    """Upgrade paket langganan app ke paket lebih tinggi"""
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Cek paket baru ada?
            await cur.execute("SELECT * FROM pricing_plans WHERE nama_paket = %s", (paket_baru,))
            paket = await cur.fetchone()
            if not paket:
                conn.close()
                return {"sukses": False, "pesan": f"Paket '{paket_baru}' tidak ditemukan"}

            tgl_baru = date.today() + timedelta(days=30)
            await cur.execute("""
                UPDATE registered_apps 
                SET nama_paket = %s, quota_sisa = %s, aktif_sampai = %s, quota_reset_date = %s
                WHERE api_key = %s
            """, (paket_baru, paket["quota_per_bulan"], tgl_baru, tgl_baru, api_key))

        conn.close()
        return {
            "sukses": True,
            "pesan": f"Berhasil upgrade ke paket {paket_baru}!",
            "paket_baru": paket_baru,
            "quota_baru": paket["quota_per_bulan"] if paket["quota_per_bulan"] != -1 else "Unlimited",
            "aktif_sampai": tgl_baru.isoformat()
        }
    except Exception as e:
        print(f"[ERROR] Gagal upgrade paket: {e}")
        return {"sukses": False, "pesan": str(e)}


# ==========================================
# FUNGSI BACKTRACKING — Logging & Statistik
# ==========================================

async def init_backtracking_table():
    """Buat tabel backtracking_log kalau belum ada (dipanggil dari init_db)"""
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS backtracking_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME,
                    user_id VARCHAR(100),
                    target_app VARCHAR(100),
                    total_candidates INT,
                    total_attempts INT,
                    route_used VARCHAR(50),
                    final_status VARCHAR(20),
                    trace JSON,
                    response_time_ms INT
                )
            """)
        conn.close()
        print("[OK] Tabel backtracking_log siap!")
    except Exception as e:
        print(f"[ERROR] Gagal buat tabel backtracking_log: {e}")


async def catat_backtracking_log(
    user_id: str, target_app: str, total_candidates: int,
    total_attempts: int, route_used: str, final_status: str,
    trace: list, response_time_ms: int
):
    """Catat hasil backtracking routing ke MySQL"""
    import json
    try:
        conn = await get_conn()
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO backtracking_log 
                (timestamp, user_id, target_app, total_candidates, total_attempts,
                 route_used, final_status, trace, response_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.now(), user_id, target_app, total_candidates,
                total_attempts, route_used or "none", final_status,
                json.dumps(trace), response_time_ms
            ))
        conn.close()
        print(f"[OK] Backtracking log {user_id} → {target_app} ({final_status}) tersimpan!")
    except Exception as e:
        print(f"[ERROR] Gagal simpan backtracking log: {e}")


async def get_backtracking_stats():
    """Ambil statistik backtracking untuk dashboard"""
    import json
    try:
        conn = await get_conn()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Total backtracking attempts
            await cur.execute("SELECT COUNT(*) as total FROM backtracking_log")
            total = (await cur.fetchone())["total"]

            # Sukses vs gagal
            await cur.execute("SELECT COUNT(*) as c FROM backtracking_log WHERE final_status = 'sukses'")
            sukses = (await cur.fetchone())["c"]

            await cur.execute("SELECT COUNT(*) as c FROM backtracking_log WHERE final_status = 'gagal'")
            gagal = (await cur.fetchone())["c"]

            # Average attempts
            await cur.execute("SELECT COALESCE(AVG(total_attempts), 0) as avg_att FROM backtracking_log")
            avg_attempts = float((await cur.fetchone())["avg_att"])

            # Backtrack events (attempts > 1 means backtracking occurred)
            await cur.execute("SELECT COUNT(*) as c FROM backtracking_log WHERE total_attempts > 1")
            backtrack_count = (await cur.fetchone())["c"]

            # Average response time
            await cur.execute("SELECT COALESCE(AVG(response_time_ms), 0) as avg_ms FROM backtracking_log")
            avg_ms = float((await cur.fetchone())["avg_ms"])

            # Most common route_used
            await cur.execute("""
                SELECT route_used, COUNT(*) as c FROM backtracking_log 
                WHERE final_status = 'sukses'
                GROUP BY route_used ORDER BY c DESC LIMIT 3
            """)
            top_routes = await cur.fetchall()

            # Per-app breakdown
            await cur.execute("""
                SELECT target_app, 
                       COUNT(*) as total,
                       SUM(CASE WHEN final_status = 'sukses' THEN 1 ELSE 0 END) as sukses,
                       SUM(CASE WHEN final_status = 'gagal' THEN 1 ELSE 0 END) as gagal,
                       AVG(total_attempts) as avg_attempts
                FROM backtracking_log 
                GROUP BY target_app
            """)
            per_app = await cur.fetchall()
            for row in per_app:
                row["avg_attempts"] = float(row["avg_attempts"])

            # Recent logs (last 20)
            await cur.execute("""
                SELECT * FROM backtracking_log 
                ORDER BY timestamp DESC LIMIT 20
            """)
            recent = await cur.fetchall()
            for r in recent:
                if r.get("timestamp"):
                    r["timestamp"] = r["timestamp"].isoformat()
                # Parse trace JSON string
                if r.get("trace") and isinstance(r["trace"], str):
                    try:
                        r["trace"] = json.loads(r["trace"])
                    except Exception:
                        pass

        conn.close()
        return {
            "total_requests": total,
            "sukses": sukses,
            "gagal": gagal,
            "success_rate": round((sukses / total * 100), 1) if total > 0 else 0,
            "backtrack_count": backtrack_count,
            "avg_attempts": round(avg_attempts, 2),
            "avg_response_ms": round(avg_ms, 1),
            "top_routes": list(top_routes),
            "per_app": list(per_app),
            "recent_logs": list(recent)
        }
    except Exception as e:
        print(f"[ERROR] Gagal ambil backtracking stats: {e}")
        return {"error": str(e)}