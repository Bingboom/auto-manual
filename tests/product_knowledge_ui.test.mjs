import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 产品知识 (tools/rtd_portal_assets/_static/product-knowledge.js) against a minimal fake DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-knowledge.js', import.meta.url), 'utf8');

function classes(...names) {
  const set = new Set(names);
  return {
    contains: (name) => set.has(name),
    add: (name) => { set.add(name); },
    toggle: (name, force = !set.has(name)) => { if (force) set.add(name); else set.delete(name); return force; },
  };
}

function node(props = {}) {
  const listeners = {};
  return {
    hidden: false, textContent: '', dataset: {}, attributes: {}, classList: classes(),
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(name, callback) { listeners[name] = callback; },
    fire(name) { listeners[name](); },
    ...props,
  };
}

// Like a DOM <select>: options may share a value (UK and EU both bind EU); selectedIndex picks one of them.
function select(value, options) {
  const element = node({value, options});
  let picked = null;
  Object.defineProperty(element, 'selectedIndex', {set: (index) => { picked = options[index]; element.value = picked.value; }});
  Object.defineProperty(element, 'selectedOptions', {get: () => (picked && picked.value === element.value
    ? [picked] : options.filter((option) => option.value === element.value).slice(0, 1))});
  return element;
}

const REGION_KEY = 'hello-docs.manual-portal.region';
const ALL_KEY = 'hello-docs.manual-portal.region-all';
function memory(entries = []) {
  const map = new Map(entries);
  return {map, getItem: (key) => map.get(key) ?? null, setItem: (key, value) => { map.set(key, String(value)); },
    removeItem: (key) => { map.delete(key); }};
}

// A topic card with its manual links ([region, model] pairs), its "+N" button and its manual count.
function card(id, tags, refs) {
  const links = refs.map(([region, model]) => node({dataset: {region, model}}));
  const more = node({hidden: true});
  const count = node();
  const element = node({
    id, dataset: {tags: tags.join(' '), models: [...new Set(refs.map(([, model]) => model))].join(' ')},
    querySelectorAll: (selector) => (selector === '.pk-ref' ? links : []),
    querySelector: (selector) => ({'.pk-more': more, '.reference-count': count})[selector] ?? null,
  });
  more.closest = (selector) => (selector === '.pk-card' ? element : null);
  return {element, links, more, count};
}

function page({cards, region = 'EU', chips = ['all', 'battery', 'inverter'], flow = [], themes = [], topicLinks = [], storage}) {
  const regions = select(region, [{value: 'EU', textContent: 'EU'}, {value: 'EU', textContent: 'UK'}, {value: 'US', textContent: 'US'},
    {value: 'all', textContent: '全部区域'}]);
  const products = select('all', [['all'], ['JE-1000F', 'EU'], ['JS-100I', 'EU'], ['JE-1000F', 'US'], ['JHP-3600C', 'US']]
    .map(([value, regionCode]) => ({value, dataset: regionCode ? {region: regionCode} : {}, hidden: false, disabled: false})));
  const list = node({scrolled: 0, scrollIntoView() { this.scrolled += 1; }});
  const parts = {regions, products, list, count: node(), empty: node({hidden: true}), reset: node(),
    chips: chips.map((tag) => node({dataset: {tag}})), flow: flow.map((tag) => node({dataset: {flowTag: tag}})),
    themes: themes.map((tag) => node({dataset: {theme: tag}})), links: topicLinks.map((id) => node({dataset: {topicLink: id}}))};
  const byId = {'learning-region': regions, 'learning-product': products, 'knowledge-list': list, 'learning-count': parts.count,
    'learning-empty': parts.empty, 'learning-reset': parts.reset};
  cards.forEach((item) => { byId[item.element.id] = item.element; });
  const document = {
    getElementById: (id) => byId[id] ?? null,
    querySelectorAll: (selector) => ({
      '.pk-card': cards.map((item) => item.element),
      '.pk-chips [data-tag]': parts.chips,
      '[data-flow-tag], [data-theme]': [...parts.flow, ...parts.themes],
      '[data-topic-link]': parts.links,
      '.pk-more': cards.map((item) => item.more),
    })[selector] ?? [],
  };
  vm.runInNewContext(script, storage ? {document, localStorage: storage} : {document});
  return parts;
}

test('a region shows only its manuals, counts them and drops a card left with none', () => {
  const watts = card('watts', ['basics'], [['EU', 'JE-1000F'], ['US', 'JE-1000F']]);
  const split = card('split-phase', ['basics'], [['US', 'JHP-3600C']]);
  const {regions, products, list, count, empty} = page({cards: [watts, split]});
  assert.deepEqual(watts.links.map((link) => link.hidden), [false, true]);
  assert.equal(watts.count.textContent, '1');
  assert.equal(split.element.hidden, true);
  assert.equal(count.textContent, '1 项知识 · EU');
  assert.equal(list.classList.contains('pk-one-region'), true);
  assert.deepEqual(products.options.map((option) => option.disabled), [false, false, false, true, true]);
  assert.equal(empty.hidden, true);

  regions.value = 'all';
  regions.fire('change');
  assert.equal(split.element.hidden, false);
  assert.equal(watts.count.textContent, '2');
  assert.equal(count.textContent, '2 项知识');
  assert.equal(list.classList.contains('pk-one-region'), false);
});

test('a card shows its first eight manuals until +N is pressed', () => {
  const many = card('watt-hours', ['basics'], Array.from({length: 11}, () => ['EU', 'JE-1000F']));
  const {regions} = page({cards: [many]});
  assert.deepEqual(many.links.map((link) => link.classList.contains('is-extra')), [...Array(8).fill(false), true, true, true]);
  assert.equal(many.more.hidden, false);
  assert.equal(many.more.textContent, '+3');
  assert.equal(many.count.textContent, '11');

  many.more.fire('click');
  assert.equal(many.element.classList.contains('is-open'), true);
  assert.equal(many.more.hidden, true);
  regions.fire('change');
  assert.equal(many.more.hidden, true, 'an opened card stays open when the filters change');
});

test('an energy-flow node or a theme head sets the theme and brings the list into view', () => {
  const battery = card('bms', ['battery'], [['EU', 'JE-1000F']]);
  const inverter = card('inverter', ['inverter'], [['EU', 'JE-1000F']]);
  const {chips, flow, themes, list} = page({cards: [battery, inverter], flow: ['battery'], themes: ['inverter']});
  flow[0].fire('click');
  assert.deepEqual([battery.element.hidden, inverter.element.hidden], [false, true]);
  assert.deepEqual(chips.map((chip) => chip.attributes['aria-pressed']), ['false', 'true', 'false']);
  assert.equal(chips[1].classList.contains('selected'), true);
  assert.equal(list.scrolled, 1);

  themes[0].fire('click');
  assert.deepEqual([battery.element.hidden, inverter.element.hidden], [true, false]);
  assert.equal(list.scrolled, 2);
});

test('a topic link clears the filters that hide its card, the region last', () => {
  const battery = card('bms', ['battery'], [['EU', 'JE-1000F']]);
  const backup = card('ups', ['backup'], [['US', 'JHP-3600C']]);
  const {chips, regions, links} = page({cards: [battery, backup], chips: ['all', 'battery'], topicLinks: ['bms', 'ups']});
  chips[1].fire('click');
  links[0].fire('click');
  assert.equal(chips[1].attributes['aria-pressed'], 'true', 'a visible card keeps the filters');

  links[1].fire('click');
  assert.equal(chips[0].attributes['aria-pressed'], 'true');
  assert.equal(regions.value, 'all');
  assert.equal(backup.element.hidden, false);
});

test('an empty selection offers a reset that clears the theme and the product', () => {
  const battery = card('bms', ['battery'], [['EU', 'JE-1000F']]);
  const {products, empty, count, reset, chips} = page({cards: [battery]});
  products.value = 'JS-100I';
  products.fire('change');
  assert.equal(battery.element.hidden, true);
  assert.equal(empty.hidden, false);
  assert.equal(count.textContent, '0 项知识 · EU');

  chips[2].fire('click');
  reset.fire('click');
  assert.equal(products.value, 'all');
  assert.equal(chips[0].attributes['aria-pressed'], 'true');
  assert.equal(battery.element.hidden, false);
  assert.equal(empty.hidden, true);
});

test('a region picked on either page opens here next time, by its name', () => {
  const watts = card('watts', ['basics'], [['EU', 'JE-1000F'], ['US', 'JE-1000F']]);
  const us = page({cards: [watts], storage: memory([[REGION_KEY, 'US']])});
  assert.equal(us.regions.value, 'US');
  assert.equal(us.count.textContent, '1 项知识 · US');
  assert.deepEqual(watts.links.map((link) => link.hidden), [true, false]);

  const uk = page({cards: [watts], storage: memory([[REGION_KEY, 'UK']])});
  assert.equal(uk.regions.value, 'EU');
  assert.equal(uk.count.textContent, '1 项知识 · UK', 'UK keeps its name while showing the shared EU manuals');
});

test('a stored name that is not an option keeps the configured default', () => {
  const watts = card('watts', ['basics'], [['EU', 'JE-1000F']]);
  const {regions, count} = page({cards: [watts], storage: memory([[REGION_KEY, 'XX']])});
  assert.equal(regions.value, 'EU');
  assert.equal(count.textContent, '1 项知识 · EU');
});

test('全部区域 is remembered here until a region is picked again', () => {
  const watts = card('watts', ['basics'], [['EU', 'JE-1000F'], ['US', 'JE-1000F']]);
  const storage = memory([[REGION_KEY, 'US']]);
  const first = page({cards: [watts], storage});
  first.regions.value = 'all';
  first.regions.fire('change');
  assert.equal(storage.map.get(ALL_KEY), '1');
  assert.equal(storage.map.get(REGION_KEY), 'US', 'the shared region stays for the manual library');

  const second = page({cards: [watts], storage});
  assert.equal(second.regions.value, 'all');
  assert.equal(second.count.textContent, '1 项知识');
  assert.equal(watts.count.textContent, '2', 'both regions\' manuals show');
  second.regions.selectedIndex = 1;
  second.regions.fire('change');
  assert.equal(storage.map.get(REGION_KEY), 'UK');
  assert.equal(storage.map.has(ALL_KEY), false);
});
