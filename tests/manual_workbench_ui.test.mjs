import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/manual-workbench.js', import.meta.url), 'utf8');
function harness(missing = false) {
  const panels = Array.from({length: 4}, () => ({hidden: false}));
  const nodes = panels.map((_, index) => ({
    attrs: {'aria-controls': String(index), 'aria-pressed': 'false'},
    getAttribute(key) { return this.attrs[key]; },
    setAttribute(key, value) { this.attrs[key] = value; },
    addEventListener(key, callback) { this[key] = callback; },
  }));
  vm.runInNewContext(script, {document: {
    querySelectorAll: () => nodes,
    getElementById: (id) => missing && id === '2' ? null : panels[Number(id)],
  }});
  return {nodes, panels};
}

test('no panel is open until a work stage is chosen; it then reveals only its linked panel', () => {
  const {nodes, panels} = harness();
  assert.deepEqual(panels.map(p => p.hidden), [true, true, true, true]);
  assert.deepEqual(nodes.map(n => n.attrs['aria-pressed']), ['false', 'false', 'false', 'false']);
  nodes[2].click();
  assert.deepEqual(panels.map(p => p.hidden), [true, true, false, true]);
  assert.deepEqual(nodes.map(n => n.attrs['aria-pressed']), ['false', 'false', 'true', 'false']);
  nodes[0].click();
  assert.deepEqual(panels.map(p => p.hidden), [false, true, true, true]);
});

test('choosing the open work stage again closes its panel', () => {
  const {nodes, panels} = harness();
  nodes[1].click();
  nodes[1].click();
  assert.deepEqual(panels.map(p => p.hidden), [true, true, true, true]);
  assert.equal(nodes[1].attrs['aria-pressed'], 'false');
});

test('incomplete navigation falls back to visible links without hiding panels', () => {
  const {panels} = harness(true);
  assert.equal(panels.some(p => p.hidden), false);
});
