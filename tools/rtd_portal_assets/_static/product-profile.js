'use strict';
// 产品档案 (step 13; tools/rtd_portal_assets/product_profile.html). Without JavaScript every market shows in turn
// and values are plain text. With it, the market switch shows one market (the hash ?market= is not used; the
// choice lives on the page), and clicking a value shows its source beside the parameters (a sheet on phones).
// The pure parts are on globalThis.ProductProfile for tests/product_profile_ui.test.mjs.
(() => {
  // The source card's lines from a value button's data attributes.
  const sourceLines = data => ({
    where: [data.market, data.language].filter(Boolean).join(' · ') + (data.date ? ` · 版本日期 ${data.date}` : ''),
    printed: data.printed || '',
    position: data.position || '',
  });
  globalThis.ProductProfile = {sourceLines};

  if (typeof document === 'undefined') return;
  const panels = [...document.querySelectorAll('[data-market-panel]')];
  const tabs = [...document.querySelectorAll('[data-market-tab]')];
  const card = document.querySelector('[data-pf-source]');
  document.documentElement.classList.add('pf-js');
  let open = null;

  const closeSource = () => {
    if (open) open.setAttribute('aria-expanded', 'false');
    open = null;
    if (card) card.hidden = true;
  };
  const showMarket = code => {
    panels.forEach(panel => { panel.hidden = panel.dataset.marketPanel !== code; });
    tabs.forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.marketTab === code)));
    document.querySelectorAll('[data-diff-market]').forEach(cell => {
      cell.classList.toggle('is-current', cell.dataset.diffMarket === code);
    });
    closeSource();
  };
  if (tabs.length) {
    tabs[0].closest('[data-pf-switch]').hidden = false;
    tabs.forEach(tab => tab.addEventListener('click', () => showMarket(tab.dataset.marketTab)));
    showMarket(tabs[0].dataset.marketTab);
  }

  document.addEventListener('click', event => {
    const button = event.target.closest('.pf-val');
    if (!button || !card) return;
    if (open === button) { closeSource(); return; }
    if (open) open.setAttribute('aria-expanded', 'false');
    open = button;
    button.setAttribute('aria-expanded', 'true');
    const lines = sourceLines(button.dataset);
    const label = button.closest('div').querySelector('dt');
    card.querySelector('[data-pf-source-title]').textContent = `${label ? label.textContent : ''} · 出处`;
    card.querySelector('[data-pf-source-value]').textContent = button.textContent;
    card.querySelector('[data-pf-source-where]').textContent = lines.where;
    card.querySelector('[data-pf-source-printed]').textContent = lines.printed;
    const link = card.querySelector('[data-pf-source-link]');
    link.hidden = !button.dataset.doc;
    if (button.dataset.doc) link.href = button.dataset.doc;
    card.hidden = false;
  });
  const close = document.querySelector('[data-pf-source-close]');
  if (close) close.addEventListener('click', closeSource);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeSource(); });
})();
