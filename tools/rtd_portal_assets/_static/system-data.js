'use strict';
// 说明书工作台「数据统计」 (production_statistics.html, 2026-11 design): the five cards are counted at build time, so
// this script only searches and sorts the full table of published Web manuals. Rows are server-rendered; without
// JavaScript the table shows in build order (newest first) and the search box stays hidden.
var SystemDataTable = (() => {
  // A row matches when every word of the query is in its text.
  const matches = (text, query) => String(query || '').trim().toLowerCase().split(/\s+/).filter(Boolean)
    .every(word => text.toLowerCase().includes(word));
  // Rows sorted by one column's text; direction 1 ascends, -1 descends; ties keep their order.
  const sorted = (rows, column, direction, cellText) => rows
    .map((row, index) => ({row, index}))
    .sort((a, b) => direction * cellText(a.row, column).localeCompare(cellText(b.row, column)) || a.index - b.index)
    .map(item => item.row);
  return {matches, sorted};
})();

(() => {
  if (typeof document === 'undefined') return;
  const table = document.getElementById('sd-table');
  const search = document.getElementById('sd-search');
  const count = document.getElementById('sd-count');
  if (!table || !search || !count) return;
  const rows = [...table.tBodies[0].rows];
  const cellText = (row, column) => row.cells[column].textContent.trim();
  const state = {column: 4, direction: -1};
  const filter = () => {
    let shown = 0;
    for (const row of rows) {
      row.hidden = !SystemDataTable.matches(row.textContent, search.value);
      if (!row.hidden) shown += 1;
    }
    // One row per published route: a legacy alias is a row, not another 语言版本, so the count reads 条.
    count.textContent = shown === rows.length ? `${rows.length} 条` : `${shown} / ${rows.length} 条`;
  };
  const sort = () => {
    table.tBodies[0].append(...SystemDataTable.sorted(rows, state.column, state.direction, cellText));
    table.querySelectorAll('[data-sort]').forEach(button => {
      if (Number(button.dataset.sort) === state.column) button.setAttribute('aria-sort', state.direction > 0 ? 'ascending' : 'descending');
      else button.removeAttribute('aria-sort');
    });
  };
  search.hidden = false;
  search.addEventListener('input', filter);
  table.querySelectorAll('[data-sort]').forEach(button => button.addEventListener('click', () => {
    const column = Number(button.dataset.sort);
    state.direction = state.column === column ? -state.direction : 1;
    state.column = column;
    sort();
  }));
})();
