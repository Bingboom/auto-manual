import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 说明书工作台「数据统计」 (tools/rtd_portal_assets/_static/system-data.js): the cards are counted at build time,
// so the script only searches and sorts the full table of published Web manuals.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/system-data.js', import.meta.url), 'utf8');

function load(context = {}) {
  vm.runInNewContext(script, context);
  return context;
}

test('every word of a query must be in a row', () => {
  const {SystemDataTable} = load();
  assert.equal(SystemDataTable.matches('JE-1000F EU en 2026-11-02', 'je-1000f en'), true);
  assert.equal(SystemDataTable.matches('JE-1000F EU en 2026-11-02', 'je-1000f ja'), false);
  assert.equal(SystemDataTable.matches('anything', '  '), true);
});

test('sorting follows one column and keeps ties in order', () => {
  const {SystemDataTable} = load();
  const rows = [['B', '2'], ['A', '1'], ['B', '1']];
  const text = (row, column) => row[column];
  assert.deepEqual(JSON.parse(JSON.stringify(SystemDataTable.sorted(rows, 0, 1, text))), [['A', '1'], ['B', '2'], ['B', '1']]);
  assert.deepEqual(JSON.parse(JSON.stringify(SystemDataTable.sorted(rows, 1, -1, text))), [['B', '2'], ['A', '1'], ['B', '1']]);
});

function page() {
  const listeners = {};
  const node = (props = {}) => ({hidden: false, attributes: {}, dataset: {},
    setAttribute(name, value) { this.attributes[name] = String(value); },
    removeAttribute(name) { delete this.attributes[name]; },
    addEventListener(name, callback) { (listeners[name] ||= []).push(callback); }, ...props});
  const row = (model, region, date) => {
    const cells = [model, region, 'en-US', '1.0', date].map(textContent => ({textContent}));
    return node({cells, textContent: cells.map(cell => cell.textContent).join(' ')});
  };
  const rows = [row('JE-1000F', 'EU', '2026-11-01'), row('JE-2000F', 'US', '2026-11-04'), row('JA-TS02A', 'US', '2026-10-30')];
  const order = [];
  const body = {rows, append: (...items) => { order.splice(0, order.length, ...items); }};
  const buttons = [0, 4].map(column => node({dataset: {sort: String(column)}}));
  const table = node({tBodies: [body], querySelectorAll: () => buttons});
  const search = node({hidden: true, value: ''});
  const count = node({textContent: ''});
  const document = {getElementById: id => ({'sd-table': table, 'sd-search': search, 'sd-count': count}[id] || null)};
  load({document});
  return {rows, order, buttons, search, count, listeners};
}

test('the search box appears with JavaScript and narrows the table', () => {
  const view = page();
  assert.equal(view.search.hidden, false);
  view.search.value = 'je-2 11-04';
  view.listeners.input.forEach(callback => callback());
  assert.deepEqual(view.rows.map(row => row.hidden), [true, false, true]);
  assert.equal(view.count.textContent, '1 / 3 条');
  view.search.value = '';
  view.listeners.input.forEach(callback => callback());
  assert.equal(view.count.textContent, '3 条');
});

test('a header click sorts by its column, a second click reverses it', () => {
  const view = page();
  const [model] = view.buttons;
  view.listeners.click[0]();
  assert.deepEqual(view.order.map(row => row.cells[0].textContent), ['JA-TS02A', 'JE-1000F', 'JE-2000F']);
  assert.equal(model.attributes['aria-sort'], 'ascending');
  view.listeners.click[0]();
  assert.deepEqual(view.order.map(row => row.cells[0].textContent), ['JE-2000F', 'JE-1000F', 'JA-TS02A']);
  assert.equal(model.attributes['aria-sort'], 'descending');
});
