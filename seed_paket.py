import asyncio
import aiomysql

async def seed():
    conn = await aiomysql.connect(host='localhost', port=3306, user='root', password='', autocommit=True)
    async with conn.cursor() as cur:
        await cur.execute('USE TugasGateaway')

        # Buat tabel pricing_plans
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
        print("[OK] Tabel pricing_plans siap")

        # Buat tabel registered_apps
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
        print("[OK] Tabel registered_apps siap")

        # Seed paket harga
        await cur.execute('SELECT COUNT(*) FROM pricing_plans')
        count = (await cur.fetchone())[0]
        if count == 0:
            paket_data = [
                ('Starter',    0,      500,    0.500, False, True,  True,  True,  False, 'Paket gratis untuk coba-coba. Akses endpoint validasi & logging saja.'),
                ('Basic',      50000,  5000,   0.500, True,  True,  True,  True,  False, 'Paket UMKM kecil. Sudah bisa routing transaksi ke SmartBank.'),
                ('Pro',        200000, 50000,  0.400, True,  True,  True,  True,  True,  'Paket profesional. Fee lebih hemat & akses monitor penuh.'),
                ('Enterprise', 500000, -1,     0.300, True,  True,  True,  True,  True,  'Kuota unlimited. Fee terendah. Cocok untuk platform besar.'),
            ]
            await cur.executemany("""
                INSERT INTO pricing_plans 
                (nama_paket, harga_per_bulan, quota_per_bulan, fee_transaksi_persen,
                 akses_routing, akses_validasi, akses_logging, akses_biaya, akses_monitor, deskripsi)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, paket_data)
            print(f"[OK] Seed {len(paket_data)} paket harga berhasil dimasukkan!")
        else:
            print(f"[INFO] Paket sudah ada ({count} data), skip seed.")

    conn.close()
    print("[DONE] Selesai!")

asyncio.run(seed())
