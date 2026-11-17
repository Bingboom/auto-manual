import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 产品档案 (tools/rtd_portal_assets/_static/product-profile.js): the source card's title, loaded without a DOM.
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
