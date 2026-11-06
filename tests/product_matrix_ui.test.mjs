import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 产品矩阵 (tools/rtd_portal_assets/_static/product-matrix.js) against a minimal fake DOM: two category panels,
// a product card per panel and its detail, the tabs, and a detail's close link.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-matrix.js', import.meta.url), 'utf8');

function classes() {
  const set = new Set();
  return {add: name => set.add(name), remove: name => set.delete(name), contains: name => set.has(name),
          toggle: (name, on) => (on ? set.add(name) : set.delete(name))};
}

function node(props = {}) {
  const listeners = {};
  return {
    hidden: false, dataset: {}, attributes: {}, classList: classes(), focused: false, scrolled: false,
    setAttribute(name, value) { this.attributes[name] = value; },
    getAttribute(name) { return this.attributes[name] ?? null; },
    addEventListener(name, callback) { (listeners[name] ||= []).push(callback); },
    fire(name, event = {}) { (listeners[name] || []).forEach(callback => callback(event)); },
    focus() { this.focused = true; },
    scrollIntoView() { this.scrolled = true; },
    closest(selector) { return this.matches(selector) ? this : null; },
    matches() { return false; },
    ...props,
  };
}

function page({hash = '', panels = true} = {}) {
  const ids = panels ? ['portable', 'accessory'] : [];
  const panelNodes = ids.map(id => node({id: `cat-${id}`, dataset: {panel: id}}));
  const details = [node({id: 'p-E1000V2'}), node({id: 'p-行车快充'})];
  panelNodes.forEach((panel, index) => { panel.contains = element => element === details[index]; });
  const card = (id, panel) => {
    const item = node({dataset: {product: id}, attributes: {'aria-expanded': 'false'}});
    item.classList.add('mx-prod');
    item.matches = selector => selector.includes('[data-product]');
    item.panel = panel;
    return item;
  };
  const cards = [card('p-E1000V2', 0), card('p-行车快充', 1)];
  const pair = node({dataset: {product: 'p-行车快充'}});
  pair.matches = selector => selector.includes('[data-product]');
  const closer = node({dataset: {}});
  closer.matches = selector => selector.includes('[data-close]');
  const tabs = ids.map(id => node({dataset: {tab: id}}));
  const root = node();
  const documentListeners = {};
  const replaced = [];
  const document = {
    documentElement: root,
    querySelectorAll: selector => {
      if (selector === '[data-panel]') return panelNodes;
      if (selector === '[data-tab]') return tabs;
      if (selector === '.mx-detail') return details;
      const match = selector.match(/^\.mx-prod\[data-product="(.+)"\]$/);
      return match ? cards.filter(item => item.dataset.product === match[1]) : [];
    },
    addEventListener(name, callback) { documentListeners[name] = callback; },
  };
  const window = {...node(), location: {hash}};
  const history = {replaceState(state, title, url) { replaced.push(url); window.location.hash = url; }};
  vm.runInNewContext(script, {document, window, history, CSS: {escape: value => value}});
  const click = target => {
    let prevented = false;
    documentListeners.click({target, preventDefault() { prevented = true; }});
    return prevented;
  };
  const shown = () => panelNodes.filter(panel => !panel.hidden).map(panel => panel.dataset.panel);
  const open = () => details.filter(detail => detail.classList.contains('is-open')).map(detail => detail.id);
  return {root, tabs, cards, details, pair, closer, window, replaced, click, shown, open};
}

test('JavaScript shows the first category and turns the tabs into a switch', () => {
  const view = page();
  assert.equal(view.root.classList.contains('mx-js'), true);
  assert.deepEqual(view.shown(), ['portable']);
  assert.equal(view.tabs[0].classList.contains('is-on'), true);
  view.tabs[1].fire('click', {preventDefault() {}});
  assert.deepEqual(view.shown(), ['accessory']);
  assert.equal(view.tabs[1].getAttribute('aria-current'), 'true');
  assert.deepEqual(view.replaced, ['#cat-accessory']);
});

test('a card opens its detail under its row and a second click closes it', () => {
  const view = page();
  assert.equal(view.click(view.cards[0]), true);
  assert.deepEqual(view.open(), ['p-E1000V2']);
  assert.equal(view.cards[0].getAttribute('aria-expanded'), 'true');
  assert.equal(view.details[0].scrolled, true);
  assert.equal(view.details[0].focused, false);
  assert.equal(view.window.location.hash, '#p-E1000V2');
  view.click(view.cards[0]);
  assert.deepEqual(view.open(), []);
  assert.equal(view.cards[0].getAttribute('aria-expanded'), 'false');
  assert.equal(view.window.location.hash, '#cat-portable');
});

test('a partner link opens that product in its own category and moves focus there', () => {
  const view = page();
  view.click(view.cards[0]);
  view.click(view.pair);
  assert.deepEqual(view.open(), ['p-行车快充']);
  assert.deepEqual(view.shown(), ['accessory']);
  assert.equal(view.details[1].focused, true);
  assert.equal(view.cards[0].getAttribute('aria-expanded'), 'false');
});

test('the close link closes the detail and keeps the category in the address', () => {
  const view = page();
  view.click(view.cards[1]);
  view.click(view.closer);
  assert.deepEqual(view.open(), []);
  assert.equal(view.window.location.hash, '#cat-accessory');
});

test('the address opens a named product or category, and other clicks pass through', () => {
  const view = page({hash: '#' + encodeURIComponent('p-行车快充')});
  assert.deepEqual(view.open(), ['p-行车快充']);
  assert.deepEqual(view.shown(), ['accessory']);
  view.window.location.hash = '#cat-portable';
  view.window.fire('hashchange');
  assert.deepEqual(view.open(), []);
  assert.deepEqual(view.shown(), ['portable']);
  assert.equal(view.click(node()), false);
});

test('a page without categories is left alone', () => {
  const view = page({panels: false});
  assert.equal(view.root.classList.contains('mx-js'), false);
});
