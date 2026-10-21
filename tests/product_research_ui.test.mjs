import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-research.js', import.meta.url), 'utf8');
function load() {
  const context = {};
  vm.runInNewContext(script, context);
  return context.ProductResearchFilters;
}

const ALL = {market: 'all', status: 'all', review: 'all', search: ''};

test('event filters combine market, verification, decision state and all search words', () => {
  const {matches} = load();
  const entry = {market: 'NL', status: 'verified', review: 'pending', text: 'Policy JE-TEST 自发自用 evidence'};
  assert.equal(matches(entry, ALL), true);
  assert.equal(matches(entry, {...ALL, market: 'NL', status: 'verified', search: ' je-test  自发自用 '}), true);
  assert.equal(matches(entry, {...ALL, market: 'US'}), false);
  assert.equal(matches(entry, {...ALL, status: 'unverified'}), false);
  assert.equal(matches(entry, {...ALL, search: 'JE-TEST unknown'}), false);
  assert.equal(matches(entry, {...ALL, review: 'pending'}), true);
  assert.equal(matches(entry, {...ALL, review: 'reviewed'}), false);
});

test('missing source is a filterable state, never silently promoted to verified', () => {
  const {matches} = load();
  const entry = {market: 'NL', status: 'missing', review: 'pending', text: 'source not available'};
  assert.equal(matches(entry, {...ALL, status: 'missing', search: 'source'}), true);
  assert.equal(matches(entry, {...ALL, status: 'verified'}), false);
});

test('a quick tile is pressed only while the filters are exactly its condition', () => {
  const {pressed} = load();
  const pending = {field: 'review', value: 'pending'};
  const all = {field: 'all', value: 'all'};
  assert.equal(pressed(all, ALL), true);
  assert.equal(pressed(pending, ALL), false);
  assert.equal(pressed(pending, {...ALL, review: 'pending'}), true);
  assert.equal(pressed(all, {...ALL, review: 'pending'}), false);
  assert.equal(pressed(pending, {...ALL, review: 'pending', market: 'NL'}), false);
  assert.equal(pressed(pending, {...ALL, review: 'pending', search: 'policy'}), false);
});

test('deep links tolerate malformed percent encodings', () => {
  const {hashId} = load();
  assert.equal(hashId('#test-policy'), 'test-policy');
  assert.equal(hashId('#%E7%A0%94%E7%A9%B6'), '研究');
  assert.equal(hashId('#%invalid'), '');
});

function page(hash = '') {
  const nodes = new Map();
  const element = (id, values = {}) => {
    const node = {
      id, value: '', hidden: false, handlers: {}, textContent: '', parentElement: null,
      addEventListener(type, fn) { this.handlers[type] = fn; },
      dispatch(type) { this.handlers[type]?.(); },
      focus() { this.focused = true; },
      scrollIntoView() { this.scrolled = true; },
      closest() { return null; },
      ...values,
    };
    nodes.set(id, node);
    return node;
  };
  for (const id of ['research-filters', 'research-market', 'research-status', 'research-review',
    'research-search', 'research-count', 'research-reset', 'research-empty', 'research-empty-reset']) element(id);
  nodes.get('research-filters').hidden = true;
  for (const id of ['research-market', 'research-status', 'research-review']) nodes.get(id).value = 'all';
  const first = element('event-nl-policy', {
    dataset: {market: 'NL', status: 'verified', review: 'pending'}, textContent: 'Dutch policy JE-EU',
    row: {open: false},
  });
  const second = element('event-us-market', {
    dataset: {market: 'US', status: 'missing', review: 'reviewed'}, textContent: 'US outage JE-US',
    row: {open: false},
  });
  for (const entry of [first, second]) {
    entry.closest = selector => selector === '.research-event' ? entry : null;
    entry.querySelector = selector => selector === 'details.event-entry' ? entry.row : null;
  }
  const tile = (field, value) => ({
    dataset: value ? {quickField: field, quickValue: value} : {quickField: field}, attributes: {}, handlers: {},
    addEventListener(type, fn) { this.handlers[type] = fn; },
    dispatch(type) { this.handlers[type]?.(); },
    setAttribute(name, text) { this.attributes[name] = text; },
  });
  const tiles = [tile('all'), tile('review', 'pending'), tile('review', 'reviewed'), tile('status', 'verified')];
  const context = {
    location: {hash}, window: {handlers: {}, addEventListener(type, fn) { this.handlers[type] = fn; }},
    document: {
      getElementById: id => nodes.get(id) || null,
      querySelectorAll: selector => ({'.research-event': [first, second], '[data-quick-field]': tiles})[selector] || [],
    },
  };
  vm.runInNewContext(script, context);
  return {nodes, context, first, second, tiles};
}

test('controls activate progressively and announce result count', () => {
  const {nodes, first, second} = page();
  assert.equal(nodes.get('research-filters').hidden, false);
  assert.equal(nodes.get('research-count').textContent, '2 个外部事件 / 共 2 个');
  nodes.get('research-market').value = 'NL';
  nodes.get('research-market').dispatch('change');
  assert.equal(first.hidden, false);
  assert.equal(second.hidden, true);
  assert.equal(nodes.get('research-count').textContent, '1 个外部事件 / 共 2 个');
  assert.equal(nodes.get('research-reset').hidden, false);
});

test('quick tiles filter in one click and show which one is active', () => {
  const {nodes, first, second, tiles} = page();
  assert.deepEqual(tiles.map(tile => tile.attributes['aria-pressed']), ['true', 'false', 'false', 'false']);
  nodes.get('research-market').value = 'US';
  tiles[1].dispatch('click');
  assert.equal(nodes.get('research-market').value, 'all');
  assert.equal(nodes.get('research-review').value, 'pending');
  assert.equal(first.hidden, false);
  assert.equal(second.hidden, true);
  assert.deepEqual(tiles.map(tile => tile.attributes['aria-pressed']), ['false', 'true', 'false', 'false']);
  tiles[3].dispatch('click');
  assert.equal(nodes.get('research-review').value, 'all');
  assert.equal(nodes.get('research-status').value, 'verified');
  tiles[0].dispatch('click');
  assert.equal(nodes.get('research-count').textContent, '2 个外部事件 / 共 2 个');
  assert.deepEqual(tiles.map(tile => tile.attributes['aria-pressed']), ['true', 'false', 'false', 'false']);
});

test('the decision filter separates pending from judged events and resets with the rest', () => {
  const {nodes, first, second} = page();
  nodes.get('research-review').value = 'reviewed';
  nodes.get('research-review').dispatch('change');
  assert.equal(first.hidden, true);
  assert.equal(second.hidden, false);
  assert.equal(nodes.get('research-reset').hidden, false);
  nodes.get('research-reset').dispatch('click');
  assert.equal(nodes.get('research-review').value, 'all');
  assert.equal(first.hidden, false);
  assert.equal(nodes.get('research-count').textContent, '2 个外部事件 / 共 2 个');
});

test('empty result reset restores every case and returns focus to search', () => {
  const {nodes, first, second} = page();
  nodes.get('research-search').value = 'not-found';
  nodes.get('research-search').dispatch('input');
  assert.equal(nodes.get('research-empty').hidden, false);
  assert.equal(first.hidden, true);
  assert.equal(second.hidden, true);
  nodes.get('research-empty-reset').dispatch('click');
  assert.equal(nodes.get('research-empty').hidden, true);
  assert.equal(nodes.get('research-search').value, '');
  assert.equal(nodes.get('research-search').focused, true);
  assert.equal(first.hidden, false);
  assert.equal(second.hidden, false);
});

test('a deep link reveals a filtered event and preserves the underlying cases', () => {
  const {nodes, context, second} = page();
  nodes.get('research-market').value = 'NL';
  nodes.get('research-market').dispatch('change');
  assert.equal(second.hidden, true);
  context.location.hash = '#event-us-market';
  context.window.handlers.hashchange();
  assert.equal(second.hidden, false);
  assert.equal(second.row.open, true);
  assert.equal(second.scrolled, true);
  assert.equal(nodes.get('research-market').value, 'all');
  assert.equal(nodes.get('research-count').textContent, '2 个外部事件 / 共 2 个');
});

test('a deep link opens nested native disclosures without rewriting HTML', () => {
  const {nodes, context, second} = page();
  const outer = {open: false, parentElement: null};
  const inner = {open: false, parentElement: {closest: () => outer}};
  nodes.set('evidence-detail', {
    closest: selector => selector === '.research-event' ? second : inner,
    scrollIntoView() { this.scrolled = true; },
  });
  context.location.hash = '#evidence-detail';
  context.window.handlers.hashchange();
  assert.equal(inner.open, true);
  assert.equal(outer.open, true);
  assert.equal(nodes.get('evidence-detail').scrolled, true);
});

test('empty page and malformed hash are harmless', () => {
  const context = {document: {getElementById: () => null}};
  assert.doesNotThrow(() => vm.runInNewContext(script, context));
  assert.doesNotThrow(() => page('#%invalid'));
});
