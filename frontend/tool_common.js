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
    backLink.innerHTML = '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg> Kembali ke Dashboard'
  } else {
    backLink.href = '/'
    backLink.innerHTML = '<svg viewBox="0 0 24 24"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg> Kembali ke Beranda'
  }
}

