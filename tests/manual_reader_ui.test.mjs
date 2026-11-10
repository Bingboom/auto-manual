import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// The reading frame around a verified manual (tools/rtd_portal_assets/_static/manual-reader.js) and its feedback
// card (manual-feedback.js), against a small fake DOM: a selector matcher for tag, #id, .class, [attr] and
// [attr^="v"], comma lists and the descendant combinator, which is all the scripts ask of the page.
const reader = readFileSync(new URL('../tools/rtd_portal_assets/_static/manual-reader.js', import.meta.url), 'utf8');
const feedback = readFileSync(new URL('../tools/rtd_portal_assets/_static/manual-feedback.js', import.meta.url), 'utf8');

function matcher(part) {
  const tag = (part.match(/^[a-z]+/) || [])[0];
  const id = (part.match(/#([\w-]+)/) || [])[1];
  const names = [...part.matchAll(/\.([\w-]+)/g)].map((m) => m[1]);
  const attrs = [...part.matchAll(/\[([\w-]+)(?:\^="([^"]*)")?\]/g)].map((m) => [m[1], m[2]]);
  return (node) => (!tag || node.tag === tag) && (!id || node.id === id)
    && names.every((name) => node.classList.contains(name))
    && attrs.every(([name, prefix]) => name in node.attributes && (prefix === undefined || node.attributes[name].startsWith(prefix)));
}
const chains = (selector) => selector.split(',').map((one) => one.trim().split(/\s+/).map(matcher));
function matches(node, chain) {
  if (!chain[chain.length - 1](node)) return false;
  let index = chain.length - 2;
  for (let up = node.parent; up && index >= 0; up = up.parent) if (chain[index](up)) index -= 1;
  return index < 0;
}
class Node {
  constructor(tag, {id = '', cls = '', attrs = {}, text = '', top = 0, height = 20} = {}) {
    Object.assign(this, {tag, id, attributes: {...attrs}, textContent: text, children: [], parent: null, listeners: {},
      hidden: false, open: false, top, height, scrollTop: 0, focused: false, scrolledIntoView: 0,
      style: {props: {}, setProperty(name, value) { this.props[name] = value; }}});
    const set = new Set(cls.split(' ').filter(Boolean));
    this.classList = {contains: (n) => set.has(n), toggle: (n, on = !set.has(n)) => (on ? set.add(n) : set.delete(n)),
      add: (n) => set.add(n), remove: (n) => set.delete(n)};
  }
  add(...kids) { kids.forEach((kid) => { kid.parent = this; this.children.push(kid); }); return this; }
  * walk() { for (const kid of this.children) { yield kid; yield* kid.walk(); } }
  querySelectorAll(selector) { const all = chains(selector); return [...this.walk()].filter((n) => all.some((c) => matches(n, c))); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  closest(selector) {
    const all = chains(selector);
    for (let node = this; node; node = node.parent) if (all.some((c) => matches(node, c))) return node;
    return null;
  }
  contains(other) { for (let node = other; node; node = node.parent) if (node === this) return true; return false; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }
  removeAttribute(name) { delete this.attributes[name]; }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  removeEventListener(name, callback) { this.listeners[name] = (this.listeners[name] || []).filter((c) => c !== callback); }
  fire(name, event = {}) { (this.listeners[name] || []).slice().forEach((callback) => callback({target: this, ...event})); }
  focus() { this.focused = true; }
  scrollIntoView() { this.scrolledIntoView += 1; }
  getBoundingClientRect() { return {top: this.top, bottom: this.top + this.height, height: this.height}; }
}
function eventTarget() {
  const listeners = {};
  return {listeners, addEventListener(name, callback) { (listeners[name] ||= []).push(callback); },
    removeEventListener(name, callback) { listeners[name] = (listeners[name] || []).filter((c) => c !== callback); },
    fire(name, event = {}) { (listeners[name] || []).slice().forEach((callback) => callback(event)); }};
}

// One manual: SAFETY, CHARGING (two sections), SPECS; tops are viewport positions the tests move.
function readerPage({hash = '', scrollHeight = 5000, innerHeight = 800, scrollY = 0} = {}) {
  const options = [new Node('option', {attrs: {value: 'manual_en.html'}}), new Node('option', {attrs: {value: '../../fr/md/manual_fr.html'}}),
    new Node('option', {attrs: {value: ''}})];
  options.forEach((option) => { option.value = option.attributes.value; option.disabled = false; });
  const select = new Node('select', {id: 'manual-locale-select', attrs: {'data-manual-locale': ''}}).add(...options);
  select.selectedOptions = [options[0]];
  const opener = new Node('button', {cls: 'mr-toc-open', attrs: {'aria-expanded': 'false'}});
  const bar = new Node('header', {cls: 'mr-top', top: 0, height: 60}).add(select, opener);
  const link = (href, text) => new Node('a', {attrs: {href}, text});
  const chapter = (href, text, subs = []) => new Node('li', {cls: 'mr-chapter'})
    .add(link(href, text), ...(subs.length ? [new Node('ul').add(...subs.map(([h, t]) => new Node('li').add(link(h, t))))] : []));
  const list = new Node('ol', {cls: 'mr-toc-list'}).add(
    chapter('#safety', 'SAFETY'),
    chapter('#charging', 'CHARGING', [['#via-ac', 'VIA AC'], ['#via-solar', 'VIA SOLAR']]),
    chapter('#specs', 'SPECS'),
  );
  const closer = new Node('button', {cls: 'mr-toc-close'});
  const toc = new Node('nav', {id: 'mr-toc', cls: 'mr-toc', top: 84, height: 400}).add(new Node('div').add(closer), list);
  const scrim = new Node('div', {cls: 'mr-scrim'});
  scrim.hidden = true;
  const sections = Object.fromEntries(['safety', 'charging', 'via-ac', 'via-solar', 'specs'].map((id, n) => [id, new Node('section', {id, top: 300 + n * 600})]));
  const article = new Node('article', {id: 'furo-main-content'}).add(...Object.values(sections));
  const root = new Node('div', {cls: 'mr'}).add(bar, toc, scrim, article);
  const body = new Node('body').add(root);
  const ids = (id) => [...body.walk()].find((node) => node.id === id) || null;
  const doc = eventTarget();
  Object.assign(doc, {getElementById: ids, querySelectorAll: (s) => body.querySelectorAll(s), querySelector: (s) => body.querySelector(s),
    documentElement: {scrollHeight}, activeElement: null});
  const win = eventTarget();
  const assigned = [];
  const location = {hash, assign: (url) => assigned.push(url)};
  const timers = [];
  Object.assign(win, {innerHeight, scrollY, location, requestAnimationFrame: (cb) => cb(), setTimeout: (cb) => timers.push(cb)});
  vm.runInNewContext(reader, {window: win, document: doc, location});
  const current = () => list.querySelectorAll('a').filter((a) => a.getAttribute('aria-current')).map((a) => a.textContent);
  const chapterOn = () => list.querySelectorAll('.mr-chapter').filter((li) => li.classList.contains('is-current')).map((li) => li.children[0].textContent);
  return {select, options, assigned, opener, bar, root, toc, list, closer, scrim, sections, doc, win, location, timers, current,
    chapterOn};
}

test('a language select opens the chosen publication, never a disabled or empty option', () => {
  const view = readerPage();
  view.select.selectedOptions = [view.options[1]];
  view.select.fire('change');
  view.select.selectedOptions = [view.options[2]];
  view.select.fire('change');
  view.options[1].disabled = true;
  view.select.selectedOptions = [view.options[1]];
  view.select.fire('change');
  assert.deepEqual(view.assigned, ['../../fr/md/manual_fr.html']);
});

test('the chapter sheet opens from 目录 and closes from the scrim, ×, Escape or a chapter', () => {
  const view = readerPage();
  view.opener.fire('click');
  assert.ok(view.toc.classList.contains('is-open'));
  assert.equal(view.opener.getAttribute('aria-expanded'), 'true');
  assert.equal(view.scrim.hidden, false);
  assert.ok(view.list.querySelector('a[aria-current]').focused);
  view.scrim.fire('click');
  assert.ok(!view.toc.classList.contains('is-open'));
  assert.equal(view.scrim.hidden, true);
  for (const close of [() => view.closer.fire('click'), () => view.doc.fire('keydown', {key: 'Escape'}),
    () => view.list.querySelectorAll('a')[2].fire('click')]) {
    view.opener.fire('click');
    close();
    assert.ok(!view.toc.classList.contains('is-open'));
    assert.equal(view.opener.getAttribute('aria-expanded'), 'false');
  }
});

test('the current section is the last heading under the top bar; the first chapter leads, the page end takes the last in view', () => {
  const view = readerPage();
  assert.deepEqual(view.current(), ['SAFETY']);  // nothing passed yet: the first chapter
  const scrollTo = (offset) => {
    Object.entries(view.sections).forEach(([id, node], n) => { node.top = 300 + n * 600 - offset; });
    view.win.fire('scroll');
  };
  scrollTo(950);  // via-ac at 1500-950 = 550; charging at 900-950 = -50 has passed the line (84)
  assert.deepEqual(view.current(), ['CHARGING']);
  assert.deepEqual(view.chapterOn(), ['CHARGING']);
  scrollTo(1500);  // via-ac at 0
  assert.deepEqual(view.current(), ['VIA AC']);
  assert.deepEqual(view.chapterOn(), ['CHARGING']);
  view.win.scrollY = 4200;  // the page's end: 4200 + 800 >= 5000
  scrollTo(2000);  // specs at 2700-2000 = 700 is in view, below the line
  assert.deepEqual(view.current(), ['SPECS']);
  assert.deepEqual(view.chapterOn(), ['SPECS']);
});

test('the list keeps the current entry in view', () => {
  const view = readerPage();
  const specs = view.list.querySelectorAll('a').find((a) => a.textContent === 'SPECS');
  specs.top = 900;  // below the list's box (84..484)
  Object.entries(view.sections).forEach(([, node]) => { node.top -= 3000; });
  view.win.fire('scroll');
  assert.deepEqual(view.current(), ['SPECS']);
  assert.ok(view.toc.scrollTop > 0);
});

test('the frame takes the top bar\'s real height, which a long product name can wrap', () => {
  const view = readerPage();
  assert.equal(view.root.style.props['--mr-top'], '60px');
  view.bar.height = 85.5;  // the name wrapped to two lines
  view.win.fire('resize');
  assert.equal(view.root.style.props['--mr-top'], '86px');
});

test('a jump keeps its section in place while images load, until the reader scrolls', () => {
  const view = readerPage({hash: '#charging'});
  const charging = view.sections.charging;
  view.doc.fire('load', {target: {tagName: 'IMG'}});
  view.doc.fire('load', {target: {tagName: 'SCRIPT'}});
  assert.equal(charging.scrolledIntoView, 1);
  view.win.fire('wheel');
  view.doc.fire('load', {target: {tagName: 'IMG'}});
  assert.equal(charging.scrolledIntoView, 1);
  view.location.hash = '#nowhere';
  view.win.fire('hashchange');
  view.doc.fire('load', {target: {tagName: 'IMG'}});
  assert.equal(charging.scrolledIntoView, 1);
});

function feedbackCard(clipboard) {
  const button = new Node('button', {attrs: {'data-copy-feedback': ''}});
  const context = new Node('pre', {cls: 'manual-feedback-context', text: 'Model: JE-TEST'});
  const details = new Node('details', {cls: 'manual-feedback-details'}).add(context);
  const status = new Node('span', {cls: 'manual-feedback-status'});
  const card = new Node('aside', {cls: 'manual-feedback', attrs: {'data-copied': 'コピーしました。', 'data-copy-failed': '自動でコピーできませんでした。'}})
    .add(new Node('div').add(button), details, status);
  vm.runInNewContext(feedback, {document: {querySelectorAll: (s) => card.querySelectorAll(s)}, navigator: {clipboard}});
  return {button, details, status};
}

test('feedback copies its folded context, and unfolds it when copying is unavailable; the card gives its messages', async () => {
  const copied = [];
  const ok = feedbackCard({writeText: async (text) => { copied.push(text); }});
  ok.button.fire('click');
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(copied, ['Model: JE-TEST']);
  assert.equal(ok.details.open, false);
  assert.equal(ok.status.textContent, 'コピーしました。');
  const refused = feedbackCard({writeText: async () => { throw new Error('denied'); }});
  refused.button.fire('click');
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(refused.details.open, true);
  assert.equal(refused.status.textContent, '自動でコピーできませんでした。');
});
