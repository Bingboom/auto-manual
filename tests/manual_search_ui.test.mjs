import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// 搜索说明书正文 (tools/rtd_portal_assets/_static/manual-search.js): the pure ManualSearch functions on a small index,
// then the page wiring against a minimal fake DOM.
const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/manual-search.js', import.meta.url), 'utf8');

const row = (model, short, name, region, lang, title, text, anchor) => ({
  model, short_name: short, name, region, lang, title, text, url: `${model}/${region}/${lang}/m.html#${anchor}`,
});
const ROWS = [
  row('JE-5000A', 'E5000Plus', 'Explorer 5000 Plus', 'US', 'en', 'ONLINE UPS', 'The online UPS mode switches in 0 ms. UPS UPS', 'online'),
  row('JE-5000A', 'E5000Plus', 'Explorer 5000 Plus', 'US', 'en', 'SAFETY', 'Do not place the unit upside down.', 'safety'),
  row('JE-5000A', 'E5000Plus', 'ポータブル電源 5000 Plus · JE-5000A', 'JP', 'ja', 'UPS機能', 'UPS（無停電電源装置）は電源を切り替えます。', 'ups'),
  row('JE-1000F', 'E1000V2', 'Explorer 1000', 'EU', 'en', 'LCD', 'UPS On: bypass mode. Charging the battery.', 'lcd'),
  row('JE-1000F', 'E1000V2', 'Explorer 1000', 'EU', 'fr', 'ÉCRAN', 'UPS activé.', 'lcd'),
  row('JE-1000F', 'E1000V2', 'Explorer 1000', 'EU', 'de', 'ANZEIGE', 'UPS an.', 'lcd'),
  row('JS-100F', '100W', 'SolarSaga 100', 'US', 'en', 'Specifications', 'IP65 rated. Parallel connection.', 'spec'),
  row('JE-1000D', '', '便携储能电源', 'CN', 'zh', '并机模式', '两台并机。', 'bj'),
];
const CONFIG = {
  regions: ['US', 'EU', 'CN', 'JP'], categories: {portable: '便携电源', solar: '太阳能板'},
  models: {'JE-5000A': {category: 'portable', series: 'Plus'}, 'JE-1000F': {category: 'portable', series: '标准'},
           'JS-100F': {category: 'solar', series: 'SolarSaga'}, 'JE-1000D': {category: 'portable', series: '标准'}},
  languages: [['en', 'en-US'], ['fr', 'fr-FR'], ['de', 'de-DE'], ['zh', 'zh-CN'], ['ja', 'ja-JP']], legacy: '语言待确认',
};
const ALL = {region: 'all', cat: 'all', lang: 'all'};

function load(context = {}) {
  const sandbox = {URLSearchParams, setTimeout, clearTimeout, console, ...context};
  vm.runInNewContext(script, sandbox);
  return sandbox;
}
const S = load().ManualSearch;
const rows = S.prepare(ROWS, CONFIG);
// Values made inside the vm context have its Array and Object prototypes; compare plain copies.
const plain = value => JSON.parse(JSON.stringify(value));
const anchors = hits => plain(hits.map(hit => hit.row.url.split('#')[1]));

test('UPS matches the whole word, so it finds UPS機能 but not upside', () => {
  const found = anchors(S.search(rows, 'ups').hits);
  assert.deepEqual(found.sort(), ['lcd', 'lcd', 'lcd', 'online', 'ups']);
});

test('a token no section has as a whole word matches word beginnings; Chinese matches as written', () => {
  assert.deepEqual(anchors(S.search(rows, 'upsi').hits), ['safety']);
  assert.deepEqual(anchors(S.search(rows, 'charg').hits), ['lcd']);
  assert.deepEqual(anchors(S.search(rows, '并机').hits), ['bj']);
  assert.equal(S.search(rows, '   ').hits.length, 0);
});

test('every token must match; the product words count most, then the section title', () => {
  const hits = S.search(rows, 'E1000V2 ups').hits;
  assert.deepEqual(plain(hits.map(hit => hit.row.lang)), ['en', 'fr', 'de']);
  assert.ok(hits.every(hit => hit.score > 100));
  const ups = S.search(rows, 'ups').hits;
  const score = anchor => ups.find(hit => hit.row.url.endsWith(`#${anchor}`)).score;
  assert.ok(score('online') > score('lcd'));
});

test('results group by product, then by market, each manual in its English edition when it has one', () => {
  const grouped = S.group(S.search(rows, 'ups').hits, ALL, CONFIG);
  assert.equal(grouped.manuals, 3);
  assert.deepEqual(plain(grouped.products.map(item => item.model)), ['JE-5000A', 'JE-1000F']);
  const [plus, explorer] = grouped.products;
  assert.deepEqual(plain(plus.markets.map(item => [item.region, item.lang])), [['US', 'en'], ['JP', 'ja']]);
  assert.equal(plus.name, 'Explorer 5000 Plus');
  assert.deepEqual([plus.category, plus.series, plus.short], ['portable', 'Plus', 'E5000Plus']);
  assert.equal(plus.markets[0].url, 'JE-5000A/US/en/m.html');
  assert.deepEqual(plain(explorer.markets[0].others.map(item => [item.lang, item.count])), [['fr', 1], ['de', 1]]);
  assert.equal(grouped.sections, 3);
  // A language filter shows that edition only.
  const french = S.group(S.search(rows, 'ups').hits, {...ALL, lang: 'fr'}, CONFIG);
  assert.deepEqual(plain(french.products.map(item => [item.model, item.markets[0].lang, item.markets[0].others.length])),
                   [['JE-1000F', 'fr', 0]]);
});

test('each filter counts manuals under the other two filters', () => {
  const counts = S.facets(S.search(rows, 'ups').hits, {...ALL, region: 'JP'});
  assert.deepEqual({...counts.region}, {all: 3, US: 1, JP: 1, EU: 1});
  assert.deepEqual({...counts.cat}, {all: 1, portable: 1});
  assert.deepEqual({...counts.lang}, {all: 1, ja: 1});
});

test('snippets centre on the first match and mark whole words only', () => {
  const matchers = S.search(rows, 'ups').matchers;
  const marked = S.pieces('Do not place the unit upside down. UPS on', matchers).filter(([, mark]) => mark);
  assert.deepEqual(plain(marked.map(([text]) => text)), ['UPS']);
  const long = `${'word '.repeat(60)}the UPS switch ${'more '.repeat(60)}`;
  const part = S.snippet(long, matchers);
  assert.ok(part.lead && part.trail && part.text.includes('UPS'));
  assert.ok(!part.text.startsWith('ord'), part.text);
});

test('the query and filters round-trip through the URL; unknown values fall back to all', () => {
  assert.deepEqual({...S.readState('?q=UPS&region=JP&cat=nope&lang=fr', CONFIG)},
                   {q: 'UPS', region: 'JP', cat: 'all', lang: 'fr'});
  assert.equal(S.writeState({q: ' UPS ', region: 'JP', cat: 'all', lang: 'fr'}), '?q=UPS&region=JP&lang=fr');
  assert.equal(S.writeState({q: ' ', ...ALL}), '');
});

test('coverage counts manuals per region and language editions per language, in the configured order', () => {
  const cover = S.coverage(rows, CONFIG);
  assert.deepEqual([cover.manuals, cover.products, cover.editions, cover.sections], [5, 4, 7, 8]);
  assert.deepEqual(plain(cover.regions), [['US', 2], ['EU', 1], ['CN', 1], ['JP', 1]]);
  assert.deepEqual(plain(cover.languages), [['en', 3], ['fr', 1], ['de', 1], ['zh', 1], ['ja', 1]]);
  assert.deepEqual(plain(S.languagesOf(rows, 'EU')), ['en', 'fr', 'de']);
});

// --- the page --------------------------------------------------------------------------------------------------
function classes() {
  const set = new Set();
  return {add: name => set.add(name), remove: name => set.delete(name), contains: name => set.has(name),
          toggle: (name, on) => ((on ?? !set.has(name)) ? set.add(name) : set.delete(name))};
}
class Element {
  constructor(tag, props = {}) {
    Object.assign(this, {tagName: tag.toUpperCase(), children: [], hidden: false, dataset: {}, attributes: {},
                         listeners: {}, className: '', classList: classes()}, props);
  }
  // Like the DOM: setting textContent leaves one text node, which later appends follow.
  get textContent() { return this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.children = String(value) ? [{textContent: String(value)}] : []; }
  append(...nodes) { nodes.forEach(node => this.children.push(typeof node === 'string' ? {textContent: node} : node)); }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return name in this.attributes ? this.attributes[name] : null; }
  addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); }
  fire(type) { (this.listeners[type] || []).forEach(callback => callback({preventDefault() {}})); }
  querySelector(selector) { return this.children.find(child => child.tagName === selector.toUpperCase()) || null; }
  focus() {}
}
const labelled = (attributes, label) => {
  const node = new Element('button', attributes);
  node.append(label, new Element('b'));
  return node;
};

function page({query = '', index = ROWS} = {}) {
  const ids = ['ms-query', 'ms-status', 'ms-clear', 'ms-form', 'ms-filters', 'ms-start', 'ms-stats', 'ms-cover-regions',
               'ms-cover-langs', 'ms-summary', 'ms-summary-text', 'ms-summary-note', 'search-results', 'ms-more', 'ms-none',
               'ms-none-title', 'ms-none-elsewhere', 'ms-reset', 'ms-none-hint'];
  const nodes = Object.fromEntries(ids.map(id => [id, new Element('div', {id})]));
  nodes['ms-config'] = new Element('script');
  nodes['ms-config'].textContent = JSON.stringify(CONFIG);
  nodes['ms-query'].value = '';
  const select = new Element('select', {value: 'all'});
  select.options = ['all', 'en', 'fr', 'de', 'zh', 'ja', 'legacy'].map(value => new Element('option', {value, disabled: false}));
  nodes['ms-lang'] = select;
  const regions = ['all', ...CONFIG.regions].map(region => labelled({dataset: {region}}, region));
  const cats = Object.keys(CONFIG.categories).map(cat => labelled({dataset: {cat}}, CONFIG.categories[cat]));
  const examples = ['ups', 'zzz'].map(q => labelled({dataset: {q}}, q));
  const replaced = [];
  const document = {
    getElementById: id => nodes[id] || null,
    querySelectorAll: selector => ({'[data-region]': regions, '[data-cat]': cats, '[data-q]': examples}[selector] || []),
    createElement: tag => new Element(tag),
    createTextNode: text => ({textContent: text}),
  };
  const window = {manualSearchIndex: index, location: {search: query, pathname: '/search.html'},
                  history: {replaceState: (state, title, url) => replaced.push(url)}};
  load({document, window});
  const count = button => button.querySelector('b').textContent;
  return {nodes, regions, cats, examples, replaced, count};
}

test('a query in the URL renders products, counts and the summary', () => {
  const view = page({query: '?q=ups'});
  assert.equal(view.nodes['ms-status'].hidden, true);
  assert.equal(view.nodes['ms-start'].hidden, true);
  assert.equal(view.nodes['ms-query'].value, 'ups');
  const cards = view.nodes['search-results'].children;
  assert.deepEqual(cards.map(card => card.className), ['ms-prod', 'ms-prod']);
  assert.match(cards[0].textContent, /^JE-5000AE5000PlusExplorer 5000 Plus便携电源 · Plus2 份说明书 · 2 个章节USen-US/);
  assert.match(cards[1].textContent, /其他语言也写到：fr-FR 1de-DE 1/);
  assert.equal(view.nodes['ms-summary-text'].textContent, '「ups」写在 2 款产品、3 份说明书的 3 个章节里');
  assert.deepEqual(view.regions.map(view.count), ['3', '1', '1', '0', '1']);
  assert.equal(view.regions[0].getAttribute('aria-pressed'), 'true');
  assert.deepEqual(view.cats.map(view.count), ['3', '0']);
  assert.equal(view.cats[1].classList.contains('is-zero'), true);
  assert.deepEqual(view.examples.map(link => [link.hidden, view.count(link)]), [[false, '3 份'], [true, '0 份']]);
  assert.equal(view.nodes['ms-stats'].textContent, '5份说明书4款产品7个语言版本8个章节');
});

test('choosing a region filters the results and records the filter in the URL', () => {
  const view = page({query: '?q=ups'});
  view.regions[4].fire('click');
  assert.equal(view.nodes['search-results'].children.length, 1);
  assert.deepEqual(view.replaced, ['/search.html?q=ups&region=JP']);
  assert.equal(view.regions[4].getAttribute('aria-pressed'), 'true');
  view.cats[0].fire('click');
  view.cats[0].fire('click');
  assert.deepEqual(view.replaced.slice(1), ['/search.html?q=ups&region=JP&cat=portable', '/search.html?q=ups&region=JP']);
});

test('when the filters leave nothing, the page says where the matches are and how to search that market', () => {
  const view = page({query: '?q=ups&region=CN'});
  assert.equal(view.nodes['ms-none'].hidden, false);
  assert.equal(view.nodes['ms-none-title'].textContent, '当前筛选（CN）下没有写到「ups」的章节');
  assert.equal(view.nodes['ms-none-elsewhere'].textContent, '去掉筛选后有 3 份说明书写到（US 1、EU 1、JP 1）。');
  assert.equal(view.nodes['ms-none-hint'].textContent, 'CN 的说明书只有 zh-CN 版本，可以换成这种语言的术语再搜。');
  view.nodes['ms-reset'].fire('click');
  assert.equal(view.nodes['ms-none'].hidden, true);
  assert.equal(view.nodes['search-results'].children.length, 2);
});

test('a query nothing matches hides the filters and gives search tips; no index shows a notice', () => {
  const view = page({query: '?q=zzz'});
  assert.equal(view.nodes['ms-filters'].hidden, true);
  assert.equal(view.nodes['ms-none-title'].textContent, '没有找到写到「zzz」的章节');
  assert.equal(view.nodes['ms-reset'].hidden, true);
  const missing = page({query: '?q=ups', index: null});
  assert.match(missing.nodes['ms-status'].textContent, /索引暂不可用/);
  assert.equal(missing.nodes['search-results'].children.length, 0);
});

test('without a query the page shows the examples and coverage', () => {
  const view = page();
  assert.equal(view.nodes['ms-start'].hidden, false);
  assert.equal(view.nodes['ms-filters'].hidden, true);
  assert.equal(view.nodes['ms-cover-langs'].textContent, 'en-US3fr-FR1de-DE1zh-CN1ja-JP1');
});
