import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 参数表 (product-table.js) and 产品对比 (product-compare.js): their pure parts, loaded without a DOM. Invented data.
const load = name => {
  const sandbox = {URLSearchParams};
  sandbox.globalThis = sandbox;
  vm.runInNewContext(readFileSync(new URL(`../tools/rtd_portal_assets/_static/${name}`, import.meta.url), 'utf8'), sandbox);
  return sandbox;
};
const plain = value => JSON.parse(JSON.stringify(value));
const {rowMatches, compareValues, csvText} = load('product-table.js').ProductTable;
const {LIMIT, parseState, stateQuery, resolvePick, comparison, sharedMarket} = load('product-compare.js').ProductCompare;

test('参数表 rows match every set filter, 未归入项目 included', () => {
  const row = {project: 'P-FAKE-1', market: 'US', series: '标准'};
  assert.equal(rowMatches(row, {project: '', market: '', series: ''}), true);
  assert.equal(rowMatches(row, {project: 'P-FAKE-1', market: 'US', series: '标准'}), true);
  assert.equal(rowMatches(row, {project: 'P-FAKE-1', market: 'JP', series: ''}), false);
  assert.equal(rowMatches({...row, project: ''}, {project: '-', market: '', series: ''}), true);
});

test('参数表 sorts numbers as numbers and keeps empty cells last', () => {
  const values = ['', '100', '20', '3'];
  assert.deepEqual([...values].sort((a, b) => compareValues(a, b, true, 'ascending')), ['3', '20', '100', '']);
  assert.deepEqual([...values].sort((a, b) => compareValues(a, b, true, 'descending')), ['100', '20', '3', '']);
});

test('the CSV starts with a BOM and quotes what needs quoting', () => {
  const text = csvText([['产品', '说明'], ['A', 'x, "y"\nz']]);
  assert.equal(text.charCodeAt(0), 0xfeff);
  assert.equal(text.slice(1), '产品,说明\r\nA,"x, ""y""\nz"\r\n');
});

const DATA = {
  products: [
    {model: 'FAKE-1', name: 'Fake One', project: 'P-FAKE-1', markets: ['US', 'JP'],
     values: {US: {cap: ['1,000 Wh', '#1000', false], cell: ['LFP', 'lfp', true]}, JP: {cap: ['1,000 Wh', '#1000', false]}}},
    {model: 'FAKE-2', name: 'Fake Two', project: 'P-FAKE-1', markets: ['US'],
     values: {US: {cap: ['2,000 Wh', '#2000', false], cell: ['LFP', 'lfp', false]}}},
    {model: 'FAKE-3', name: 'Other Three', project: '', markets: ['JP'], values: {JP: {cap: ['1,000 Wh', '#1000', false]}}},
  ],
  groups: [{title: '电池', parameters: [['cap', '标称容量'], ['cell', '电芯类型'], ['none', '没人写']]}],
  labels: {US: '美规', JP: '日规'},
};

test('产品对比 keeps known, distinct picks up to the limit and the market from the URL', () => {
  const state = parseState('?p=FAKE-1,FAKE-1,NOPE,FAKE-2&market=US&diff=1', DATA);
  assert.deepEqual([...state.picked], ['FAKE-1', 'FAKE-2']);
  assert.equal(state.market, 'US');
  assert.equal(state.diffOnly, true);
  assert.equal(stateQuery(state), '?p=FAKE-1%2CFAKE-2&market=US&diff=1');
  assert.equal(LIMIT, 4);
});

test('产品对比 resolves a typed code or a unique name', () => {
  assert.equal(resolvePick('fake-2', DATA), 'FAKE-2');
  assert.equal(resolvePick('Other', DATA), 'FAKE-3');
  assert.equal(resolvePick('Fake', DATA), '');
});

test('产品对比 marks rows that differ and drops rows nobody states', () => {
  const view = comparison(DATA, {picked: ['FAKE-1', 'FAKE-2'], market: 'US', diffOnly: false});
  const rows = view.groups[0].rows;
  assert.deepEqual(plain(rows.map(row => [row.name, row.differs])), [['标称容量', true], ['电芯类型', false]]);
  assert.equal(rows[1].cells[0].conflict, true);
  const only = comparison(DATA, {picked: ['FAKE-1', 'FAKE-2'], market: 'US', diffOnly: true});
  assert.deepEqual(plain(only.groups[0].rows.map(row => row.name)), ['标称容量']);
});

test('a product not sold in the market is shown as such and does not count as a difference', () => {
  const view = comparison(DATA, {picked: ['FAKE-1', 'FAKE-2'], market: 'JP', diffOnly: false});
  assert.deepEqual(plain(view.sold), [true, false]);
  assert.deepEqual(plain(view.groups[0].rows.map(row => row.differs)), [false]);
  assert.equal(sharedMarket(DATA, ['FAKE-1', 'FAKE-2'], 'JP', ['US', 'JP']), 'US');
  assert.equal(sharedMarket(DATA, ['FAKE-1', 'FAKE-3'], 'US', ['US', 'JP']), 'JP');
  assert.equal(sharedMarket(DATA, ['FAKE-2', 'FAKE-3'], 'US', ['US', 'JP']), '');
});
