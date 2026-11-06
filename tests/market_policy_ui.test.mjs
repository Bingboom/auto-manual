import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 市场与政策 (tools/rtd_portal_assets/_static/market-policy.js) against a minimal fake DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/market-policy.js', import.meta.url), 'utf8');

function node(props = {}) {
  const listeners = {};
  return {
    hidden: false, textContent: '', dataset: {}, attributes: {},
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(name, callback) { (listeners[name] ||= []).push(callback); },
    fire(name) { (listeners[name] || []).forEach(callback => callback()); },
    ...props,
  };
}

function page({ids = ['pt', 'eu', 'nl'], chips = ['pt', 'nl'], hash = '', toggle = true} = {}) {
  const records = ids.map(id => node({id, open: false}));
  const button = toggle ? node({hidden: true}) : null;
  const links = chips.map(id => node({dataset: {recordLink: id}}));
  const other = node({id: 'theme-energy'});
  const byId = Object.fromEntries([...records, other].map(item => [item.id, item]));
  if (button) byId['mp-expand'] = button;
  const window = {...node(), location: {hash}};
  const document = {
    getElementById: id => byId[id] ?? null,
    querySelectorAll: selector => ({'.mp-record': records, '[data-record-link]': links})[selector] ?? [],
  };
  vm.runInNewContext(script, {document, window});
  // A <details> fires toggle when its open state changes; the fake does it on request.
  const setOpen = (record, open) => { record.open = open; record.fire('toggle'); };
  return {records, button, links, window, other, setOpen};
}

test('全部展开 shows only with JavaScript and opens or closes every record', () => {
  const {records, button} = page();
  assert.equal(button.hidden, false);
  assert.equal(button.textContent, '全部展开');
  assert.equal(button.attributes['aria-expanded'], 'false');
  button.fire('click');
  assert.deepEqual(records.map(record => record.open), [true, true, true]);
  assert.equal(button.textContent, '全部收起');
  assert.equal(button.attributes['aria-expanded'], 'true');
  button.fire('click');
  assert.deepEqual(records.map(record => record.open), [false, false, false]);
  assert.equal(button.textContent, '全部展开');
});

test('the label follows records opened one by one', () => {
  const {records, button, setOpen} = page({ids: ['pt', 'nl']});
  setOpen(records[0], true);
  assert.equal(button.textContent, '全部展开');
  setOpen(records[1], true);
  assert.equal(button.textContent, '全部收起');
  button.fire('click');
  assert.deepEqual(records.map(record => record.open), [false, false]);
});

test('a country chip and the URL hash open their record, and nothing else', () => {
  const {records, links, window, other} = page({hash: '#eu'});
  assert.deepEqual(records.map(record => record.open), [false, true, false]);
  links[1].fire('click');
  assert.equal(records[2].open, true);
  window.location.hash = '#theme-energy';
  window.fire('hashchange');
  assert.equal(other.open, undefined);
  window.location.hash = '#pt';
  window.fire('hashchange');
  assert.equal(records[0].open, true);
});

test('without records the script leaves the page alone', () => {
  const {button} = page({ids: [], chips: []});
  assert.equal(button.hidden, true);
});
