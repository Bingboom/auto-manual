import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 说明书资料库 (tools/rtd_portal_assets/_static/portal.js) region memory against a minimal fake DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/portal.js', import.meta.url), 'utf8');
const KEY = 'hello-docs.manual-portal.region';
const ALL_KEY = 'hello-docs.manual-portal.region-all';

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
    context.localStorage = {getItem: (key) => storage.get(key) ?? null, setItem: (key, value) => { storage.set(key, String(value)); },
      removeItem: (key) => { storage.delete(key); }};
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

test('changing the region remembers it and ends 产品知识\'s 全部区域', () => {
  const storage = new Map([[ALL_KEY, '1']]);
  const view = page(storage);
  view.region.value = 'US';
  view.region.fire('change');
  assert.equal(storage.get(KEY), 'US');
  assert.equal(storage.has(ALL_KEY), false);
  assert.deepEqual(view.visible(), ['US']);
});

test('blocked storage keeps the default and still switches regions', () => {
  const view = page('blocked');
  assert.equal(view.region.value, 'EU');
  view.region.value = 'JP';
  assert.doesNotThrow(() => view.region.fire('change'));
  assert.deepEqual(view.visible(), ['JP']);
});
