'use strict';
// 市场与政策 (2026-11 layout): every record is a <details> row, readable without JavaScript. This script shows
// 「全部展开」 (it reads 「全部收起」 while every record is open) and opens the record a country chip or the URL hash
// points to.
(() => {
  const records = [...document.querySelectorAll('.mp-record')];
  if (!records.length) return;
  const toggle = document.getElementById('mp-expand');
  const sync = () => {
    const allOpen = records.every(record => record.open);
    toggle.textContent = allOpen ? '全部收起' : '全部展开';
    toggle.setAttribute('aria-expanded', String(allOpen));
  };
  if (toggle) {
    toggle.hidden = false;
    toggle.addEventListener('click', () => {
      const open = !records.every(record => record.open);
      records.forEach(record => { record.open = open; });
      sync();
    });
    records.forEach(record => record.addEventListener('toggle', sync));
    sync();
  }
  const open = id => {
    const record = id ? document.getElementById(id) : null;
    if (record && records.includes(record)) record.open = true;
  };
  document.querySelectorAll('[data-record-link]').forEach(link => link.addEventListener('click', () => {
    open(link.dataset.recordLink);
  }));
  const fromHash = () => open(decodeURIComponent(window.location.hash.slice(1)));
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
