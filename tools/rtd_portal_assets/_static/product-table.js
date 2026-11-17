'use strict';
// 参数表 (step 13; tools/rtd_portal_assets/product_table.html). Without JavaScript every category's table shows in
// full. With it: one category at a time, 项目 / 市场 / 系列 filters, 按项目分组, sorting by a column (numbers as
// numbers, empty cells last) and 下载表格 (the visible rows of the open table as CSV with a BOM, so spreadsheet
// programs read the Chinese text). The pure parts are on globalThis.ProductTable for tests/product_table_ui.test.mjs.
(() => {
  const rowMatches = (row, filter) =>
    (!filter.project || (filter.project === '-' ? row.project === '' : row.project === filter.project))
    && (!filter.market || row.market === filter.market)
    && (!filter.series || row.series === filter.series);
  // Compare two sort values; empty last whatever the direction.
  const compareValues = (a, b, numeric, direction) => {
    if (a === '' || b === '') return a === b ? 0 : (a === '' ? 1 : -1);
    const order = numeric ? Number(a) - Number(b) : String(a).localeCompare(String(b), 'zh-CN');
    return direction === 'descending' ? -order : order;
  };
  const csvCell = text => (/[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text);
  const csvText = rows => '﻿' + rows.map(cells => cells.map(csvCell).join(',')).join('\r\n') + '\r\n';
  globalThis.ProductTable = {rowMatches, compareValues, csvText};

  if (typeof document === 'undefined') return;
  const panels = [...document.querySelectorAll('[data-pt-panel]')];
  if (!panels.length) return;
  const cats = [...document.querySelectorAll('[data-pt-cat]')];
  const download = document.querySelector('[data-pt-download]');
  document.documentElement.classList.add('pt-js');
  let current = panels[0];

  const cellText = cell => {
    if (cell.querySelector('.pt-none')) return '';
    const link = cell.querySelector('a');
    const first = link || cell.firstChild;
    return first ? first.textContent.trim() : '';
  };
  const setup = panel => {
    const table = panel.querySelector('[data-pt-table]');
    const body = table.tBodies[0];
    const rows = [...body.rows].filter(row => !row.classList.contains('pt-group'));
    const selects = [...panel.querySelectorAll('[data-pt-filter]')];
    const group = panel.querySelector('[data-pt-group]');
    const headers = [...table.tHead.rows[0].cells];
    let sorted = null;
    panel.querySelector('[data-pt-filters]').hidden = false;

    const render = () => {
      const filter = Object.fromEntries(selects.map(select => [select.dataset.ptFilter, select.value]));
      let ordered = rows.slice();
      if (sorted) {
        const numeric = headers[sorted.index].dataset.ptCol === 'number';
        ordered.sort((a, b) => compareValues(a.cells[sorted.index].dataset.sort ?? '',
                                             b.cells[sorted.index].dataset.sort ?? '', numeric, sorted.direction));
      }
      if (group && group.checked) {
        // Projects keep their order; rows without one come last; sorting applies inside each project.
        const projects = [...new Set(rows.map(row => row.dataset.project))].sort((a, b) => (a === '') - (b === '') || a.localeCompare(b));
        ordered = projects.flatMap(project => ordered.filter(row => row.dataset.project === project));
      }
      body.querySelectorAll('.pt-group').forEach(row => row.remove());
      let last = null;
      ordered.forEach(row => {
        const visible = rowMatches(row.dataset, filter);
        row.hidden = !visible;
        if (visible && group && group.checked && row.dataset.project !== last) {
          const head = document.createElement('tr');
          head.className = 'pt-group';
          const th = document.createElement('th');
          th.colSpan = headers.length;
          th.textContent = row.dataset.project || '未归入项目';
          head.appendChild(th);
          body.appendChild(head);
          last = row.dataset.project;
        }
        body.appendChild(row);
      });
    };
    selects.forEach(select => select.addEventListener('change', render));
    if (group) group.addEventListener('change', render);
    headers.forEach((header, index) => {
      const button = header.querySelector('[data-pt-sort]');
      if (!button) return;
      button.addEventListener('click', () => {
        const direction = sorted && sorted.index === index && sorted.direction === 'ascending' ? 'descending' : 'ascending';
        sorted = {index, direction};
        headers.forEach(cell => cell.removeAttribute('aria-sort'));
        header.setAttribute('aria-sort', direction);
        render();
      });
    });
    panel.ptRows = () => {
      const head = headers.map(cell => cell.dataset.ptHead || cell.textContent.trim());
      const visible = [...body.rows].filter(row => !row.hidden && !row.classList.contains('pt-group'));
      return [head, ...visible.map(row => [...row.cells].map(cellText))];
    };
    render();
  };
  panels.forEach(setup);

  const show = id => {
    panels.forEach(panel => { panel.hidden = panel.dataset.ptPanel !== id; });
    cats.forEach(cat => cat.setAttribute('aria-pressed', String(cat.dataset.ptCat === id)));
    current = panels.find(panel => panel.dataset.ptPanel === id) || panels[0];
  };
  if (cats.length) {
    cats[0].parentElement.hidden = false;
    cats.forEach(cat => cat.addEventListener('click', () => show(cat.dataset.ptCat)));
    show(cats[0].dataset.ptCat);
  }
  if (download) {
    download.hidden = false;
    download.addEventListener('click', () => {
      const blob = new Blob([csvText(current.ptRows())], {type: 'text/csv;charset=utf-8'});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `参数表-${current.querySelector('[data-pt-table]').dataset.ptName}.csv`;
      document.body.appendChild(link);
      link.click();
      setTimeout(() => { link.remove(); URL.revokeObjectURL(link.href); }, 1000);
    });
  }
})();
