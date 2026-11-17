'use strict';
// 视觉媒体 front page (tools/rtd_portal_assets/asset_media.html). Without JavaScript every tile shows and the filters
// stay hidden. With it: a type chip and a search narrow the tiles, a tile opens a larger view, and the page's old
// section anchors (now on 素材清单) forward there. The pure parts are on globalThis.MediaFront for
// tests/media_front_ui.test.mjs.
(() => {
  // The section ids this page had before the inventory moved to 素材清单 (assets/media/inventory.html).
  const MOVED = ['scale', 'maintained', 'inventory', 'registry', 'symbols', 'used-by', 'sources', 'gaps'];
  const movedTarget = hash => {
    const id = decodeURIComponent((hash || '').replace(/^#/, ''));
    return MOVED.includes(id) ? `inventory.html#${id}` : '';
  };
  const matches = (tile, filter) => {
    if (filter.type && tile.type !== filter.type) return false;
    const words = (filter.q || '').trim().toLowerCase().split(/\s+/).filter(Boolean);
    return words.every(word => (tile.search || '').includes(word));
  };
  const usedText = editions => (editions ? `用于 ${editions} 本说明书` : '');
  globalThis.MediaFront = {MOVED, movedTarget, matches, usedText};

  if (typeof document === 'undefined') return;
  const target = movedTarget(window.location.hash);
  if (target) { window.location.replace(target); return; }
  const form = document.querySelector('[data-mf-filters]');
  const tiles = [...document.querySelectorAll('.mf-grid > li')];
  if (!form || !tiles.length) return;
  form.hidden = false;
  const chips = [...form.querySelectorAll('[data-mf-type]')];
  const search = form.querySelector('[data-mf-q]');
  const empty = document.querySelector('[data-mf-empty]');
  const filter = {type: '', q: ''};
  const apply = () => {
    let shown = 0;
    tiles.forEach(tile => {
      const on = matches(tile.dataset, filter);
      tile.hidden = !on;
      shown += on ? 1 : 0;
    });
    if (empty) empty.hidden = shown > 0;
  };
  chips.forEach(chip => chip.addEventListener('click', () => {
    filter.type = chip.dataset.mfType;
    chips.forEach(other => other.setAttribute('aria-pressed', String(other === chip)));
    apply();
  }));
  search.addEventListener('input', () => { filter.q = search.value; apply(); });

  const dialog = document.querySelector('[data-mf-dialog]');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  const image = dialog.querySelector('[data-mf-dialog-img]');
  const title = dialog.querySelector('[data-mf-dialog-title]');
  const meta = dialog.querySelector('[data-mf-dialog-meta]');
  const art = dialog.querySelector('.mf-dialog-art');
  document.querySelectorAll('[data-mf-open]').forEach(button => button.addEventListener('click', () => {
    const source = button.querySelector('img');
    image.src = source.src;
    image.alt = button.getAttribute('aria-label');
    art.style.background = button.querySelector('.mf-art').style.background;
    title.textContent = button.getAttribute('aria-label');
    meta.textContent = [button.dataset.mfTypeLabel, usedText(Number(button.dataset.mfUsed || 0))].filter(Boolean).join(' · ');
    dialog.showModal();
  }));
})();
