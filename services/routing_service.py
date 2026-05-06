import httpx

# Ini daftar alamat aplikasi lain (nanti lu ganti sesuai IP temen kelompok lu)
URL_SMARTBANK = "http://127.0.0.1:8000/smartbank/pembayaran_transaksi"

async def teruskan_ke_smartbank(data_transaksi: dict):
    """Fungsi Algoritma Routing untuk meneruskan request ke SmartBank"""
    async with httpx.AsyncClient() as client:
        try:
            # Di sini proses forwarding terjadi
            response = await client.post(URL_SMARTBANK, json=data_transaksi)
            return response.json()
        except Exception as e:
            return {"status": "gagal", "pesan": f"Gagal konek ke SmartBank: {str(e)}"}