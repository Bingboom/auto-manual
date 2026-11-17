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
const {rowMatches, compareValues, csvText, csvCell} = load('product-table.js').ProductTable;
const {LIMIT, parseState, stateQuery, resolvePick, comparison, sharedMarket, itemPath, columnHead} = load('product-compare.js').ProductCompare;

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

test('参数表 puts text-only cells of a number column after the numbers and before empty ones, both ways', () => {
  const values = ['', '100~120', '20', '约 5', '3', ''];
  const up = [...values].sort((a, b) => compareValues(a, b, true, 'ascending'));
  const down = [...values].sort((a, b) => compareValues(a, b, true, 'descending'));
  assert.deepEqual(plain(up.slice(0, 2)), ['3', '20']);
  assert.deepEqual(plain(down.slice(0, 2)), ['20', '3']);
  for (const order of [up, down]) {
    assert.deepEqual(plain(order.slice(2, 4)).sort(), ['100~120', '约 5']);
    assert.deepEqual(plain(order.slice(4)), ['', '']);
  }
});

test('no CSV cell can run as a formula; plain numbers stay numbers', () => {
  const defused = raw => csvCell(raw).replace(/^"/, '').startsWith("'");
  for (const raw of ['=1+1', '+SUM(A1)', '@cmd', '@SUM(1)', '\t=1', '\r=1', '-x', "-1+cmd|' /C calc'!A0",
    "+cmd|' /C calc'!A0", '-10-40', '+1*2', '-1,5 ', '-1+A1', '-1&"x"', '-1 (x)']) {
    assert.ok(defused(raw), raw);
  }
  assert.equal(csvCell('-10'), '-10');
  assert.equal(csvCell('-0.5'), '-0.5');
  assert.equal(csvCell('+3'), '+3');
  assert.equal(csvCell('100 W'), '100 W');
  assert.equal(csvCell('=A1,"x"'), `"'=A1,""x"""`);
});

test('plain text after a sign, which cannot be a formula, keeps no apostrophe', () => {
  for (const raw of ['-10–40 °C', '-10 ~ 40°C', '+5 °C', '-10~45 °C', '-20 °C to 60 °C']) {
    assert.equal(csvCell(raw), raw);
  }
  for (const raw of ['-10', '-0.5', '-.5', '+3', '-12.']) assert.equal(csvCell(raw), raw);
});

test('the CSV starts with a BOM and quotes what needs quoting', () => {
  const text = csvText([['产品', '说明'], ['A', 'x, "y"\nz']]);
  assert.equal(text.charCodeAt(0), 0xfeff);
  assert.equal(text.slice(1), '产品,说明\r\nA,"x, ""y""\nz"\r\n');
});

const DATA = {
  products: [
    {model: 'FAKE-1', name: 'Fake One', project: 'P-FAKE-1', markets: ['US', 'JP'],
     values: {US: {cap: ['1000 Wh', '#1000', false], cell: ['LFP', 'lfp', true]}, JP: {cap: ['1000 Wh', '#1000', false]}}},
    {model: 'FAKE-2', name: 'Fake Two', project: 'P-FAKE-1', markets: ['US'],
     values: {US: {cap: ['2000 Wh', '#2000', false], cell: ['LFP', 'lfp', false]}}},
    {model: 'FAKE-3', name: 'Other Three', project: '', markets: ['JP'], values: {JP: {cap: ['1000 Wh', '#1000', false]}}},
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

test('a missing value is no difference: at least two stated values must differ', () => {
  const data = {...DATA, products: [
    {model: 'M-1', name: 'One', project: '', markets: ['US'], values: {US: {cap: ['1 Wh', '#1', false]}}},
    {model: 'M-2', name: 'Two', project: '', markets: ['US'], values: {US: {}}},
    {model: 'M-3', name: 'Three', project: '', markets: ['US'], values: {US: {cap: ['1 Wh', '#1', false]}}},
  ]};
  const both = comparison(data, {picked: ['M-1', 'M-2'], market: 'US', diffOnly: false});
  assert.deepEqual(plain(both.groups[0].rows.map(row => [row.name, row.differs])), [['标称容量', false]]);
  assert.equal(both.groups[0].rows[0].cells[1].text, '');
  const three = comparison(data, {picked: ['M-1', 'M-2', 'M-3'], market: 'US', diffOnly: true});
  assert.deepEqual(plain(three.groups), []);
});

test('产品对比 links a product page by the model code itself', () => {
  for (const model of ['FAKE-1000F', 'FAKE-AD01A.v2', 'X_1']) assert.equal(itemPath(model), model);
});

test('a product not sold in the market is shown as such and does not count as a difference', () => {
  const view = comparison(DATA, {picked: ['FAKE-1', 'FAKE-2'], market: 'JP', diffOnly: false});
  assert.deepEqual(plain(view.sold), [true, false]);
  assert.deepEqual(plain(view.groups[0].rows.map(row => row.differs)), [false]);
  assert.equal(sharedMarket(DATA, ['FAKE-1', 'FAKE-2'], 'JP', ['US', 'JP']), 'US');
  assert.equal(sharedMarket(DATA, ['FAKE-1', 'FAKE-3'], 'US', ['US', 'JP']), 'JP');
  assert.equal(sharedMarket(DATA, ['FAKE-2', 'FAKE-3'], 'US', ['US', 'JP']), '');
});

test('产品对比 heads a column with the name and the model code, no project, and says when it is not sold', () => {
  const [one, two] = DATA.products;
  assert.deepEqual(plain(columnHead(one, true, '美规')), {name: 'Fake One', model: 'FAKE-1', absent: ''});
  assert.deepEqual(plain(columnHead(two, false, '日规')), {name: 'Fake Two', model: 'FAKE-2', absent: '无日规版本'});
  assert.ok(!JSON.stringify(columnHead(one, true, '美规')).includes('P-FAKE'));
});
