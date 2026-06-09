(function() {
  // Check auth
  if (localStorage.getItem('gateway_logged_in') !== 'true') {
    window.location.href = '/login';
    return;
  }

  // Check role authorization
  const role = localStorage.getItem('gateway_role') || 'end_user';
  const path = window.location.pathname;

  const guards = {
    '/pricing/manage': ['admin'],
    '/integrator/fee/manage': ['admin', 'operator'],
    '/integrator/logging/manage': ['admin', 'operator'],
    '/monitor/health-check/manage': ['admin', 'operator'],
    '/monitor': ['admin', 'operator'],
    '/integrator/backtracking/manage': ['admin', 'operator'],
    '/integrator/pembukuan': ['admin', 'operator']
  };

  for (const [guardedPath, allowedRoles] of Object.entries(guards)) {
    if (path === guardedPath || path.startsWith(guardedPath + '/')) {
      if (!allowedRoles.includes(role)) {
        alert('Akses Ditolak: Role "' + role + '" tidak memiliki izin untuk mengakses halaman ini.');
        window.location.href = '/dashboard';
        break;
      }
    }
  }
})();

function configureBackLink(linkId) {
  const backLink = document.getElementById(linkId)
  if (!backLink) return

  const ref = document.referrer || ''
  const fromDashboard = ref.includes('/dashboard')

  if (fromDashboard) {
    backLink.href = '/dashboard'
    backLink.textContent = '📊 Kembali ke Dashboard'
  } else {
    backLink.href = '/'
    backLink.textContent = '🏠 Kembali ke Beranda'
  }
}

