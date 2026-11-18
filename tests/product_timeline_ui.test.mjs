import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/product-timeline.js', import.meta.url), 'utf8');
const sandbox = {};
sandbox.globalThis = sandbox;
vm.runInNewContext(script, sandbox);
const {parseYearFrac, capacityBucket, selectPoints, packLaneNodes} = sandbox.ProductTimeline;

const SAMPLE_PRODUCTS = [
  {
    model: 'JE-1000B', short_name: 'E1000Pro', category: '便携储能', series: 'Pro', cap: '1度电',
    markets: [{market: 'JP', date: '2023-10-21', upper: true}]
  },
  {
    model: 'JE-1000F', short_name: 'E1000V2', category: '便携储能', series: '标准', cap: '1度电',
    markets: [{market: 'JP', date: '2026-02-26', upper: false}, {market: 'US', date: '2026-09-07', upper: false}]
  },
  {
    model: 'JS-100G', short_name: '100W Light', category: '太阳能板', series: 'SolarSaga', cap: '',
    markets: [{market: 'US', date: '2025-08-05', upper: false}]
  }
];

test('parseYearFrac orders chronological dates monotonically within and across years', () => {
  assert.ok(parseYearFrac('2024-01-01') < parseYearFrac('2024-06-15'));
  assert.ok(parseYearFrac('2024-12-20') < parseYearFrac('2025-01-02'));
  assert.equal(capacityBucket('1.5度电'), '1.5 – 1.8 度电');
  assert.equal(capacityBucket(''), '无容量档（板 / 配件）');
});

test('selectPoints picks earliest market by default, filters single market, and expands on market yAxis', () => {
  const earliest = selectPoints(SAMPLE_PRODUCTS, {category: '便携储能', yAxis: 'series', market: 'EARLIEST'});
  assert.deepEqual(Array.from(earliest, p => `${p.model}:${p.market}:${p.date}`), [
    'JE-1000B:JP:2023-10-21',
    'JE-1000F:JP:2026-02-26'
  ]);

  const usOnly = selectPoints(SAMPLE_PRODUCTS, {category: '便携储能', yAxis: 'series', market: 'US'});
  assert.deepEqual(Array.from(usOnly, p => `${p.model}:${p.market}:${p.date}`), ['JE-1000F:US:2026-09-07']);

  const byMarketLane = selectPoints(SAMPLE_PRODUCTS, {category: '便携储能', yAxis: 'market', market: 'EARLIEST'});
  assert.equal(byMarketLane.length, 3);
});

test('packLaneNodes separates same-day dots and assigns non-overlapping label tiers', () => {
  const cluster = [
    {model: 'JE-1000B', short_name: 'E1000Pro', market: 'JP', date: '2023-10-21'},
    {model: 'JE-2000A', short_name: 'E2000Pro', market: 'US', date: '2023-10-21'},
    {model: 'JE-3000A', short_name: 'E3000Pro', market: 'JP', date: '2023-10-21'}
  ];
  const xOf = frac => 150 + (frac - 2023) * 220;
  const packed = packLaneNodes(cluster, xOf, 150, 1100, {labelMode: 'short', market: 'EARLIEST', yAxis: 'series'});
  assert.equal(packed.nodes.length, 3);
  assert.ok(packed.nodes[1].x - packed.nodes[0].x >= 11);
  assert.ok(packed.nodes[2].x - packed.nodes[1].x >= 11);
  const uniqueTiers = new Set(packed.nodes.map(n => n.tier));
  assert.equal(uniqueTiers.size, 3);
});
