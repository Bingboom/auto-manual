'use strict';
// Size each same-origin component preview to its content; without JS the
// declared height (with scrolling) stays. Measure the preview's <main>, not
// the document: a document is never shorter than its frame, so measuring it
// could only ever grow the frame.
(() => {
  const fit = frame => {
    try {
      const doc = frame.contentDocument;
      const main = doc && doc.querySelector('main');
      if (!main || frame.offsetParent === null) return;
      const view = doc.defaultView;
      const margin = parseFloat(view.getComputedStyle(main).marginBottom) || 0;
      const bottom = main.getBoundingClientRect().bottom + view.scrollY + margin;
      if (bottom <= 0) return;
      const height = Math.ceil(bottom) + 'px';
      frame.style.height = height;
      // A scaled preview (组件's open card) keeps its box as tall as the scaled content.
      const box = frame.parentElement;
      if (box && box.classList.contains('ds-zoom')) box.style.setProperty('--ds-zoom-h', height);
    } catch (error) {
      // A cross-origin frame keeps its declared height.
    }
  };
  // 概览's gallery and 组件's thumbnails and open card lay each preview out SHOT_WIDTH px wide (the manual's widest
  // table fits) and scale it to its box; a hidden box measures 0 and is scaled when it is shown.
  const SHOT_WIDTH = 720;
  const scaleShot = box => {
    const width = box.clientWidth;
    if (width > 0) box.style.setProperty('--ds-shot-scale', String(Math.min(1, width / SHOT_WIDTH)));
  };
  document.querySelectorAll('.ds-shot-frame, .ds-zoom').forEach(box => {
    scaleShot(box);
    if ('ResizeObserver' in window) new ResizeObserver(() => scaleShot(box)).observe(box);
  });
  document.querySelectorAll('iframe.ds-preview').forEach(frame => {
    frame.addEventListener('load', () => {
      fit(frame);
      try {
        const main = frame.contentDocument && frame.contentDocument.querySelector('main');
        if (main && 'ResizeObserver' in window) new ResizeObserver(() => fit(frame)).observe(main);
      } catch (error) {
        // Keep the declared height.
      }
    });
  });
})();

// The inner tabs (2026-11 step 10). Rows are <details> and work without this; here the filter bars, the 组件 card
// details, the 图标与素材 side panel and the 「显示全部」 buttons.
(() => {
  const pressed = node => node.getAttribute('aria-pressed') === 'true';

  // A filter bar: a chip picks one group (data-group, '' for all), the search box narrows by data-search.
  const filterBar = (panel, apply) => {
    const bar = panel.querySelector('.ds-filter');
    if (!bar) return;
    const chips = [...bar.querySelectorAll('.ds-chip')];
    const input = bar.querySelector('input');
    const state = {group: '', query: ''};
    chips.forEach(chip => chip.addEventListener('click', () => {
      state.group = chip.dataset.group;
      chips.forEach(other => other.setAttribute('aria-pressed', String(other === chip)));
      apply(state);
    }));
    if (input) input.addEventListener('input', () => {
      state.query = input.value.trim().toLowerCase();
      apply(state);
    });
  };
  const showEmpty = (panel, shown) => {
    const empty = panel.querySelector('.ds-empty');
    if (empty) empty.hidden = shown > 0;
  };

  // 组件: one card open at a time; its detail follows it in the DOM and spans the row below it.
  const components = document.getElementById('components');
  if (components) {
    const cards = [...components.querySelectorAll('.ds-comp')];
    const openCard = (card, on) => {
      const detail = document.getElementById(card.id + '-detail');
      if (!detail) return;
      detail.hidden = !on;
      card.classList.toggle('is-open', on);
      const button = card.querySelector('.ds-comp-open');
      if (button) button.setAttribute('aria-expanded', String(on));
    };
    const toggle = card => {
      const opening = !card.classList.contains('is-open');
      cards.forEach(other => openCard(other, opening && other === card));
      return opening;
    };
    cards.forEach(card => {
      const button = card.querySelector('.ds-comp-open');
      if (!button) return;
      button.addEventListener('click', () => {
        history.replaceState(null, '', toggle(card) ? '#' + card.id : '#components');
      });
    });
    components.querySelectorAll('.ds-comp-close').forEach(button => button.addEventListener('click', () => {
      const detail = button.closest('.ds-comp-detail');
      const card = detail && document.getElementById(detail.id.replace(/-detail$/, ''));
      if (!card) return;
      openCard(card, false);
      card.querySelector('.ds-comp-open').focus();
      history.replaceState(null, '', '#components');
    }));
    filterBar(components, ({group, query}) => {
      let shown = 0;
      components.querySelectorAll('.ds-comp-group').forEach(section => {
        let visible = 0;
        section.querySelectorAll('.ds-comp').forEach(card => {
          const match = (!group || section.dataset.group === group) && (!query || card.dataset.search.includes(query));
          card.hidden = !match;
          if (!match) openCard(card, false);
          if (match) visible += 1;
        });
        section.hidden = visible === 0;
        shown += visible;
      });
      showEmpty(components, shown);
    });
    // A #component-… address opens that card; the shared tab script has already shown the panel.
    const openFromHash = () => {
      const id = decodeURIComponent(location.hash.slice(1));
      const card = id.startsWith('component-') ? document.getElementById(id) : null;
      if (card && card.classList.contains('ds-comp') && !card.classList.contains('is-open')) toggle(card);
    };
    window.addEventListener('hashchange', openFromHash);
    openFromHash();
  }

  // 图标与素材: a tile selects into the side panel; with none selected it shows the current group's notes.
  const assets = document.getElementById('assets');
  if (assets) {
    const groups = [...assets.querySelectorAll('.ds-asset-group')];
    const tiles = [...assets.querySelectorAll('.ds-tile')];
    const side = assets.querySelector('.ds-asset-side');
    const notes = side ? [...side.querySelectorAll('.ds-side-group')] : [];
    const details = side ? [...side.querySelectorAll('.ds-side-asset')] : [];
    let current = groups.length ? groups[0].dataset.group : '';
    const showSide = asset => {
      details.forEach(section => { section.hidden = section.id !== asset; });
      notes.forEach(section => { section.hidden = Boolean(asset) || section.dataset.group !== current; });
    };
    const select = tile => {
      tiles.forEach(other => other.setAttribute('aria-pressed', String(other === tile)));
      showSide(tile ? tile.dataset.asset : '');
    };
    tiles.forEach(tile => tile.addEventListener('click', () => {
      const on = !pressed(tile);
      select(on ? tile : null);
      if (on && side && side.scrollIntoView) side.scrollIntoView({block: 'nearest'});
    }));
    filterBar(assets, ({group, query}) => {
      current = group || (groups.length ? groups[0].dataset.group : '');
      let shown = 0;
      groups.forEach(box => {
        let visible = 0;
        box.querySelectorAll('.ds-tile').forEach(tile => {
          tile.hidden = Boolean(query) && !tile.dataset.search.includes(query);
          if (!tile.hidden) visible += 1;
        });
        box.hidden = (Boolean(group) && box.dataset.group !== group) || visible === 0;
        box.classList.toggle('is-search', Boolean(query));
        if (!box.hidden && (group || query)) box.open = true;
        if (!box.hidden) shown += visible;
      });
      showEmpty(assets, shown);
      const chosen = tiles.find(pressed);
      select(chosen && !chosen.hidden && !chosen.closest('.ds-asset-group').hidden ? chosen : null);
    });
    assets.querySelectorAll('.ds-copy').forEach(button => {
      const label = button.textContent;
      button.addEventListener('click', () => {
        if (!navigator.clipboard) return;
        navigator.clipboard.writeText(button.dataset.copy).then(() => {
          button.textContent = '已复制';
          setTimeout(() => { button.textContent = label; }, 1600);
        }, () => {});
      });
    });
  }

  // 「显示全部」: the button's host (data-ds-more) shows its folded rows or tiles, and folds them again.
  document.querySelectorAll('.ds-show-all').forEach(button => {
    const host = button.closest('[data-ds-more]');
    if (!host) return;
    const label = button.textContent;
    button.addEventListener('click', () => {
      const all = !host.classList.contains('is-all');
      host.classList.toggle('is-all', all);
      button.setAttribute('aria-expanded', String(all));
      button.textContent = all ? '收起' : label;
    });
  });
})();
