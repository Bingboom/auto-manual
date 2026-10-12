'use strict';
// 系统数据 page: filter the build-time rows by region and model and redraw every
// card. The rows come from the page's JSON block; without JavaScript the
// whole-repository counts and the publication table stay as rendered.
// The counting functions are pure and exposed as SystemDataModel for tests.
(() => {
  const SHARED = 'ALL';
  const READY = '成品';
  const CRITICAL = new Set(['缺失', '隔离']);

  const fits = (row, sel) => (sel.region === '' || row.region === sel.region) && (sel.model === '' || row.model === sel.model);
  // An asset whose model or region is ALL applies to every model or region.
  const assetFits = (row, sel) => (sel.region === '' || row.region === sel.region || row.region === SHARED)
    && (sel.model === '' || row.model === sel.model || row.model === SHARED);

  const countBy = (rows, key) => {
    const counts = new Map();
    for (const row of rows) counts.set(row[key], (counts.get(row[key]) || 0) + 1);
    return [...counts].map(([label, n]) => ({label, n}))
      .sort((a, b) => b.n - a.n || String(a.label).localeCompare(String(b.label)));
  };

  const summary = (data, sel) => {
    const published = data.published ? data.published.filter(row => fits(row, sel)) : null;
    const targets = data.targets.filter(row => fits(row, sel));
    const assets = data.assets.filter(row => assetFits(row, sel));
    const distinct = key => (published ? new Set(published.map(row => row[key])).size : null);
    return {
      manuals: published ? published.length : null,
      models: distinct('model'), languages: distinct('lang'), regions: distinct('region'),
      targets: targets.length,
      review_targets: targets.filter(row => row.review_pages > 0).length,
      assets: assets.length,
      ready_share: assets.length ? assets.filter(row => row.status === READY).length / assets.length : null,
    };
  };

  // Rows: models in the region (any model filter only highlights); columns: its languages.
  const matrix = (published, sel) => {
    const rows = published.filter(row => sel.region === '' || row.region === sel.region);
    const languages = countBy(rows, 'lang').map(item => item.label);
    const byModel = new Map();
    for (const row of rows) {
      const entry = byModel.get(row.model) || {model: row.model, manuals: 0, cells: new Map()};
      entry.manuals += 1;
      const cell = entry.cells.get(row.lang) || {manuals: 0, regions: new Set()};
      cell.manuals += 1;
      cell.regions.add(row.region);
      entry.cells.set(row.lang, cell);
      byModel.set(row.model, entry);
    }
    const models = [...byModel.values()].sort((a, b) => b.manuals - a.manuals || a.model.localeCompare(b.model));
    return {languages, models};
  };

  const coverage = (data, sel) => {
    const targets = data.targets.filter(row => fits(row, sel));
    return data.capabilities.map((name, index) => {
      const supported = targets.filter(row => row.caps[index] === 1).length;
      return {label: name, supported, targets: targets.length, share: targets.length ? supported / targets.length : 0};
    }).sort((a, b) => b.share - a.share);
  };

  const model = {fits, assetFits, countBy, summary, matrix, coverage};
  globalThis.SystemDataModel = model;

  const source = typeof document !== 'undefined' && document.getElementById('system-data-json');
  if (!source) return;
  let data;
  try {
    data = JSON.parse(source.textContent);
  } catch (error) {
    return;
  }

  const NS = 'http://www.w3.org/2000/svg';
  const $ = id => document.getElementById(id);
  const number = new Intl.NumberFormat('zh-CN');
  const percent = new Intl.NumberFormat('zh-CN', {style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1});
  const languageName = code => (data.language_labels[code] ? `${code} · ${data.language_labels[code]}` : code);
  const regionCodes = new Set(data.regions.map(item => item.code));
  const modelNames = new Set(data.models);

  const readSelection = () => {
    const params = new URLSearchParams(location.search);
    const region = params.get('region') || '';
    const picked = params.get('model') || '';
    return {region: regionCodes.has(region) ? region : '', model: modelNames.has(picked) ? picked : ''};
  };
  let sel = readSelection();

  const svg = (tag, attrs = {}, text) => {
    const node = document.createElementNS(NS, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const tip = (node, lines) => node.appendChild(svg('title', {}, lines.join('\n')));
  const note = (box, text) => {
    const p = document.createElement('p');
    p.className = 'sd-fallback';
    p.textContent = text;
    box.replaceChildren(p);
  };
  // Width of the widest label as drawn, so the bars start after it.
  const labelWidth = (root, labels, cls) => {
    const probe = svg('g');
    root.appendChild(probe);
    let width = 0;
    for (const label of labels) {
      const text = svg('text', cls ? {class: cls} : {}, label);
      probe.appendChild(text);
      width = Math.max(width, text.getComputedTextLength());
    }
    probe.remove();
    return Math.ceil(width);
  };
  const stage = (box, height) => {
    const root = svg('svg', {width: '100%', role: 'img'});
    const heading = box.closest('.sd-card') && box.closest('.sd-card').querySelector('h3');
    if (heading) root.setAttribute('aria-label', heading.textContent);
    box.replaceChildren(root);
    const width = Math.max(260, box.clientWidth);
    root.setAttribute('viewBox', `0 0 ${width} ${height}`);
    root.setAttribute('height', String(height));
    return {root, width};
  };

  const setSelection = next => {
    sel = {...sel, ...next};
    const params = new URLSearchParams(location.search);
    for (const key of ['region', 'model']) {
      if (sel[key]) params.set(key, sel[key]); else params.delete(key);
    }
    const query = params.toString();
    history.replaceState(null, '', `${location.pathname}${query ? `?${query}` : ''}${location.hash}`);
    render();
  };
  const toggleModel = name => {
    if (name && name !== SHARED) setSelection({model: sel.model === name ? '' : name});
  };

  // One horizontal bar per item; options: format, max, color(item), picked(item), onClick(item), title(item).
  const bars = (box, items, options) => {
    if (!items.length) {
      note(box, '当前筛选下没有数据。');
      return;
    }
    const rowHeight = 26, barHeight = 14;
    const {root, width} = stage(box, items.length * rowHeight);
    const labelW = labelWidth(root, items.map(item => item.label), 'sd-label') + 10;
    const valueW = labelWidth(root, items.map(item => options.format(item.value))) + 10;
    const max = options.max || Math.max(...items.map(item => item.value), 1);
    const span = Math.max(10, width - labelW - valueW);
    items.forEach((item, index) => {
      const length = Math.max(2, (item.value / max) * span);
      const picked = options.picked && options.picked(item);
      const clickable = options.onClick && item.label !== SHARED;
      const row = svg('g', {
        class: ['sd-row', picked ? 'is-picked' : '', options.dim && options.dim(item) ? 'is-dim' : '', clickable ? 'is-clickable' : ''].join(' ').trim(),
        transform: `translate(0,${index * rowHeight})`,
      });
      row.appendChild(svg('rect', {class: 'sd-row-bg', width, height: rowHeight, rx: 4}));
      row.appendChild(svg('text', {class: 'sd-label', x: labelW - 10, y: rowHeight / 2, dy: '0.35em', 'text-anchor': 'end'}, item.label));
      const bar = svg('rect', {class: 'sd-bar', x: labelW, y: (rowHeight - barHeight) / 2, width: length, height: barHeight, rx: 4});
      if (options.color) bar.style.fill = options.color(item);
      row.appendChild(bar);
      row.appendChild(svg('text', {class: 'sd-value', x: labelW + length + 6, y: rowHeight / 2, dy: '0.35em'}, options.format(item.value)));
      if (options.title) tip(row, options.title(item));
      if (clickable) row.addEventListener('click', () => options.onClick(item));
      root.appendChild(row);
    });
  };

  const drawMatrix = () => {
    const box = $('sd-matrix');
    if (!box || !data.published) return;
    const {languages, models} = matrix(data.published, sel);
    if (!models.length) {
      note(box, '当前筛选下没有数据。');
      return;
    }
    const rowHeight = 18, headHeight = 22;
    const {root, width} = stage(box, headHeight + models.length * rowHeight);
    const labelW = labelWidth(root, models.map(item => item.model), 'sd-label') + 12;
    const endW = labelWidth(root, models.map(item => number.format(item.manuals))) + 14;
    const cell = Math.max(14, Math.min(44, (width - labelW - endW) / Math.max(1, languages.length)));
    languages.forEach((code, index) => {
      const head = svg('text', {class: 'sd-axis', x: labelW + index * cell + cell / 2, y: headHeight - 8, 'text-anchor': 'middle'}, code);
      tip(head, [languageName(code)]);
      root.appendChild(head);
    });
    models.forEach((entry, index) => {
      const picked = sel.model === entry.model;
      const row = svg('g', {
        class: ['sd-row', 'is-clickable', picked ? 'is-picked' : '', sel.model && !picked ? 'is-dim' : ''].join(' ').trim(),
        transform: `translate(0,${headHeight + index * rowHeight})`,
      });
      row.appendChild(svg('rect', {class: 'sd-row-bg', width, height: rowHeight, rx: 3}));
      row.appendChild(svg('text', {class: 'sd-label', x: labelW - 12, y: rowHeight / 2, dy: '0.35em', 'text-anchor': 'end'}, entry.model));
      languages.forEach((code, column) => {
        const found = entry.cells.get(code);
        const rect = svg('rect', {
          class: found ? 'sd-cell is-on' : 'sd-cell', x: labelW + column * cell + 1.5, y: 2,
          width: cell - 3, height: rowHeight - 4, rx: 3,
        });
        tip(rect, found
          ? [`${entry.model} · ${languageName(code)}`, `区域：${[...found.regions].sort().join(' · ')}`, `说明书：${found.manuals} 份`]
          : [`${entry.model} · ${languageName(code)}`, '未发布']);
        row.appendChild(rect);
      });
      row.appendChild(svg('text', {class: 'sd-value', x: labelW + languages.length * cell + 8, y: rowHeight / 2, dy: '0.35em'}, number.format(entry.manuals)));
      row.addEventListener('click', () => toggleModel(entry.model));
      root.appendChild(row);
    });
  };

  const drawCapabilities = () => {
    const box = $('sd-caps');
    if (!box) return;
    const targets = data.targets.filter(row => fits(row, sel))
      .sort((a, b) => a.model.localeCompare(b.model) || a.region.localeCompare(b.region));
    if (!targets.length) {
      note(box, '当前筛选下没有数据。');
      return;
    }
    const names = data.capabilities;
    const probe = stage(box, 10);
    const headHeight = labelWidth(probe.root, [...names, '能力数', '评审页面']) + 12;
    const rowHeight = 17;
    const {root, width} = stage(box, headHeight + targets.length * rowHeight);
    const labelW = labelWidth(root, targets.map(row => row.key), 'sd-label') + 10;
    const cell = Math.max(12, Math.min(40, (width - labelW - 64) / names.length));
    const endX = labelW + names.length * cell;
    const heads = [...names.map((name, index) => [name, labelW + index * cell + cell / 2]), ['能力数', endX + 16], ['评审页面', endX + 44]];
    for (const [label, x] of heads) {
      root.appendChild(svg('text', {class: 'sd-axis', transform: `translate(${x + 4},${headHeight - 6}) rotate(-90)`}, label));
    }
    targets.forEach((target, index) => {
      const row = svg('g', {
        class: ['sd-row', 'is-clickable', sel.model === target.model ? 'is-picked' : ''].join(' ').trim(),
        transform: `translate(0,${headHeight + index * rowHeight})`,
      });
      row.appendChild(svg('rect', {class: 'sd-row-bg', width, height: rowHeight, rx: 3}));
      row.appendChild(svg('text', {class: 'sd-label', x: labelW - 10, y: rowHeight / 2, dy: '0.35em', 'text-anchor': 'end'}, target.key));
      names.forEach((name, column) => {
        row.appendChild(svg('rect', {
          class: target.caps[column] === 1 ? 'sd-cell is-on' : 'sd-cell', x: labelW + column * cell + 1.5, y: 2,
          width: cell - 3, height: rowHeight - 4, rx: 3,
        }));
      });
      const supported = target.caps.filter(value => value === 1).length;
      row.appendChild(svg('text', {class: 'sd-value', x: endX + 16, y: rowHeight / 2, dy: '0.35em', 'text-anchor': 'middle'}, String(supported)));
      if (target.review_pages > 0) row.appendChild(svg('circle', {class: 'sd-review', cx: endX + 44, cy: rowHeight / 2, r: 4}));
      tip(row, [
        target.key, `项目号：${target.project}`, `能力：${supported} / ${names.length}`,
        `语言：${target.langs.length ? target.langs.map(languageName).join('、') : '未登记'}`,
        `评审页面：${target.review_pages || '无'}`,
      ]);
      row.addEventListener('click', () => toggleModel(target.model));
      root.appendChild(row);
    });
  };

  const drawBars = () => {
    if (data.published) {
      const published = data.published.filter(row => fits(row, sel));
      const langs = countBy(published, 'lang').map(item => ({...item, value: item.n}));
      const box = $('sd-langs');
      if (box) bars(box, langs, {format: n => number.format(n), title: item => [languageName(item.label), `${item.value} 份`]});
      const regions = countBy(data.published.filter(row => sel.model === '' || row.model === sel.model), 'region')
        .map(item => ({...item, value: item.n}));
      const regionBox = $('sd-regions');
      if (regionBox) {
        bars(regionBox, regions, {
          format: n => number.format(n),
          picked: item => item.label === sel.region,
          dim: item => sel.region !== '' && item.label !== sel.region,
          onClick: item => setSelection({region: sel.region === item.label ? '' : item.label}),
          title: item => [item.label, `${item.value} 份`],
        });
      }
    }
    const coverageBox = $('sd-coverage');
    if (coverageBox) {
      bars(coverageBox, coverage(data, sel).filter(item => item.targets).map(item => ({...item, value: item.share})), {
        format: share => percent.format(share), max: 1,
        title: item => [item.label, `${item.supported} / ${item.targets} 个目标支持`],
      });
    }
    const assets = data.assets.filter(row => assetFits(row, sel));
    const statusBox = $('sd-status');
    if (statusBox) {
      bars(statusBox, countBy(assets, 'status').map(item => ({...item, value: item.n})), {
        format: n => number.format(n),
        color: item => (CRITICAL.has(item.label) ? 'var(--sd-critical)' : item.label === READY ? '' : 'var(--sd-muted)'),
        title: item => [item.label, `${item.value} 条`],
      });
    }
    const categoryBox = $('sd-category');
    if (categoryBox) {
      bars(categoryBox, countBy(assets, 'category').map(item => ({...item, value: item.n})), {
        format: n => number.format(n), title: item => [item.label, `${item.value} 条`],
      });
    }
    const modelBox = $('sd-asset-models');
    if (modelBox) {
      const all = countBy(data.assets.filter(row => assetFits(row, {region: sel.region, model: ''})), 'model')
        .map(item => ({...item, value: item.n}));
      const shown = all.slice(0, 12);
      const extra = all.find(item => item.label === sel.model);
      if (extra && !shown.includes(extra)) shown.push(extra);
      bars(modelBox, shown, {
        format: n => number.format(n),
        color: item => (item.label === SHARED ? 'var(--sd-muted)' : ''),
        picked: item => item.label === sel.model,
        dim: item => sel.model !== '' && item.label !== sel.model && item.label !== SHARED,
        onClick: item => toggleModel(item.label),
        title: item => [item.label, `${item.value} 条`],
      });
    }
  };

  const fillCounts = () => {
    const counts = summary(data, sel);
    document.querySelectorAll('[data-kpi]').forEach(node => {
      const value = counts[node.dataset.kpi];
      node.textContent = value === null || value === undefined ? '—'
        : node.dataset.kpi === 'ready_share' ? percent.format(value) : number.format(value);
    });
    const scope = $('sd-scope');
    const parts = [sel.region, sel.model].filter(Boolean);
    scope.hidden = !parts.length;
    scope.textContent = parts.length ? `当前筛选：${parts.join(' · ')}` : '';
  };

  // Publication table: rows are server-rendered; filter, search and sort them in place.
  const table = $('sd-table');
  const search = $('sd-search');
  const sortState = {column: 4, direction: -1};
  const rows = table ? [...table.tBodies[0].rows] : [];
  const cellText = (row, column) => row.cells[column].textContent.trim();
  const filterTable = () => {
    if (!table) return;
    const query = (search.value || '').trim().toLowerCase();
    let shown = 0;
    for (const row of rows) {
      const visible = fits(row.dataset, sel) && (!query || row.textContent.toLowerCase().includes(query));
      row.hidden = !visible;
      if (visible) shown += 1;
    }
    $('sd-count').textContent = shown === rows.length ? `${rows.length} 份` : `${shown} / ${rows.length} 份`;
  };
  const sortTable = () => {
    const {column, direction} = sortState;
    rows.sort((a, b) => direction * cellText(a, column).localeCompare(cellText(b, column)));
    table.tBodies[0].append(...rows);
    table.querySelectorAll('[data-sort]').forEach(button => {
      const on = Number(button.dataset.sort) === column;
      if (on) button.setAttribute('aria-sort', direction > 0 ? 'ascending' : 'descending');
      else button.removeAttribute('aria-sort');
    });
  };
  if (table) {
    search.hidden = false;
    search.addEventListener('input', filterTable);
    table.querySelectorAll('[data-sort]').forEach(button => button.addEventListener('click', () => {
      const column = Number(button.dataset.sort);
      sortState.direction = sortState.column === column ? -sortState.direction : 1;
      sortState.column = column;
      sortTable();
    }));
    table.tBodies[0].addEventListener('click', event => {
      if (event.target.closest('a')) return;
      const row = event.target.closest('tr[data-model]');
      if (row) toggleModel(row.dataset.model);
    });
  }

  const regionSelect = $('sd-region'), modelSelect = $('sd-model'), reset = $('sd-reset');
  regionSelect.addEventListener('change', () => setSelection({region: regionSelect.value}));
  modelSelect.addEventListener('change', () => setSelection({model: modelSelect.value}));
  reset.addEventListener('click', () => setSelection({region: '', model: ''}));
  $('sd-filters').hidden = false;

  function render() {
    regionSelect.value = sel.region;
    modelSelect.value = sel.model;
    regionSelect.classList.toggle('is-set', sel.region !== '');
    modelSelect.classList.toggle('is-set', sel.model !== '');
    reset.hidden = !sel.region && !sel.model;
    fillCounts();
    drawMatrix();
    drawCapabilities();
    drawBars();
    filterTable();
  }

  render();
  let pending = 0;
  let lastWidth = document.documentElement.clientWidth;
  window.addEventListener('resize', () => {
    if (document.documentElement.clientWidth === lastWidth) return;
    lastWidth = document.documentElement.clientWidth;
    cancelAnimationFrame(pending);
    pending = requestAnimationFrame(render);
  });
})();
