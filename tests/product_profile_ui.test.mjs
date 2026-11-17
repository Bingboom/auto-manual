import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 产品档案 (tools/rtd_portal_assets/_static/product-profile.js): the source card's title without a DOM, then the
// market switch on a stand-in page.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-profile.js', import.meta.url), 'utf8');
const sandbox = {};
sandbox.globalThis = sandbox;
vm.runInNewContext(script, sandbox);
const {sourceTitle, showDates} = sandbox.ProductProfile;

test('the card is titled by the parameter, as on the canvas', () => {
  assert.equal(sourceTitle('重量'), '重量 · 出处');
  assert.equal(sourceTitle('额定功率（STC）'), '额定功率（STC） · 出处');
  assert.equal(sourceTitle(''), '数值 · 出处');
});

test('switching market shows that market own SKU 创建时间 only', () => {
  const dates = [{dataset: {marketDate: 'US'}, hidden: false}, {dataset: {marketDate: 'JP'}, hidden: true}];
  showDates(dates, 'JP');
  assert.deepEqual(dates.map(d => d.hidden), [true, false]);
  showDates(dates, 'US');
  assert.deepEqual(dates.map(d => d.hidden), [false, true]);
});

// A minimal stand-in for the page: two market panels, their tabs, the head's dates with their market labels and
// the 各市场差异 heads; enough to run the script's load and its market switch.
function fakeElement(dataset = {}, extra = {}) {
  const attributes = {};
  const classes = new Set();
  const listeners = {};
  return {
    dataset, hidden: false, attributes, listeners,
    setAttribute: (name, value) => { attributes[name] = value; },
    classList: {add: name => classes.add(name), toggle: (name, on) => (on ? classes.add(name) : classes.delete(name)),
                contains: name => classes.has(name)},
    addEventListener: (type, fn) => { listeners[type] = fn; },
    ...extra,
  };
}

function fakePage() {
  const switcher = fakeElement();
  switcher.hidden = true;
  const tabs = ['US', 'JP'].map(code => fakeElement({marketTab: code}, {closest: () => switcher}));
  const panels = ['US', 'JP'].map(code => fakeElement({marketPanel: code}));
  const dates = ['US', 'JP'].map(code => fakeElement({marketDate: code}));
  const labels = [fakeElement(), fakeElement()];
  const heads = ['US', 'JP'].map(code => fakeElement({diffMarket: code}));
  const all = {'[data-market-panel]': panels, '[data-market-tab]': tabs, '[data-market-date]': dates,
               '[data-market-date-label]': labels, '[data-diff-market]': heads};
  const document = {
    documentElement: fakeElement(),
    querySelectorAll: selector => all[selector] || [],
    querySelector: () => null,
    getElementById: () => null,
    addEventListener: () => {},
  };
  return {document, switcher, tabs, panels, dates, labels, heads};
}

test('on load the head keeps only the first market date, unlabelled; the switch updates it', () => {
  const page = fakePage();
  const box = {document: page.document};
  box.globalThis = box;
  vm.runInNewContext(script, box);
  assert.equal(page.switcher.hidden, false);
  assert.deepEqual(page.labels.map(l => l.hidden), [true, true]);
  assert.deepEqual(page.dates.map(d => d.hidden), [false, true]);
  assert.deepEqual(page.panels.map(p => p.hidden), [false, true]);
  assert.deepEqual(page.tabs.map(t => t.attributes['aria-selected']), ['true', 'false']);
  page.tabs[1].listeners.click();
  assert.deepEqual(page.dates.map(d => d.hidden), [true, false]);
  assert.deepEqual(page.panels.map(p => p.hidden), [true, false]);
  assert.deepEqual(page.tabs.map(t => t.attributes['aria-selected']), ['false', 'true']);
  assert.deepEqual(page.heads.map(h => h.classList.contains('is-current')), [false, true]);
  assert.deepEqual(page.labels.map(l => l.hidden), [true, true]);
});
