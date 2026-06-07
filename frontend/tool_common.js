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
