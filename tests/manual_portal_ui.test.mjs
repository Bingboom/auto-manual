import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 说明书资料库 (tools/rtd_portal_assets/_static/portal.js) region memory against a minimal fake DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/portal.js', import.meta.url), 'utf8');
const KEY = 'hello-docs.manual-portal.region';

function node(props = {}) {
  const listeners = {};
  return {
    hidden: false, textContent: '', value: '', dataset: {}, classList: {toggle() {}},
    setAttribute() {}, addEventListener(name, callback) { listeners[name] = callback; },
    fire(name) { listeners[name](); },
    querySelector: () => null, querySelectorAll: () => [],
    replaceChildren() {}, append() {}, focus() {}, scrollIntoView() {},
    ...props,
  };
}

function card(region) {
  const link = node({dataset: {model: `JE-${region}`, languages: '[]'}});
  return node({dataset: {region, category: 'power', filters: 'power', search: `je-${region.toLowerCase()}`},
    querySelector: () => link});
}

// The page as the server renders it: EU (the configured default) selected.
function page(storage) {
  const options = [['US', 'US'], ['EU', 'EU'], ['UK', 'EU'], ['JP', 'JP']]
    .map(([value, binding]) => ({value, dataset: {binding}}));
  const region = node({value: 'EU', options});
  Object.defineProperty(region, 'selectedOptions', {get: () => options.filter((option) => option.value === region.value)});
  const cards = ['US', 'EU', 'JP'].map(card);
  const elements = new Map([['#region', region], ['#search-language', node({value: 'all'})]]);
  const document = {
    querySelector: (selector) => {
      if (selector.startsWith('button[data-category')) return null;
      if (!elements.has(selector)) elements.set(selector, node());
      return elements.get(selector);
    },
    querySelectorAll: (selector) => (selector === '.card' ? cards : []),
  };
  const context = {document, window: {}, location: {search: ''}, URLSearchParams, CSS: {escape: (value) => value}};
  if (storage === 'blocked') {
    Object.defineProperty(context, 'localStorage', {get() { throw new Error('SecurityError'); }});
  } else {
    context.localStorage = {getItem: (key) => storage.get(key) ?? null, setItem: (key, value) => { storage.set(key, String(value)); }};
  }
  vm.runInNewContext(script, context);
  const visible = () => cards.filter((item) => !item.hidden).map((item) => item.dataset.region);
  return {region, visible, title: () => elements.get('#market-title').textContent};
}

test('first visit keeps the configured default region', () => {
  const view = page(new Map());
  assert.equal(view.region.value, 'EU');
  assert.deepEqual(view.visible(), ['EU']);
  assert.equal(view.title(), 'EU 区域');
});

test('the last chosen region is restored before the first render', () => {
  const view = page(new Map([[KEY, 'JP']]));
  assert.equal(view.region.value, 'JP');
  assert.deepEqual(view.visible(), ['JP']);
  assert.equal(view.title(), 'JP 区域');
});

test('UK is restored as UK while showing the shared EU manuals', () => {
  const view = page(new Map([[KEY, 'UK']]));
  assert.equal(view.region.value, 'UK');
  assert.deepEqual(view.visible(), ['EU']);
  assert.equal(view.title(), 'UK 区域');
});

test('a stored value that is no longer an option falls back to the default', () => {
  const view = page(new Map([[KEY, 'XX']]));
  assert.equal(view.region.value, 'EU');
  assert.deepEqual(view.visible(), ['EU']);
});

test('changing the region remembers it', () => {
  const storage = new Map();
  const view = page(storage);
  view.region.value = 'US';
  view.region.fire('change');
  assert.equal(storage.get(KEY), 'US');
  assert.deepEqual(view.visible(), ['US']);
});

test('blocked storage keeps the default and still switches regions', () => {
  const view = page('blocked');
  assert.equal(view.region.value, 'EU');
  view.region.value = 'JP';
  assert.doesNotThrow(() => view.region.fire('change'));
  assert.deepEqual(view.visible(), ['JP']);
});

// 产品类别 sections: each family counts its visible cards, a family without a manual in the region keeps its
// heading and says so (unless a search narrows the list), and its chip shows the same count.
function classList() {
  const names = new Set();
  return {toggle: (name, on) => (on ? names.add(name) : names.delete(name)), contains: name => names.has(name)};
}

function library(regions) {
  const families = Object.entries(regions).map(([id, cardRegions]) => {
    const familyCards = cardRegions.map(card);
    const count = node();
    const empty = node({hidden: true});
    const family = node({
      dataset: {family: id, models: String(cardRegions.length + 1)}, classList: classList(),
      querySelectorAll: (selector) => (selector === '.card:not([hidden])' ? familyCards.filter((item) => !item.hidden) : []),
      querySelector: (selector) => ({'.family-count': count, '.family-empty': empty})[selector] ?? null,
    });
    const chipCount = node();
    const chip = node({classList: classList(), querySelector: () => chipCount});
    return {id, family, familyCards, count, empty, chip, chipCount};
  });
  const options = [['EU', 'EU'], ['US', 'US']].map(([value, binding]) => ({value, dataset: {binding}}));
  const region = node({value: 'EU', options});
  Object.defineProperty(region, 'selectedOptions', {get: () => options.filter((option) => option.value === region.value)});
  const search = node({value: ''});
  const elements = new Map([['#region', region], ['#search', search], ['#search-language', node({value: 'all'})]]);
  const document = {
    querySelector: (selector) => {
      const chip = families.find((item) => selector === `[data-chip="${item.id}"]`);
      if (chip) return chip.chip;
      if (!elements.has(selector)) elements.set(selector, node());
      return elements.get(selector);
    },
    querySelectorAll: (selector) => {
      if (selector === '.card') return families.flatMap((item) => item.familyCards);
      if (selector === '.family') return families.map((item) => item.family);
      return [];
    },
  };
  const context = {document, window: {}, location: {search: ''}, URLSearchParams, CSS: {escape: (value) => value},
    localStorage: {getItem: () => null, setItem: () => {}}};
  vm.runInNewContext(script, context);
  return {families: Object.fromEntries(families.map((item) => [item.id, item])), region, search};
}

test('categories count the region and say when it has none of theirs', () => {
  const view = library({portable: ['EU', 'EU', 'US'], home: ['US']});
  const {portable, home} = view.families;
  assert.equal(portable.count.textContent, '2 份');
  assert.equal(portable.chipCount.textContent, '2');
  assert.equal(portable.chip.classList.contains('is-empty'), false);
  assert.equal(home.family.hidden, false);
  assert.equal(home.family.classList.contains('is-empty'), true);
  assert.equal(home.empty.hidden, false);
  assert.equal(home.empty.textContent, 'EU 暂无说明书 · 其他区域 2 款');
  assert.equal(home.chipCount.textContent, '0');
  assert.equal(home.chip.classList.contains('is-empty'), true);
  view.region.value = 'US';
  view.region.fire('change');
  assert.equal(home.count.textContent, '1 份');
  assert.equal(home.empty.hidden, true);
});

test('其他说明书 leaves with its chip when the region has none', () => {
  const view = library({portable: ['EU'], other: ['US']});
  assert.equal(view.families.other.family.hidden, true);
  assert.equal(view.families.other.chip.hidden, true);
  view.region.value = 'US';
  view.region.fire('change');
  assert.equal(view.families.other.family.hidden, false);
  assert.equal(view.families.other.chip.hidden, false);
});

test('a search hides the categories it leaves empty', () => {
  const view = library({portable: ['EU'], home: ['US']});
  view.search.value = 'je-eu';
  view.search.fire('input');
  assert.equal(view.families.portable.family.hidden, false);
  assert.equal(view.families.home.family.hidden, true);
});
