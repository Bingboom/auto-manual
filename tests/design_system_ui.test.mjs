import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/design-system.js', import.meta.url), 'utf8');

function frame({bottom = 120, margin = '8px', scrollY = 0, hidden = false, crossOrigin = false} = {}) {
  const listeners = {};
  const main = {getBoundingClientRect: () => ({bottom})};
  const doc = {
    querySelector: (selector) => (selector === 'main' ? main : null),
    defaultView: {scrollY, getComputedStyle: () => ({marginBottom: margin})},
  };
  const element = {
    style: {},
    offsetParent: hidden ? null : {},
    addEventListener: (name, callback) => { listeners[name] = callback; },
    fire: (name) => listeners[name](),
  };
  Object.defineProperty(element, 'contentDocument', {
    get() { if (crossOrigin) throw new Error('blocked'); return doc; },
  });
  return element;
}

function run(frames, withObserver = true) {
  const observed = [];
  const window = withObserver ? {ResizeObserver: class { observe(target) { observed.push(target); } }} : {};
  const context = {
    window, ResizeObserver: window.ResizeObserver,
    document: {querySelectorAll: (selector) => (selector === 'iframe.ds-preview' ? frames : []), getElementById: () => null},
  };
  vm.runInNewContext(script, context);
  frames.forEach((item) => item.fire('load'));
  return observed;
}

test('a loaded preview is sized to the bottom of its main element', () => {
  const preview = frame({bottom: 120.2, margin: '8px', scrollY: 4});
  const observed = run([preview]);
  assert.equal(preview.style.height, '133px');
  assert.equal(observed.length, 1);
});

test('a hidden or cross-origin preview keeps its declared height', () => {
  const hidden = frame({hidden: true});
  const foreign = frame({crossOrigin: true});
  run([hidden, foreign], false);
  assert.equal(hidden.style.height, undefined);
  assert.equal(foreign.style.height, undefined);
});

test('a gallery card, thumbnail or open preview scales from the 720px layout width; a hidden one waits', () => {
  const set = [];
  const box = (clientWidth) => ({clientWidth, style: {setProperty: (name, value) => set.push([clientWidth, name, value])}});
  const observed = [];
  const window = {ResizeObserver: class { observe(target) { observed.push(target); } }};
  const boxes = [box(360), box(0), box(900)];
  vm.runInNewContext(script, {
    window, ResizeObserver: window.ResizeObserver,
    document: {querySelectorAll: (selector) => (selector === '.ds-shot-frame, .ds-zoom' ? boxes : []), getElementById: () => null},
  });
  assert.deepEqual(set, [[360, '--ds-shot-scale', '0.5'], [900, '--ds-shot-scale', '1']]);
  assert.equal(observed.length, 3);
});

// The inner tabs (2026-11 step 10) against a small fake DOM: a selector matcher for tag, #id, .class and [attr],
// comma lists and the descendant combinator, which is all design-system.js asks of the page.
function matcher(part) {
  const tag = (part.match(/^[a-z]+/) || [])[0];
  const id = (part.match(/#([\w-]+)/) || [])[1];
  const names = [...part.matchAll(/\.([\w-]+)/g)].map((match) => match[1]);
  const attrs = [...part.matchAll(/\[([\w-]+)\]/g)].map((match) => match[1]);
  return (node) => (!tag || node.tag === tag) && (!id || node.id === id)
    && names.every((name) => node.classList.contains(name)) && attrs.every((name) => name in node.attributes);
}
function chains(selector) {
  return selector.split(',').map((one) => one.trim().split(/\s+/).map(matcher));
}
function matches(node, chain) {
  if (!chain[chain.length - 1](node)) return false;
  let index = chain.length - 2;
  for (let up = node.parent; up && index >= 0; up = up.parent) if (chain[index](up)) index -= 1;
  return index < 0;
}
class Node {
  constructor(tag, {id = '', cls = '', data = {}, attrs = {}, hidden = false, text = ''} = {}) {
    Object.assign(this, {tag, id, dataset: {...data}, attributes: {...attrs}, hidden, textContent: text, children: [],
      parent: null, listeners: {}, open: false, focused: false, style: {setProperty() {}}});
    const set = new Set(cls.split(' ').filter(Boolean));
    this.classList = {contains: (name) => set.has(name), toggle: (name, on = !set.has(name)) => (on ? set.add(name) : set.delete(name))};
  }
  add(...kids) { kids.forEach((kid) => { kid.parent = this; this.children.push(kid); }); return this; }
  * walk() { for (const kid of this.children) { yield kid; yield* kid.walk(); } }
  querySelectorAll(selector) { const all = chains(selector); return [...this.walk()].filter((node) => all.some((chain) => matches(node, chain))); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) {
    const all = chains(selector);
    for (let node = this; node; node = node.parent) if (all.some((chain) => matches(node, chain))) return node;
    return null;
  }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  fire(name, event = {}) { (this.listeners[name] || []).forEach((callback) => callback(event)); }
  focus() { this.focused = true; }
}

function card(id, search) {
  const open = new Node('button', {cls: 'ds-comp-open', attrs: {'aria-expanded': 'false'}});
  const item = new Node('article', {id: `component-${id}`, cls: 'ds-comp', data: {search}}).add(open);
  const close = new Node('button', {cls: 'ds-comp-close'});
  const detail = new Node('div', {id: `component-${id}-detail`, cls: 'ds-comp-detail', hidden: true}).add(close);
  return {item, detail, open, close};
}
function filterBar(groups) {
  const chips = ['', ...groups].map((group, index) => new Node('button', {cls: 'ds-chip', data: {group},
    attrs: {'aria-pressed': String(index === 0)}}));
  const input = new Node('input', {});
  input.value = '';
  return {bar: new Node('div', {cls: 'ds-filter'}).add(...chips, input), chips, input};
}
function tile(group, name, search) {
  return new Node('button', {cls: 'ds-tile', data: {asset: `asset-${group}-${name}`, search}, attrs: {'aria-pressed': 'false'}});
}

function designPage({hash = ''} = {}) {
  const titles = [card('title-l1', '一级标题深色条 hb-title-l1'), card('title-l2', '二级标题 hb-title-l2')];
  const tables = [card('spec-table', '规格表 hb-table-spec'), card('lcd-icon-table', '显示屏图标表 hb-table-lcd-icon')];
  const section = (group, cards) => new Node('section', {cls: 'ds-comp-group', data: {group}})
    .add(new Node('div', {cls: 'ds-comp-grid'}).add(...cards.flatMap((one) => [one.item, one.detail])));
  const compFilter = filterBar(['titles', 'tables']);
  const compEmpty = new Node('p', {cls: 'ds-empty', hidden: true});
  const components = new Node('div', {id: 'components'})
    .add(compFilter.bar, section('titles', titles), section('tables', tables), compEmpty);

  const symbols = [tile('symbols', 'shock', 'symbol_electric_shock.svg electric-shock 有触电危险。'),
    tile('symbols', 'li-ion', 'symbol_li_ion.svg li-ion 锂离子电池')];
  const lcd = [tile('lcd', 'meter', 'lcd_smart-meter.png 智能电表')];
  const box = (group, tiles) => new Node('details', {cls: 'ds-asset-group', data: {group}, attrs: {'data-ds-more': ''}})
    .add(new Node('div', {cls: 'ds-tiles'}).add(...tiles));
  const showAll = new Node('button', {cls: 'ds-show-all', text: '显示全部 76 个', attrs: {'aria-expanded': 'false'}});
  const symbolBox = box('symbols', symbols).add(showAll);
  const lcdBox = box('lcd', lcd);
  const notes = ['symbols', 'lcd'].map((group, index) => new Node('section', {cls: 'ds-side-group', data: {group}, hidden: index > 0}));
  const sideAssets = [...symbols, ...lcd].map((one) => new Node('section', {id: one.dataset.asset, cls: 'ds-side-asset', hidden: true}));
  const copy = new Node('button', {cls: 'ds-copy', data: {copy: 'electric-shock/bolt-triangle-tinted'}, text: '复制语义键'});
  sideAssets[0].add(copy);
  const side = new Node('aside', {cls: 'ds-asset-side'}).add(...notes, ...sideAssets);
  const assetFilter = filterBar(['symbols', 'lcd']);
  const assetEmpty = new Node('p', {cls: 'ds-empty', hidden: true});
  const assets = new Node('div', {id: 'assets'})
    .add(assetFilter.bar, new Node('div', {cls: 'ds-asset-groups'}).add(symbolBox, lcdBox, assetEmpty), side);

  const printMore = new Node('button', {cls: 'ds-show-all', text: '显示全部 34 种', attrs: {'aria-expanded': 'false'}});
  const printType = new Node('section', {id: 'print-type', attrs: {'data-ds-more': ''}}).add(printMore);
  const root = new Node('main', {}).add(components, assets, printType);
  const ids = id => [...root.walk()].find((node) => node.id === id) || null;
  const replaced = [];
  const copied = [];
  const window = {listeners: {}, addEventListener(name, callback) { this.listeners[name] = callback; }};
  const location = {hash};
  vm.runInNewContext(script, {
    window, location, setTimeout: () => {},
    history: {replaceState: (state, title, url) => { replaced.push(url); location.hash = url; }},
    navigator: {clipboard: {writeText: (text) => { copied.push(text); return {then: (done) => done()}; }}},
    document: {getElementById: ids, querySelectorAll: (selector) => root.querySelectorAll(selector)},
  });
  return {titles, tables, compFilter, compEmpty, symbols, lcd, symbolBox, lcdBox, notes, sideAssets, assetFilter, assetEmpty,
    showAll, printMore, printType, copy, replaced, copied, window, location};
}
const visible = (nodes) => nodes.filter((node) => !node.hidden).map((node) => node.id || node.dataset.asset || node.dataset.group);

test('a card opens its detail, one at a time, and the address follows it', () => {
  const view = designPage();
  const [first, second] = view.titles;
  first.open.fire('click');
  assert.equal(first.detail.hidden, false);
  assert.equal(first.open.getAttribute('aria-expanded'), 'true');
  assert.ok(first.item.classList.contains('is-open'));
  second.open.fire('click');
  assert.deepEqual([first.detail.hidden, second.detail.hidden], [true, false]);
  assert.equal(first.open.getAttribute('aria-expanded'), 'false');
  second.open.fire('click');
  assert.equal(second.detail.hidden, true);
  assert.deepEqual(view.replaced, ['#component-title-l1', '#component-title-l2', '#components']);
  first.open.fire('click');
  first.close.fire('click');
  assert.equal(first.detail.hidden, true);
  assert.ok(first.open.focused);
});

test('chips and search narrow the cards; a card filtered away closes, and no match says so', () => {
  const view = designPage();
  view.tables[0].open.fire('click');
  view.compFilter.chips[1].fire('click');  // 标题
  assert.deepEqual(visible([...view.titles, ...view.tables].map((one) => one.item)), ['component-title-l1', 'component-title-l2']);
  assert.equal(view.tables[0].detail.hidden, true);
  assert.equal(view.compFilter.chips[0].getAttribute('aria-pressed'), 'false');
  view.compFilter.chips[0].fire('click');  // 全部
  view.compFilter.input.value = ' HB-TABLE-LCD ';
  view.compFilter.input.fire('input');
  assert.deepEqual(visible([...view.titles, ...view.tables].map((one) => one.item)), ['component-lcd-icon-table']);
  assert.equal(view.compEmpty.hidden, true);
  view.compFilter.input.value = 'zzz';
  view.compFilter.input.fire('input');
  assert.equal(view.compEmpty.hidden, false);
});

test('a #component- address opens that card', () => {
  const view = designPage({hash: '#component-spec-table'});
  assert.equal(view.tables[0].detail.hidden, false);
  view.location.hash = '#component-title-l2';
  view.window.listeners.hashchange();
  assert.deepEqual([view.tables[0].detail.hidden, view.titles[1].detail.hidden], [true, false]);
});

test('a tile selects into the side panel; with none selected the panel shows its group notes', () => {
  const view = designPage();
  assert.deepEqual(visible([...view.notes, ...view.sideAssets]), ['symbols']);
  view.symbols[0].fire('click');
  assert.deepEqual(visible([...view.notes, ...view.sideAssets]), ['asset-symbols-shock']);
  assert.equal(view.symbols[0].getAttribute('aria-pressed'), 'true');
  view.symbols[0].fire('click');  // again: deselect
  assert.deepEqual(visible([...view.notes, ...view.sideAssets]), ['symbols']);
  view.symbols[0].fire('click');
  view.assetFilter.input.value = 'li-ion';
  view.assetFilter.input.fire('input');  // the selected tile is filtered away
  assert.deepEqual(visible(view.symbols), ['asset-symbols-li-ion']);
  assert.deepEqual(visible([view.symbolBox, view.lcdBox]), ['symbols']);
  assert.ok(view.symbolBox.classList.contains('is-search') && view.symbolBox.open);
  assert.deepEqual(visible([...view.notes, ...view.sideAssets]), ['symbols']);
  view.assetFilter.input.value = '';
  view.assetFilter.input.fire('input');
  view.assetFilter.chips[2].fire('click');  // 显示屏图标
  assert.deepEqual(visible([view.symbolBox, view.lcdBox]), ['lcd']);
  assert.deepEqual(visible([...view.notes, ...view.sideAssets]), ['lcd']);
  view.assetFilter.input.value = 'nothing';
  view.assetFilter.input.fire('input');
  assert.equal(view.assetEmpty.hidden, false);
});

test('copy puts the semantic key on the clipboard', () => {
  const view = designPage();
  view.copy.fire('click');
  assert.deepEqual(view.copied, ['electric-shock/bolt-triangle-tinted']);
  assert.equal(view.copy.textContent, '已复制');
});

test('显示全部 unfolds its host and folds it again', () => {
  const view = designPage();
  view.printMore.fire('click');
  assert.ok(view.printType.classList.contains('is-all'));
  assert.deepEqual([view.printMore.getAttribute('aria-expanded'), view.printMore.textContent], ['true', '收起']);
  view.printMore.fire('click');
  assert.ok(!view.printType.classList.contains('is-all'));
  assert.equal(view.printMore.textContent, '显示全部 34 种');
  view.showAll.fire('click');
  assert.ok(view.symbolBox.classList.contains('is-all'));
});
