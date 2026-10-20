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

test('research filters combine market, verification and all search words', () => {
  const {matches} = load();
  const entry = {market: 'NL', status: 'verified', text: 'Policy JE-TEST 自发自用 evidence'};
  assert.equal(matches(entry, {market: 'all', status: 'all', search: ''}), true);
  assert.equal(matches(entry, {market: 'NL', status: 'verified', search: ' je-test  自发自用 '}), true);
  assert.equal(matches(entry, {market: 'US', status: 'verified', search: ''}), false);
  assert.equal(matches(entry, {market: 'NL', status: 'unverified', search: ''}), false);
  assert.equal(matches(entry, {market: 'NL', status: 'verified', search: 'JE-TEST unknown'}), false);
});

test('missing source is a filterable state, never silently promoted to verified', () => {
  const {matches} = load();
  const entry = {market: 'NL', status: 'missing', text: 'source not available'};
  assert.equal(matches(entry, {market: 'all', status: 'missing', search: 'source'}), true);
  assert.equal(matches(entry, {market: 'all', status: 'verified', search: ''}), false);
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
  for (const id of ['research-filters', 'research-market', 'research-status', 'research-search',
    'research-count', 'research-reset', 'research-empty', 'research-empty-reset']) element(id);
  nodes.get('research-filters').hidden = true;
  nodes.get('research-market').value = 'all';
  nodes.get('research-status').value = 'all';
  const first = element('nl-policy', {
    dataset: {market: 'NL', status: 'verified'}, textContent: 'Dutch policy JE-EU',
  });
  const second = element('us-market', {
    dataset: {market: 'US', status: 'missing'}, textContent: 'US outage JE-US',
  });
  first.closest = selector => selector === '.research-event' ? first : null;
  second.closest = selector => selector === '.research-event' ? second : null;
  const context = {
    location: {hash}, window: {handlers: {}, addEventListener(type, fn) { this.handlers[type] = fn; }},
    document: {getElementById: id => nodes.get(id) || null, querySelectorAll: () => [first, second]},
  };
  vm.runInNewContext(script, context);
  return {nodes, context, first, second};
}

test('controls activate progressively and announce result count', () => {
  const {nodes, first, second} = page();
  assert.equal(nodes.get('research-filters').hidden, false);
  assert.equal(nodes.get('research-count').textContent, '2 个研究案例 / 共 2 个');
  nodes.get('research-market').value = 'NL';
  nodes.get('research-market').dispatch('change');
  assert.equal(first.hidden, false);
  assert.equal(second.hidden, true);
  assert.equal(nodes.get('research-count').textContent, '1 个研究案例 / 共 2 个');
  assert.equal(nodes.get('research-reset').hidden, false);
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
  context.location.hash = '#us-market';
  context.window.handlers.hashchange();
  assert.equal(second.hidden, false);
  assert.equal(second.scrolled, true);
  assert.equal(nodes.get('research-market').value, 'all');
  assert.equal(nodes.get('research-count').textContent, '2 个研究案例 / 共 2 个');
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
