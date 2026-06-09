// ===== AUTH CHECK =====
if (localStorage.getItem('gateway_logged_in') !== 'true') {
  window.location.href = '/login';
}

// ===== KONFIGURASI =====
const API_BASE = window.location.origin;

// ===== LOGOUT =====
function logout() {
  localStorage.removeItem('gateway_logged_in');
  localStorage.removeItem('gateway_user');
  localStorage.removeItem('gateway_username');
  window.location.href = '/';
}

// ===== NAVIGASI =====
function showPage(pageId) {
  const role = localStorage.getItem('gateway_role') || 'end_user';
  if (pageId === 'transaksi' && role === 'operator') {
    showToast('Akses Ditolak: Operator tidak diizinkan mengirim transaksi.', 'error');
    return;
  }

  document.querySelectorAll('.page-section').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById('page-' + pageId);
  const nav = document.getElementById('nav-' + pageId);
  if (page) page.classList.add('active');
  if (nav) nav.classList.add('active');

  // Close sidebar on mobile
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ===== TOAST NOTIFICATIONS =====
const toastIcons = {
  success: `<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>`,
  error:   `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  info:    `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
};

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.innerHTML = `<span class="toast-icon">${toastIcons[type] || toastIcons.info}</span><span class="toast-message">${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ===== FORMAT RUPIAH =====
function formatRupiah(angka) {
  return 'Rp ' + Number(angka).toLocaleString('id-ID');
}

// ===== CEK SERVER =====
async function cekServer() {
  const dot = document.getElementById('serverDot');
  const status = document.getElementById('serverStatus');
  try {
    const res = await fetch(API_BASE + '/docs', { method: 'HEAD', signal: AbortSignal.timeout(3000) });
    dot.classList.remove('offline');
    status.textContent = 'Server Online';
  } catch {
    dot.classList.add('offline');
    status.textContent = 'Server Offline';
  }
}

// ===== GENERATE TOKEN =====
async function generateToken() {
  const userId = document.getElementById('tokenUserId').value.trim();
  if (!userId) {
    showToast('Masukkan User ID terlebih dahulu!', 'error');
    return;
  }

  const btn = document.getElementById('btnGenerateToken');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Generating...';

  try {
    const res = await fetch(API_BASE + '/generate_token_tester/' + encodeURIComponent(userId));
    const data = await res.json();

    document.getElementById('tokenValue').textContent = data.token_buat_ngetes;
    document.getElementById('tokenResult').style.display = 'block';
    showToast('Token berhasil di-generate!', 'success');
  } catch (err) {
    showToast('Gagal generate token: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg> Generate Token`;
  }
}

// ===== COPY TOKEN =====
function copyToken() {
  const token = document.getElementById('tokenValue').textContent;
  navigator.clipboard.writeText(token).then(() => {
    showToast('Token berhasil disalin!', 'success');
  }).catch(() => {
    const textarea = document.createElement('textarea');
    textarea.value = token;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('Token berhasil disalin!', 'success');
  });
}

// ===== KIRIM TRANSAKSI =====
async function kirimTransaksi() {
  const userId = document.getElementById('txUserId').value.trim();
  const amount = parseFloat(document.getElementById('txAmount').value) || 0;
  const token = document.getElementById('txToken').value.trim();
  const metadataRaw = document.getElementById('txMetadata').value.trim();

  if (!userId) { showToast('User ID wajib diisi!', 'error'); return; }
  if (!token)  { showToast('Token JWT wajib diisi!', 'error'); return; }
  if (amount <= 0) { showToast('Jumlah harus lebih dari 0!', 'error'); return; }

  let parameter = { token: token, amount: amount };

  if (metadataRaw) {
    try {
      const extra = JSON.parse(metadataRaw);
      parameter = { ...parameter, ...extra };
    } catch {
      showToast('Format metadata JSON tidak valid!', 'error');
      return;
    }
  }

  const body = { user_id: userId, parameter: parameter };

  const btn = document.getElementById('btnKirimTransaksi');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Mengirim...';

  const startTime = Date.now();
  document.getElementById('txResponseCard').style.display = 'block';
  document.getElementById('txResponseStatus').className = 'response-status pending';
  document.getElementById('txResponseStatus').innerHTML = '<span class="status-pill" style="background:var(--accent-amber);"></span> Memproses...';
  document.getElementById('txResponseBody').textContent = 'Mengirim request ke server...';

  try {
    const res = await fetch(API_BASE + '/integrator/routing_api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    const data = await res.json();
    const elapsed = Date.now() - startTime;

    document.getElementById('txResponseTime').textContent = elapsed + 'ms';
    document.getElementById('txResponseBody').textContent = JSON.stringify(data, null, 2);

    if (data.status === 'sukses') {
      document.getElementById('txResponseStatus').className = 'response-status success';
      document.getElementById('txResponseStatus').innerHTML = '<span class="status-pill" style="background:var(--accent-emerald);"></span> Sukses';
      showToast('Transaksi berhasil diproses!', 'success');
    } else {
      document.getElementById('txResponseStatus').className = 'response-status error';
      document.getElementById('txResponseStatus').innerHTML = '<span class="status-pill" style="background:var(--accent-rose);"></span> Gagal';
      showToast('Transaksi gagal: ' + (data.data?.pesan || 'Unknown error'), 'error');
    }
  } catch (err) {
    document.getElementById('txResponseStatus').className = 'response-status error';
    document.getElementById('txResponseStatus').innerHTML = '<span class="status-pill" style="background:var(--accent-rose);"></span> Error';
    document.getElementById('txResponseBody').textContent = 'Error: ' + err.message;
    document.getElementById('txResponseTime').textContent = (Date.now() - startTime) + 'ms';
    showToast('Gagal mengirim: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg> Kirim Transaksi`;
  }
}

// ===== RESET FORM =====
function resetForm() {
  document.getElementById('txUserId').value = '';
  document.getElementById('txAmount').value = '';
  document.getElementById('txToken').value = '';
  document.getElementById('txMetadata').value = '';
  document.getElementById('txFeePreview').style.display = 'none';
  document.getElementById('txResponseCard').style.display = 'none';
  showToast('Form direset', 'info');
}

// ===== RBAC INITIALIZATION =====
function initRBAC() {
  const role = localStorage.getItem('gateway_role') || 'end_user';
  
  // 1. Hide/show sidebar elements based on data-roles attribute
  document.querySelectorAll('.nav-item').forEach(item => {
    const rolesAllowed = item.getAttribute('data-roles');
    if (rolesAllowed) {
      const allowedList = rolesAllowed.split(',').map(r => r.trim());
      if (!allowedList.includes(role)) {
        item.style.display = 'none';
      }
    }
  });

  // 2. Hide/show quick action buttons inside dashboard
  const btnQuickTransaksi = document.getElementById('btnQuickTransaksi');
  if (btnQuickTransaksi && role === 'operator') {
    btnQuickTransaksi.style.display = 'none';
  }
}

// ===== FEE PREVIEW (TRANSAKSI) =====
document.addEventListener('DOMContentLoaded', function() {
  const amountInput = document.getElementById('txAmount');
  if (amountInput) {
    amountInput.addEventListener('input', function() {
      const amount = parseFloat(this.value) || 0;
      if (amount > 0) {
        document.getElementById('txFeePreview').style.display = 'block';
        document.getElementById('txFeeValue').textContent = formatRupiah(amount * 0.005);
      } else {
        document.getElementById('txFeePreview').style.display = 'none';
      }
    });
  }

  // Cek server saat load
  cekServer();
  setInterval(cekServer, 15000);

  // Initialize RBAC (hiding sidebar menu items)
  initRBAC();

  // Display user name and role
  const userName = localStorage.getItem('gateway_user');
  const userRole = localStorage.getItem('gateway_role');
  if (userName) {
    const el = document.getElementById('userName');
    if (el) el.textContent = userName;
  }
  if (userRole) {
    const roleEl = document.querySelector('.user-role');
    if (roleEl) {
      let roleLabel = 'Konsumen';
      if (userRole === 'admin') roleLabel = '👑 Admin';
      else if (userRole === 'operator') roleLabel = '⚙️ Operator';
      else if (userRole === 'end_user') roleLabel = '👤 End User';
      roleEl.textContent = roleLabel;
    }
  }
});

// ===== KALKULATOR FEE =====
function hitungFeePreview() {
  const amount = parseFloat(document.getElementById('feeAmount').value) || 0;
  const fee = amount * 0.005;
  const net = amount - fee;

  document.getElementById('feeResult').textContent = formatRupiah(fee);
  document.getElementById('feeNet').textContent = formatRupiah(net);
}
