import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 产品库 (tools/rtd_portal_assets/_static/product-library.js): the filter logic, loaded without a DOM. A chip
// carries its model × market rows as a JSON array of [project, market] pairs.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-library.js', import.meta.url), 'utf8');
const sandbox = {};
sandbox.globalThis = sandbox;
vm.runInNewContext(script, sandbox);
const {chipState, chipRows, activeText} = sandbox.ProductLibrary;
// The data-rows text of a chip from "project|market" shorthand (test only).
const r = (...pairs) => JSON.stringify(pairs.map(pair => pair.split('|')));

test('no filter leaves every chip plain', () => {
  assert.equal(chipState({rows: r('P-FAKE-1|US', 'P-FAKE-1|EU')}, {project: '', market: ''}), '');
});

test('a project highlights its chips and dims the rest', () => {
  const filter = {project: 'P-FAKE-1', market: ''};
  assert.equal(chipState({rows: r('P-FAKE-1|US')}, filter), 'on');
  assert.equal(chipState({rows: r('P-FAKE-2|US')}, filter), 'off');
  assert.equal(chipState({rows: r('|US')}, filter), 'off');
});

test('未归入项目 matches the rows without a project', () => {
  const filter = {project: '-', market: ''};
  assert.equal(chipState({rows: r('|JP')}, filter), 'on');
  assert.equal(chipState({rows: r('P-FAKE-1|JP')}, filter), 'off');
});

test('a market matches any row sold there', () => {
  assert.equal(chipState({rows: r('P-FAKE-1|US', 'P-FAKE-1|EU')}, {project: '', market: 'EU'}), 'on');
  assert.equal(chipState({rows: r('P-FAKE-1|US')}, {project: '', market: 'EU'}), 'off');
  assert.equal(chipState({rows: r()}, {project: '', market: 'US'}), 'off');
});

test('project and market together must hold on one row', () => {
  // The model is in P-FAKE-1 in the US and in P-FAKE-2 in Japan.
  const chip = {rows: r('P-FAKE-1|US', 'P-FAKE-2|JP')};
  assert.equal(chipState(chip, {project: 'P-FAKE-1', market: 'US'}), 'on');
  assert.equal(chipState(chip, {project: 'P-FAKE-2', market: 'US'}), 'off');
  assert.equal(chipState(chip, {project: 'P-FAKE-2', market: ''}), 'on');
});

test('the active pill joins the chosen labels', () => {
  assert.equal(activeText(['P-FAKE-1', '日规']), 'P-FAKE-1 · 日规');
  assert.equal(activeText(['', '欧规']), '欧规');
});

test('the search matches codes, names and projects, and narrows the other filters', () => {
  const chip = {rows: r('P-FAKE-1|US'), search: 'fake station one fake-1 p-fake-1'};
  assert.equal(chipState(chip, {project: '', market: '', q: 'Station'}), 'on');
  assert.equal(chipState(chip, {project: '', market: '', q: 'p-fake-1'}), 'on');
  assert.equal(chipState(chip, {project: '', market: '', q: 'other'}), 'off');
  assert.equal(chipState(chip, {project: '', market: 'JP', q: 'fake'}), 'off');
  assert.equal(chipState(chip, {project: '', market: '', q: '  '}), '');
});

test('a project with a space or a bar stays one value', () => {
  const chip = {rows: JSON.stringify([['P FAKE|1', 'US'], ['', 'JP']])};
  assert.equal(chipState(chip, {project: 'P FAKE|1', market: 'US'}), 'on');
  assert.equal(chipState(chip, {project: 'P FAKE', market: ''}), 'off');
  assert.equal(chipState(chip, {project: '1', market: ''}), 'off');
  assert.equal(chipState(chip, {project: '-', market: 'JP'}), 'on');
  assert.deepEqual(JSON.parse(JSON.stringify(chipRows('not json'))), []);
  assert.deepEqual(JSON.parse(JSON.stringify(chipRows('{"a":1}'))), []);
});
