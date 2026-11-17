import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 产品库 (tools/rtd_portal_assets/_static/product-library.js): the filter logic, loaded without a DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-library.js', import.meta.url), 'utf8');
const sandbox = {};
sandbox.globalThis = sandbox;
vm.runInNewContext(script, sandbox);
const {chipState, activeText} = sandbox.ProductLibrary;

test('no filter leaves every chip plain', () => {
  assert.equal(chipState({project: 'P-FAKE-1', markets: 'US EU'}, {project: '', market: ''}), '');
});

test('a project highlights its chips and dims the rest', () => {
  const filter = {project: 'P-FAKE-1', market: ''};
  assert.equal(chipState({project: 'P-FAKE-1', markets: 'US'}, filter), 'on');
  assert.equal(chipState({project: 'P-FAKE-2', markets: 'US'}, filter), 'off');
  assert.equal(chipState({project: '', markets: 'US'}, filter), 'off');
});

test('未归入项目 matches the chips without a project', () => {
  const filter = {project: '-', market: ''};
  assert.equal(chipState({project: '', markets: 'JP'}, filter), 'on');
  assert.equal(chipState({project: 'P-FAKE-1', markets: 'JP'}, filter), 'off');
});

test('a market matches any chip sold there, and both filters must match', () => {
  assert.equal(chipState({project: 'P-FAKE-1', markets: 'US EU'}, {project: '', market: 'EU'}), 'on');
  assert.equal(chipState({project: 'P-FAKE-1', markets: 'US'}, {project: '', market: 'EU'}), 'off');
  assert.equal(chipState({project: 'P-FAKE-1', markets: 'US'}, {project: 'P-FAKE-1', market: 'JP'}), 'off');
  assert.equal(chipState({project: 'P-FAKE-1', markets: ''}, {project: '', market: 'US'}), 'off');
});

test('the active pill joins the chosen labels', () => {
  assert.equal(activeText(['P-FAKE-1', '日规']), 'P-FAKE-1 · 日规');
  assert.equal(activeText(['', '欧规']), '欧规');
});
