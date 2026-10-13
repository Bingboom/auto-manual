import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-matrix.js', import.meta.url), 'utf8');
function load() {
  // No document: only the pure rules are set up.
  const context = {};
  vm.runInNewContext(script, context);
  return context.ProductMatrixModel;
}

test('a product is out only when a market is chosen and it has no Web manual there', () => {
  const {isOut} = load();
  assert.equal(isOut('US EU', ''), false);
  assert.equal(isOut('US EU', 'EU'), false);
  assert.equal(isOut('US EU', 'JP'), true);
  // A capability row without any Web manual dims for every market.
  assert.equal(isOut('', 'US'), true);
  assert.equal(isOut(undefined, ''), false);
});

test('numeric columns open largest first and a second click reverses', () => {
  const {nextSort} = load();
  assert.deepEqual({...nextSort({col: 2, dir: 1}, 3, true)}, {col: 3, dir: -1});
  assert.deepEqual({...nextSort({col: 3, dir: -1}, 3, true)}, {col: 3, dir: 1});
  assert.deepEqual({...nextSort({col: 2, dir: 1}, 0, false)}, {col: 0, dir: 1});
  assert.deepEqual({...nextSort({col: 2, dir: 1}, 2, true)}, {col: 2, dir: -1});
});

test('values compare as numbers or text in the chosen direction', () => {
  const {compare} = load();
  const rows = ['512', '96', '3584'];
  assert.deepEqual([...rows].sort((a, b) => compare(a, b, true, 1)), ['96', '512', '3584']);
  assert.deepEqual([...rows].sort((a, b) => compare(a, b, true, -1)), ['3584', '512', '96']);
  assert.deepEqual(['JE-B', 'JE-A'].sort((a, b) => compare(a, b, false, 1)), ['JE-A', 'JE-B']);
});
