import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 产品档案 (tools/rtd_portal_assets/_static/product-profile.js): the source card's lines, loaded without a DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-profile.js', import.meta.url), 'utf8');
const sandbox = {};
sandbox.globalThis = sandbox;
vm.runInNewContext(script, sandbox);
const {sourceLines} = sandbox.ProductProfile;

test('market, language and edition date make one line', () => {
  const lines = sourceLines({market: '美规', language: 'English', date: '2026-01-02', printed: 'Weight: 10 kg'});
  assert.equal(lines.where, '美规 · English · 版本日期 2026-01-02');
  assert.equal(lines.printed, 'Weight: 10 kg');
});

test('a missing edition date leaves no empty label', () => {
  assert.equal(sourceLines({market: '日规', language: '日本語', date: ''}).where, '日规 · 日本語');
  assert.equal(sourceLines({}).printed, '');
});
