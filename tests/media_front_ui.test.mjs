import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 视觉媒体 (tools/rtd_portal_assets/_static/media-front.js): the filter and the moved anchors, loaded without a DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/media-front.js', import.meta.url), 'utf8');
const sandbox = {};
sandbox.globalThis = sandbox;
vm.runInNewContext(script, sandbox);
const {movedTarget, matches, usedText} = sandbox.MediaFront;

test('the old inventory anchors forward to 设计规范 › 图标与素材, others stay', () => {
  assert.equal(movedTarget('#registry'), '../../workspace/design/index.html#assets-inventory');
  assert.equal(movedTarget('#used-by'), '../../workspace/design/index.html#assets-inventory');
  assert.equal(movedTarget('#gallery'), '');
  assert.equal(movedTarget(''), '');
});

test('a type and every search word must match', () => {
  const tile = {type: 'symbols', search: '警告 通用符号'};
  assert.equal(matches(tile, {type: '', q: ''}), true);
  assert.equal(matches(tile, {type: 'symbols', q: '警告'}), true);
  assert.equal(matches(tile, {type: 'buttons', q: ''}), false);
  assert.equal(matches(tile, {type: '', q: '警告 按键'}), false);
  assert.equal(matches(tile, {type: '', q: '  '}), true);
});

test('use reads as manuals, nothing when unknown', () => {
  assert.equal(usedText(3), '用于 3 本说明书');
  assert.equal(usedText(0), '');
});
