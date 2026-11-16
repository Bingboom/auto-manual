import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 四类资产 list filters (tools/rtd_portal_assets/_static/asset-layers.js) against a minimal fake DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/asset-layers.js', import.meta.url), 'utf8');

function element(props = {}) {
  const listeners = {};
  return {
    hidden: false, textContent: '', dataset: {}, value: '', checked: false,
    addEventListener(name, callback) { listeners[name] = callback; },
    fire(name, event = {preventDefault() {}}) { listeners[name](event); },
    ...props,
  };
}

function row(dataset) { return element({dataset}); }

const rows = [
  row({category: '插图', models: 'JE-X', regions: 'EU', languages: 'en', neutral: 'false', finished: 'true'}),
  row({category: '图标', models: 'ALL', regions: 'ALL', languages: '', neutral: 'true', finished: 'true'}),
  row({category: '插图', models: 'JE-Y', regions: 'US', languages: 'en fr', neutral: 'false', finished: 'false'}),
  row({category: '插图', models: 'JE-Y', regions: 'US', languages: 'shared', neutral: 'false', finished: 'true'}),
];

function page() {
  const selects = ['category', 'model', 'region', 'language'].map(key => element({dataset: {alFilter: key}}));
  const unfinished = element(), count = element(), empty = element({hidden: true});
  const form = element({
    hidden: true,
    querySelectorAll: selector => (selector === '[data-al-filter]' ? selects : []),
    querySelector: selector => ({'[data-al-unfinished]': unfinished, '[data-al-count]': count})[selector],
  });
  const table = {querySelectorAll: () => rows};
  const document = {
    querySelector: selector => ({'[data-al-filters]': form, '[data-al-list]': table, '[data-al-empty]': empty})[selector],
  };
  const window = {};
  vm.runInNewContext(script, {document, window});
  return {window, form, selects, unfinished, count, empty};
}

test('the form shows only with the script and starts with every row', () => {
  const {form, count} = page();
  assert.equal(form.hidden, false);
  assert.equal(count.textContent, '4 / 4 项');
  assert.ok(rows.every(r => !r.hidden));
});

test('a model, region or language keeps the rows every model, region or language uses', () => {
  const {selects, count} = page();
  const [, model, region, language] = selects;
  model.value = 'JE-X';
  model.fire('change');
  assert.deepEqual(rows.map(r => r.hidden), [false, false, true, true]);
  model.value = '';
  region.value = 'US';
  region.fire('change');
  assert.deepEqual(rows.map(r => r.hidden), [true, false, false, false]);
  region.value = '';
  language.value = 'fr';
  language.fire('change');
  // en-only is out; the neutral icon, the en+fr row and the shared row stay.
  assert.deepEqual(rows.map(r => r.hidden), [true, false, false, false]);
  assert.equal(count.textContent, '3 / 4 项');
});

test('只看未完成 and an empty result', () => {
  const {selects, unfinished, empty} = page();
  unfinished.checked = true;
  unfinished.fire('change');
  assert.deepEqual(rows.map(r => r.hidden), [true, true, false, true]);
  selects[0].value = '图标';
  selects[0].fire('change');
  assert.ok(rows.every(r => r.hidden));
  assert.equal(empty.hidden, false);
});

test('matches is pure and shared', () => {
  const {window} = page();
  assert.equal(window.assetLayers.matches(rows[1].dataset, {model: 'ANY', region: 'JP', language: 'ko'}), true);
  assert.equal(window.assetLayers.matches(rows[0].dataset, {category: '图标'}), false);
});
