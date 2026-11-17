'use strict';
// 产品对比 (step 13; tools/rtd_portal_assets/product_compare.html). Reads every product's values from the page's
// JSON block (#pc-data), lets the visitor pick two to four products and a market, and draws the comparison: a group
// row per parameter group, a row per parameter, rows that differ highlighted, 只看不同的参数 keeping only those. The
// choice is kept in the URL (?p=A,B&market=US). Everything is written with textContent. The pure parts are on
// globalThis.ProductCompare for tests/product_compare_ui.test.mjs.
(() => {
  const LIMIT = 4;
  const parseState = (search, data) => {
    const params = new URLSearchParams(search);
    const known = new Set(data.products.map(product => product.model));
    const picked = [...new Set((params.get('p') || '').split(',').map(code => code.trim()).filter(code => known.has(code)))];
    return {picked: picked.slice(0, LIMIT), market: params.get('market') || '', diffOnly: params.get('diff') === '1'};
  };
  const stateQuery = state => {
    const params = new URLSearchParams();
    if (state.picked.length) params.set('p', state.picked.join(','));
    if (state.market) params.set('market', state.market);
    if (state.diffOnly) params.set('diff', '1');
    const query = params.toString();
    return query ? `?${query}` : '';
  };
  // The model a typed text names: an exact model code, else the single product whose code or name contains it.
  const resolvePick = (text, data) => {
    const wanted = text.trim().toLowerCase();
    if (!wanted) return '';
    const exact = data.products.find(product => product.model.toLowerCase() === wanted);
    if (exact) return exact.model;
    const hits = data.products.filter(product => `${product.model} ${product.name}`.toLowerCase().includes(wanted));
    return hits.length === 1 ? hits[0].model : '';
  };
  // Groups of rows for the picked products in one market: a row differs when at least two products sold in that
  // market state a value and those values (comparison keys) are not all the same; a missing value shows 暂无 and
  // takes no part; a product not sold there is shown as such; rows nobody states are left out.
  const comparison = (data, state) => {
    const products = state.picked.map(code => data.products.find(product => product.model === code)).filter(Boolean);
    const sold = products.map(product => product.markets.includes(state.market));
    const groups = [];
    data.groups.forEach(group => {
      const rows = [];
      group.parameters.forEach(([key, name]) => {
        const cells = products.map(product => {
          const value = ((product.values || {})[state.market] || {})[key];
          return value ? {text: value[0], key: value[1], conflict: Boolean(value[2])} : {text: '', key: '', conflict: false};
        });
        if (cells.every(cell => !cell.text)) return;
        // As on 产品档案: only products sold in the market with a value take part; a missing value is no value.
        const stated = cells.filter((cell, index) => sold[index] && cell.text);
        const differs = stated.length >= 2 && new Set(stated.map(cell => cell.key)).size > 1;
        if (state.diffOnly && !differs) return;
        rows.push({name, cells, differs});
      });
      if (rows.length) groups.push({title: group.title, rows});
    });
    return {products, sold, groups};
  };
  // A market every picked product is sold in, keeping the current one when it qualifies; '' when there is none.
  const sharedMarket = (data, picked, current, markets) => {
    const products = picked.map(code => data.products.find(product => product.model === code)).filter(Boolean);
    const shared = markets.filter(code => products.every(product => product.markets.includes(code)));
    return shared.includes(current) ? current : (shared[0] || '');
  };
  // The 产品档案 path segment of a model: page names are the model code itself (letters, digits, ".", "-", "_"
  // only), which encodeURIComponent leaves unchanged, so both always agree.
  const itemPath = model => encodeURIComponent(model);
  globalThis.ProductCompare = {LIMIT, parseState, stateQuery, resolvePick, comparison, sharedMarket, itemPath};

  if (typeof document === 'undefined') return;
  const app = document.querySelector('[data-pc]');
  const source = document.getElementById('pc-data');
  if (!app || !source) return;
  const data = JSON.parse(source.textContent);
  const itemHref = model => app.dataset.itemBase.replace('__MODEL__', itemPath(model));
  const picked = app.querySelector('[data-pc-picked]');
  const input = app.querySelector('[data-pc-input]');
  const market = app.querySelector('[data-pc-market]');
  const diff = app.querySelector('[data-pc-diff]');
  const empty = app.querySelector('[data-pc-empty]');
  const wrap = app.querySelector('[data-pc-wrap]');
  const table = app.querySelector('[data-pc-table]');
  const state = parseState(window.location.search, data);
  const markets = [...market.options].map(option => option.value);
  if (!markets.includes(state.market)) {
    const first = state.picked.length && data.products.find(product => product.model === state.picked[0]);
    state.market = (first && first.markets.find(code => markets.includes(code))) || markets[0] || '';
  }
  market.value = state.market;
  diff.checked = state.diffOnly;
  app.hidden = false;

  const el = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const save = () => {
    try { history.replaceState(null, '', window.location.pathname + stateQuery(state)); } catch (error) { /* file:// */ }
  };
  const draw = () => {
    picked.replaceChildren(...state.picked.map(code => {
      const product = data.products.find(item => item.model === code);
      const chip = el('span', null, 'pc-chip');
      chip.append(el('span', product ? product.name : code));
      const remove = el('button', '×');
      remove.type = 'button';
      remove.setAttribute('aria-label', `移除 ${product ? product.name : code}`);
      remove.addEventListener('click', () => { state.picked = state.picked.filter(item => item !== code); repick(); });
      chip.append(remove);
      return chip;
    }));
    input.disabled = state.picked.length >= LIMIT;
    const view = comparison(data, state);
    const ready = view.products.length >= 2;
    empty.hidden = ready;
    wrap.hidden = !ready;
    table.replaceChildren();
    if (!ready) return;
    const head = el('thead');
    const top = el('tr');
    top.append(el('th', '参数'));
    view.products.forEach((product, index) => {
      const th = el('th');
      th.scope = 'col';
      const link = el('a', product.name);
      link.href = itemHref(product.model);
      th.append(link, el('small', [product.model, product.project].filter(Boolean).join(' · ')));
      if (!view.sold[index]) th.append(el('small', `无${data.labels[state.market] || state.market}版本`, 'pc-absent'));
      top.append(th);
    });
    head.append(top);
    const body = el('tbody');
    view.groups.forEach(group => {
      const row = el('tr', null, 'pt-group');
      const th = el('th', group.title);
      th.colSpan = view.products.length + 1;
      row.append(th);
      body.append(row);
      group.rows.forEach(item => {
        const tr = el('tr', null, item.differs ? 'is-diff' : '');
        const label = el('th', item.name);
        label.scope = 'row';
        tr.append(label);
        item.cells.forEach(cell => {
          const td = el('td');
          if (cell.text) {
            td.append(document.createTextNode(cell.text));
            if (cell.conflict) td.append(el('span', '各说明书写法不一致', 'pt-badge'));
          } else {
            td.append(el('span', '暂无', 'pt-none'));
          }
          tr.append(td);
        });
        body.append(tr);
      });
    });
    table.append(head, body);
  };
  const update = () => { save(); draw(); };
  const repick = () => {
    const next = sharedMarket(data, state.picked, state.market, markets);
    if (next) { state.market = next; market.value = next; }
    update();
  };
  const add = () => {
    const code = resolvePick(input.value, data);
    if (code && !state.picked.includes(code) && state.picked.length < LIMIT) state.picked.push(code);
    input.value = '';
    repick();
  };
  app.querySelector('[data-pc-add]').addEventListener('click', add);
  input.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); add(); } });
  input.addEventListener('change', () => { if (resolvePick(input.value, data)) add(); });
  market.addEventListener('change', () => { state.market = market.value; update(); });
  diff.addEventListener('change', () => { state.diffOnly = diff.checked; update(); });
  draw();
})();
