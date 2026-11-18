'use strict';
// 产品档案 (step 13; tools/rtd_portal_assets/product_profile.html). Without JavaScript every market shows in turn
// and values are plain text. With it, the market switch shows one market, and clicking a value shows its sources
// beside the parameters (a sheet on phones): the page renders each value's source list, escaped, in a hidden block,
// and this script copies those nodes into the card; nothing is built from strings. The pure part is on
// globalThis.ProductProfile for tests/product_profile_ui.test.mjs.
(() => {
  const sourceTitle = label => `${label || '数值'} · 参数原文溯源`;
  // The head's SKU 创建时间 is the chosen market's own: show that market's date, hide the others. Without JavaScript
  // the head lists every market's date with its market; the labels go once the switch runs.
  const showDates = (dates, code) => dates.forEach(date => { date.hidden = date.dataset.marketDate !== code; });
  globalThis.ProductProfile = {sourceTitle, showDates};

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
    showDates([...document.querySelectorAll('[data-market-date]')], code);
    tabs.forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.marketTab === code)));
    document.querySelectorAll('[data-diff-market]').forEach(cell => {
      cell.classList.toggle('is-current', cell.dataset.diffMarket === code);
    });
    closeSource();
  };
  if (tabs.length) {
    tabs[0].closest('[data-pf-switch]').hidden = false;
    document.querySelectorAll('[data-market-date-label]').forEach(label => { label.hidden = true; });
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
    card.querySelector('[data-pf-source-title]').textContent = sourceTitle(button.dataset.label);
    card.querySelector('[data-pf-source-value]').textContent = button.textContent;
    const list = document.getElementById(button.dataset.sources);
    const target = card.querySelector('[data-pf-source-list]');
    target.replaceChildren(...(list ? [...list.children].map(node => node.cloneNode(true)) : []));
    card.hidden = false;
  });
  const close = document.querySelector('[data-pf-source-close]');
  if (close) close.addEventListener('click', closeSource);
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeSource(); });
})();
