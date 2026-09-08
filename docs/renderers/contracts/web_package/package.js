/* Probe only when HTTP can establish absence. Local/offline download stays usable. */
document.addEventListener('DOMContentLoaded', () => {
  const link = document.querySelector('.manual-package-pdf');
  if (!link || !['http:', 'https:'].includes(location.protocol)) return;
  fetch(link.href, {method: 'HEAD'}).then(response => {
    if (![404, 410].includes(response.status)) return;
    link.setAttribute('aria-disabled', 'true');
    link.removeAttribute('href');
    link.textContent = link.dataset.unavailable;
  }).catch(() => { /* A failed probe does not establish a missing PDF. */ });
});
