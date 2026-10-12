import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/system-data.js', import.meta.url), 'utf8');
function load() {
  // No document: only the pure counting functions are set up.
  const context = {};
  vm.runInNewContext(script, context);
  return context.SystemDataModel;
}

const data = {
  capabilities: ['UPS', 'LED'],
  published: [
    {model: 'A', region: 'EU', lang: 'en'}, {model: 'A', region: 'EU', lang: 'fr'},
    {model: 'A', region: 'US', lang: 'en'}, {model: 'B', region: 'EU', lang: 'en'},
  ],
  targets: [
    {key: 'A_EU', model: 'A', region: 'EU', caps: [1, 0], review_pages: 3},
    {key: 'A_US', model: 'A', region: 'US', caps: [1, 1], review_pages: 0},
    {key: 'B_EU', model: 'B', region: 'EU', caps: [0, 0], review_pages: 0},
  ],
  assets: [
    {category: '插图', status: '成品', model: 'A', region: 'EU'},
    {category: '图标', status: '成品', model: 'ALL', region: 'ALL'},
    {category: '插图', status: '缺失', model: 'B', region: 'US'},
  ],
};
const all = {region: '', model: ''};
// Results are built in the script's own realm; compare them as plain JSON.
const plain = value => JSON.parse(JSON.stringify(value));

test('without a filter the counts cover every row', () => {
  const counts = load().summary(data, all);
  assert.equal(counts.manuals, 4);
  assert.equal(counts.models, 2);
  assert.equal(counts.languages, 2);
  assert.equal(counts.regions, 2);
  assert.equal(counts.targets, 3);
  assert.equal(counts.review_targets, 1);
  assert.equal(counts.assets, 3);
  assert.equal(counts.ready_share, 2 / 3);
});

test('region and model filters narrow every count; shared assets stay in', () => {
  const model = load();
  const counts = model.summary(data, {region: 'EU', model: 'A'});
  assert.equal(counts.manuals, 2);
  assert.equal(counts.targets, 1);
  // A's EU asset plus the ALL/ALL asset; B's US asset is out.
  assert.equal(counts.assets, 2);
  assert.equal(model.summary(data, {region: 'US', model: ''}).assets, 2);
  assert.equal(model.summary(data, {region: 'JP', model: ''}).manuals, 0);
  assert.equal(model.summary(data, {region: 'JP', model: ''}).ready_share, 1);
});

test('a missing publish manifest keeps the publication counts empty', () => {
  const counts = load().summary({...data, published: null}, all);
  assert.equal(counts.manuals, null);
  assert.equal(counts.languages, null);
  assert.equal(counts.targets, 3);
});

test('the matrix keeps every model of the region and orders languages by use', () => {
  const {languages, models} = load().matrix(data.published, {region: 'EU', model: 'B'});
  assert.deepEqual(plain(languages), ['en', 'fr']);
  assert.deepEqual(plain(models.map(m => [m.model, m.manuals])), [['A', 2], ['B', 1]]);
  assert.deepEqual(plain([...models[0].cells.get('fr').regions]), ['EU']);
});

test('coverage is the supported share of the filtered targets', () => {
  const model = load();
  assert.deepEqual(plain(model.coverage(data, all).map(c => [c.label, c.supported, c.targets])), [['UPS', 2, 3], ['LED', 1, 3]]);
  assert.deepEqual(plain(model.coverage(data, {region: '', model: 'A'}).map(c => c.share)), [1, 0.5]);
  assert.deepEqual(plain(model.coverage(data, {region: 'JP', model: ''}).map(c => c.targets)), [0, 0]);
});

test('counts are ordered by size, then label', () => {
  assert.deepEqual(plain(load().countBy(data.assets, 'status').map(c => [c.label, c.n])), [['成品', 2], ['缺失', 1]]);
});
