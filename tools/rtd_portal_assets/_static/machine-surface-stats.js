/* Machine-surface coverage, read from the deployed manifest and receipt.
   The manifest is written after pages render, so the page reads it at view
   time. Without JS or when either file is unreadable, the note and the
   download link remain. */
(() => {
  const MANIFEST = 'machine_surface_manifest.json';

  function summarize(manifest, receipt, manifestDigest) {
    const files = (receipt && receipt.files) || {};
    const variants = Array.isArray(manifest && manifest.variants) ? manifest.variants : [];
    const count = (pick) => variants.reduce((all, v) => {
      const key = pick(v);
      all[key] = (all[key] || 0) + 1;
      return all;
    }, {});
    const status = count((v) => !(v.url in files) ? 'unavailable'
      : files[v.url] === v.html_sha256 ? 'fresh' : 'stale');
    const callouts = {known: 0, total: 0};
    const images = {total: 0, withoutAlt: 0};
    variants.forEach((v) => {
      const severity = (v.counts && v.counts.callouts_by_severity) || {};
      Object.entries(severity).forEach(([key, n]) => {
        callouts.total += n;
        if (key !== 'unknown') callouts.known += n;
      });
      images.total += (v.counts && v.counts.images) || 0;
      images.withoutAlt += (v.counts && v.counts.images_without_alt) || 0;
    });
    const problems = [];
    if (!(MANIFEST in files)) problems.push('清单未纳入部署回执');
    else if (manifestDigest && manifestDigest !== files[MANIFEST]) problems.push('清单与部署回执不一致');
    if (manifest && receipt && manifest.source_sha256 !== receipt.source_sha256) problems.push('清单来自另一次冻结源');
    return {variants: variants.length, status, problems, callouts, images,
            modes: count((v) => v.generation_mode), revisions: count((v) => v.revision_kind),
            languages: count((v) => v.language_status)};
  }

  function tiles(s) {
    const fresh = s.status.fresh || 0;
    const notFresh = s.variants - fresh;
    const other = s.variants - (s.revisions.printed || 0) - (s.revisions.technical_snapshot || 0);
    const label = {html_compatibility: 'HTML 兼容', source_native: '源原生', ir_native: 'IR 原生'};
    const modes = Object.entries(s.modes).sort((x, y) => y[1] - x[1]);
    const main = modes.length ? label[modes[0][0]] || modes[0][0] : '—';
    const modeDetail = modes.map(([k, n]) => `${label[k] || k} ${n}`).join(' · ')
      + (s.modes.ir_native ? '' : '；IR 原生为长期目标');
    return [
      ['机读版本', String(s.variants), `需核语言 ${s.languages.needs_review || 0}`],
      ['与网页一致', `${fresh}/${s.variants}`, notFresh
        ? `过期 ${s.status.stale || 0} · 已下线 ${s.status.unavailable || 0}` : '全部 fresh'],
      ['生成方式', main, modeDetail],
      ['修订号', `${s.revisions.printed || 0}`, `正式修订；技术快照 ${s.revisions.technical_snapshot || 0} · 其他 ${other}`],
      ['警示识别', `${s.callouts.known}/${s.callouts.total}`, '其余标 unknown，待人工核对'],
      ['无 alt 图片', `${s.images.withoutAlt}/${s.images.total}`, '图片内文字未转写'],
    ];
  }

  async function digest(buffer) {
    const subtle = globalThis.crypto && globalThis.crypto.subtle;
    if (!subtle) return null;
    const bytes = new Uint8Array(await subtle.digest('SHA-256', buffer));
    return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  }

  async function render(root, fetchImpl) {
    const note = root.querySelector('[data-surface-note]');
    const list = root.querySelector('[data-surface-stats]');
    try {
      const get = async (url) => {
        const response = await fetchImpl(url, {cache: 'no-store'});
        if (!response.ok) throw new Error(String(response.status));
        return response.arrayBuffer();
      };
      const [manifestBytes, receiptBytes] = await Promise.all([
        get(root.dataset.surfaceManifest), get(root.dataset.surfaceReceipt)]);
      const decode = (buffer) => JSON.parse(new TextDecoder().decode(buffer));
      const summary = summarize(decode(manifestBytes), decode(receiptBytes), await digest(manifestBytes));
      list.replaceChildren(...tiles(summary).map(([label, value, detail]) => {
        const item = document.createElement('div');
        const dt = document.createElement('dt');
        const dd = document.createElement('dd');
        const small = document.createElement('small');
        dt.textContent = label;
        dd.textContent = value;
        small.textContent = detail;
        dd.append(small);
        item.append(dt, dd);
        return item;
      }));
      list.hidden = false;
      note.textContent = summary.problems.length
        ? `注意：${summary.problems.join('；')}。`
        : '以上统计读取本次部署的机读清单，并逐版本与部署回执中的网页哈希比对。';
      return summary;
    } catch (error) {
      note.textContent = '暂时读取不到机读清单，可直接下载查看。';
      return null;
    }
  }

  globalThis.MachineSurfaceStats = {summarize, tiles, render};
  if (typeof document !== 'undefined') {
    const root = document.querySelector('[data-surface-manifest]');
    if (root && typeof fetch === 'function') render(root, fetch);
  }
})();
