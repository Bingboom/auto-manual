import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const script = readFileSync(new URL('../tools/rtd_portal_assets/_static/machine-surface-stats.js', import.meta.url), 'utf8');
const context = {};
vm.runInNewContext(script, context);
const {summarize, tiles} = context.MachineSurfaceStats;

const variant = (url, hash, extra = {}) => ({
  url, html_sha256: hash, generation_mode: 'html_compatibility', revision_kind: 'printed',
  language_status: 'verified',
  counts: {callouts_by_severity: {warning: 2, unknown: 1}, images: 4, images_without_alt: 1}, ...extra,
});
const manifest = {source_sha256: 's', variants: [
  variant('a.html', 'h1'),
  variant('b.html', 'h2', {revision_kind: 'technical_snapshot', language_status: 'needs_review'}),
  variant('c.html', 'h3'),
]};
const receipt = {source_sha256: 's', files: {'a.html': 'h1', 'b.html': 'changed', 'machine_surface_manifest.json': 'm'}};

test('freshness compares every variant with the deployed receipt', () => {
  const s = summarize(manifest, receipt, 'm');
  assert.deepEqual({...s.status}, {fresh: 1, stale: 1, unavailable: 1});
  assert.deepEqual([...s.problems], []);
  assert.deepEqual({...s.callouts}, {known: 6, total: 9});
  assert.deepEqual({...s.images}, {total: 12, withoutAlt: 3});
  assert.equal(s.languages.needs_review, 1);
  const rows = tiles(s);
  assert.equal(rows[1][1], '1/3');
  assert.match(rows[1][2], /过期 1 · 已下线 1/);
  assert.equal(rows[2][1], 'HTML 兼容');
  assert.equal(rows[2][2], 'HTML 兼容 3；IR 原生为长期目标');
  assert.equal(rows[4][1], '6/9');
});

test('a manifest the receipt does not seal is reported, never shown as current', () => {
  assert.deepEqual([...summarize(manifest, {...receipt, files: {'a.html': 'h1'}}, null).problems], ['清单未纳入部署回执']);
  assert.deepEqual([...summarize(manifest, receipt, 'other').problems], ['清单与部署回执不一致']);
  assert.deepEqual([...summarize(manifest, {...receipt, source_sha256: 'x'}, 'm').problems], ['清单来自另一次冻结源']);
});

test('an unreadable manifest leaves the fallback note and hides no content', async () => {
  const note = {textContent: 'fallback'};
  const list = {hidden: true};
  const root = {dataset: {surfaceManifest: 'm', surfaceReceipt: 'r'},
    querySelector: (q) => q === '[data-surface-note]' ? note : list};
  const result = await context.MachineSurfaceStats.render(root, async () => ({ok: false, status: 404}));
  assert.equal(result, null);
  assert.equal(list.hidden, true);
  assert.match(note.textContent, /读取不到机读清单/);
});
