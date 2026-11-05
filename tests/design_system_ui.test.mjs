import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/design-system.js', import.meta.url), 'utf8');

function frame({bottom = 120, margin = '8px', scrollY = 0, hidden = false, crossOrigin = false} = {}) {
  const listeners = {};
  const main = {getBoundingClientRect: () => ({bottom})};
  const doc = {
    querySelector: (selector) => (selector === 'main' ? main : null),
    defaultView: {scrollY, getComputedStyle: () => ({marginBottom: margin})},
  };
  const element = {
    style: {},
    offsetParent: hidden ? null : {},
    addEventListener: (name, callback) => { listeners[name] = callback; },
    fire: (name) => listeners[name](),
  };
  Object.defineProperty(element, 'contentDocument', {
    get() { if (crossOrigin) throw new Error('blocked'); return doc; },
  });
  return element;
}

function run(frames, withObserver = true) {
  const observed = [];
  const window = withObserver ? {ResizeObserver: class { observe(target) { observed.push(target); } }} : {};
  const context = {
    window, ResizeObserver: window.ResizeObserver,
    document: {querySelectorAll: (selector) => (selector === 'iframe.ds-preview' ? frames : [])},
  };
  vm.runInNewContext(script, context);
  frames.forEach((item) => item.fire('load'));
  return observed;
}

test('a loaded preview is sized to the bottom of its main element', () => {
  const preview = frame({bottom: 120.2, margin: '8px', scrollY: 4});
  const observed = run([preview]);
  assert.equal(preview.style.height, '133px');
  assert.equal(observed.length, 1);
});

test('a hidden or cross-origin preview keeps its declared height', () => {
  const hidden = frame({hidden: true});
  const foreign = frame({crossOrigin: true});
  run([hidden, foreign], false);
  assert.equal(hidden.style.height, undefined);
  assert.equal(foreign.style.height, undefined);
});

test('a gallery card scales its preview from the 720px layout width; a hidden card waits for its size', () => {
  const set = [];
  const box = (clientWidth) => ({clientWidth, style: {setProperty: (name, value) => set.push([clientWidth, name, value])}});
  const observed = [];
  const window = {ResizeObserver: class { observe(target) { observed.push(target); } }};
  const boxes = [box(360), box(0), box(900)];
  vm.runInNewContext(script, {
    window, ResizeObserver: window.ResizeObserver,
    document: {querySelectorAll: (selector) => (selector === '.ds-shot-frame' ? boxes : [])},
  });
  assert.deepEqual(set, [[360, '--ds-shot-scale', '0.5'], [900, '--ds-shot-scale', '1']]);
  assert.equal(observed.length, 3);
});
