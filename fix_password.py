import bcrypt
import asyncio
import aiomysql

# Generate hash baru untuk "password123"
password = b"password123"
new_hash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode("utf-8")
print(f"Hash baru: {new_hash}")
print(f"Verifikasi: {bcrypt.checkpw(password, new_hash.encode())}")

# Cek hash lama dari DB
async def fix():
    conn = await aiomysql.connect(
        host="localhost", port=3306,
        user="root", password="",
        db="tugasgateaway", autocommit=True
    )
    async with conn.cursor(aiomysql.DictCursor) as cur:
        # Lihat hash lama
        await cur.execute("SELECT username, password_hash FROM users")
        users = await cur.fetchall()
        for u in users:
            old_hash = u["password_hash"]
            if old_hash.startswith("$2y$"):
                old_hash = "$2b$" + old_hash[4:]
            try:
                valid = bcrypt.checkpw(password, old_hash.encode())
                print(f"  {u['username']}: hash lama valid={valid}")
            except Exception as e:
                print(f"  {u['username']}: ERROR cek hash lama — {e}")

        # Update semua user dengan hash baru
        await cur.execute(
            "UPDATE users SET password_hash = %s WHERE username IN ('admin_gateway','operator_01','enduser_demo')",
            (new_hash,)
        )
        print(f"\n✅ Semua password diupdate ke 'password123'")
    conn.close()

asyncio.run(fix())
