import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 覆盖矩阵 on 说明书工作台「交付物」 (tools/rtd_portal_assets/_static/web-progress.js) against a minimal fake DOM:
// category chips, search, 只看还有待办, the first rows of each group until 显示全部, and a row's detail.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/web-progress.js', import.meta.url), 'utf8');

function classes() {
  const set = new Set();
  return {contains: name => set.has(name), toggle: (name, on) => (on ? set.add(name) : set.delete(name))};
}
function listening(props = {}) {
  const listeners = {};
  return {hidden: false, dataset: {}, attributes: {}, classList: classes(), ...props, listeners,
    addEventListener(name, callback) { (listeners[name] ||= []).push(callback); },
    fire(name, event = {}) { (listeners[name] || []).forEach(callback => callback(event)); },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }};
}

function page() {
  const details = {};
  const makeRow = (category, rank, model, open) => {
    const toggle = listening({attributes: {'aria-expanded': 'false', 'aria-controls': `wp-d-${model}`}});
    details[`wp-d-${model}`] = listening({hidden: true});
    const row = listening({dataset: {rank: String(rank), open: open ? '1' : '0', find: `${model.toLowerCase()} e${model.slice(3)}`},
      querySelector: selector => (selector === '.wp-toggle' ? toggle : null), model, toggle});
    row.closest = selector => (selector === 'tr.wp-row' ? row : null);
    return row;
  };
  const portable = Array.from({length: 7}, (_, i) => makeRow('便携储能', i + 1, `JE-${1000 + i}`, i % 2 === 0));
  const battery = [makeRow('加电包', 1, 'JBP-2000B', true), makeRow('加电包', 2, 'JBP-3600A', false)];
  const group = (category, rows) => listening({dataset: {category}, querySelectorAll: () => rows});
  const groups = [group('便携储能', portable), group('加电包', battery)];
  const table = listening({querySelectorAll: selector => (selector === 'tbody[data-category]' ? groups : [])});
  const chips = ['', '便携储能', '加电包'].map(cat => listening({dataset: {cat}}));
  const find = listening({value: ''});
  const gaps = listening({checked: false});
  const empty = listening({hidden: true});
  const more = listening({hidden: true});
  const ids = {'wp-find': find, 'wp-gaps': gaps, 'wp-empty': empty, 'wp-more': more, ...details};
  const document = {
    querySelector: selector => (selector === '.wp-table' ? table : null),
    querySelectorAll: selector => (selector === '.wp-cat' ? chips : []),
    getElementById: id => ids[id] || null,
  };
  vm.runInNewContext(script, {document, window: {}});
  const shown = () => [...portable, ...battery].filter(row => !row.hidden).map(row => row.model);
  const click = target => table.fire('click', {target});
  return {portable, battery, groups, chips, find, gaps, empty, more, details, shown, click};
}

test('each group shows its first five rows until 显示全部', () => {
  const view = page();
  assert.deepEqual(view.shown(), ['JE-1000', 'JE-1001', 'JE-1002', 'JE-1003', 'JE-1004', 'JBP-2000B', 'JBP-3600A']);
  assert.equal(view.more.hidden, false);
  view.more.fire('click');
  assert.equal(view.shown().length, 9);
  assert.equal(view.more.hidden, true);
});

test('a category chip, the search and 只看还有待办 show every match', () => {
  const view = page();
  view.chips[2].fire('click');
  assert.deepEqual(view.shown(), ['JBP-2000B', 'JBP-3600A']);
  assert.equal(view.groups[0].hidden, true);
  assert.equal(view.chips[2].attributes['aria-pressed'], 'true');
  view.chips[0].fire('click');
  view.find.value = 'je-1006';
  view.find.fire('input');
  assert.deepEqual(view.shown(), ['JE-1006']);
  view.find.value = '';
  view.gaps.checked = true;
  view.gaps.fire('change');
  assert.deepEqual(view.shown(), ['JE-1000', 'JE-1002', 'JE-1004', 'JE-1006', 'JBP-2000B']);
  view.find.value = 'nothing';
  view.find.fire('input');
  assert.equal(view.empty.hidden, false);
});

test('a row opens and closes its language versions; a link in it does not', () => {
  const view = page();
  const row = view.portable[0];
  view.click({closest: selector => (selector === 'a' ? {} : row)});
  assert.equal(view.details['wp-d-JE-1000'].hidden, true);
  view.click({closest: selector => (selector === 'a' ? null : row)});
  assert.equal(row.toggle.attributes['aria-expanded'], 'true');
  assert.equal(view.details['wp-d-JE-1000'].hidden, false);
  assert.equal(row.classList.contains('is-open'), true);
  // Filtering the row away hides its detail too; bringing it back shows it again.
  view.chips[2].fire('click');
  assert.equal(view.details['wp-d-JE-1000'].hidden, true);
  view.chips[0].fire('click');
  assert.equal(view.details['wp-d-JE-1000'].hidden, false);
  view.click({closest: selector => (selector === 'a' ? null : row)});
  assert.equal(view.details['wp-d-JE-1000'].hidden, true);
});
