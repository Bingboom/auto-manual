'use strict';
// 产品矩阵 page: dim what a market has no Web manual for, and sort the spec
// table by any column. Everything is rendered at build time; without
// JavaScript every product shows and the filter stays hidden.
// The pure rules are exposed as ProductMatrixModel for tests.
(() => {
  // An element is out when a market is chosen and it has no Web manual there.
  const isOut = (regions, market) => market !== '' && !String(regions || '').split(' ').filter(Boolean).includes(market);

  // Numeric columns open largest first, text columns A→Z; a second click reverses.
  const nextSort = (state, col, numeric) => ({col, dir: state.col === col ? -state.dir : (numeric ? -1 : 1)});

  const compare = (x, y, numeric, dir) => dir * (numeric ? Number(x) - Number(y) : String(x).localeCompare(String(y)));

  globalThis.ProductMatrixModel = {isOut, nextSort, compare};

  if (typeof document === 'undefined') return;

  const filter = document.getElementById('pm-filter');
  if (filter) {
    const buttons = [...filter.querySelectorAll('button[data-market]')];
    const items = [...document.querySelectorAll('main [data-regions]')];
    buttons.forEach(button => button.addEventListener('click', () => {
      const market = button.dataset.market;
      buttons.forEach(other => other.setAttribute('aria-pressed', String(other === button)));
      items.forEach(item => item.classList.toggle('is-out', isOut(item.dataset.regions, market)));
    }));
    filter.hidden = false;
  }

  const table = document.getElementById('pm-specs');
  if (!table) return;
  const body = table.tBodies[0];
  const headers = [...table.tHead.rows[0].cells];
  let state = {col: 2, dir: 1};
  table.tHead.querySelectorAll('button[data-col]').forEach(button => button.addEventListener('click', () => {
    const col = Number(button.dataset.col);
    const numeric = button.dataset.num === '1';
    state = nextSort(state, col, numeric);
    const rows = [...body.rows].sort((a, b) => compare(a.cells[col].dataset.v, b.cells[col].dataset.v, numeric, state.dir));
    body.append(...rows);
    headers.forEach((th, index) => {
      if (index === col) th.setAttribute('aria-sort', state.dir > 0 ? 'ascending' : 'descending');
      else th.removeAttribute('aria-sort');
    });
  }));
})();
