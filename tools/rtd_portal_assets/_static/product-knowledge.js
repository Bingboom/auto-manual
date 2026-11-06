'use strict';
// 产品知识 (2026-11 layout): filter the topic cards by region, product and theme. The energy-flow nodes and the
// theme-card heads set the theme and bring the list into view; a theme card's topic link clears whatever filter
// would hide its topic. Each card lists its region's manuals, the first VISIBLE_REFS of them until "+N" is
// pressed. Without JavaScript every card and every manual link shows.
(() => {
  const VISIBLE_REFS = 8;
  const region = document.getElementById('learning-region');
  const product = document.getElementById('learning-product');
  const list = document.getElementById('knowledge-list');
  const count = document.getElementById('learning-count');
  const empty = document.getElementById('learning-empty');
  const cards = [...document.querySelectorAll('.pk-card')];
  const chips = [...document.querySelectorAll('.pk-chips [data-tag]')];
  let tag = 'all';
  const has = (value, item) => (value || '').split(' ').includes(item);
  const regionMatches = value => region.value === 'all' || value === region.value;

  // Shows the card's manuals for the region and product; returns whether the card stays in the list.
  function renderCard(card) {
    let shown = 0;
    card.querySelectorAll('.pk-ref').forEach(ref => {
      const match = regionMatches(ref.dataset.region) && (product.value === 'all' || ref.dataset.model === product.value);
      ref.hidden = !match;
      ref.classList.toggle('is-extra', match && shown >= VISIBLE_REFS);
      if (match) shown += 1;
    });
    const more = card.querySelector('.pk-more');
    if (more) {
      more.hidden = shown <= VISIBLE_REFS || card.classList.contains('is-open');
      more.textContent = `+${shown - VISIBLE_REFS}`;
    }
    card.querySelector('.reference-count').textContent = String(shown);
    card.hidden = (tag !== 'all' && !has(card.dataset.tags, tag))
      || (product.value !== 'all' && !has(card.dataset.models, product.value)) || shown === 0;
    return !card.hidden;
  }

  function render() {
    [...product.options].forEach(option => {
      const available = option.value === 'all' || regionMatches(option.dataset.region);
      option.hidden = !available;
      option.disabled = !available;
    });
    if (!product.selectedOptions.length || product.selectedOptions[0].disabled) product.value = 'all';
    const visible = cards.filter(renderCard).length;
    chips.forEach(chip => {
      const on = chip.dataset.tag === tag;
      chip.classList.toggle('selected', on);
      chip.setAttribute('aria-pressed', String(on));
    });
    const oneRegion = region.value !== 'all';
    list.classList.toggle('pk-one-region', oneRegion);
    count.textContent = oneRegion ? `${visible} 项知识 · ${region.selectedOptions[0].textContent}` : `${visible} 项知识`;
    empty.hidden = visible !== 0;
  }

  chips.forEach(chip => chip.addEventListener('click', () => { tag = chip.dataset.tag; render(); }));
  document.querySelectorAll('[data-flow-tag], [data-theme]').forEach(button => button.addEventListener('click', () => {
    tag = button.dataset.flowTag || button.dataset.theme;
    render();
    list.scrollIntoView({block: 'start'});
  }));
  document.querySelectorAll('[data-topic-link]').forEach(link => link.addEventListener('click', () => {
    const card = document.getElementById(link.dataset.topicLink);
    if (card && card.hidden) { tag = 'all'; product.value = 'all'; render(); }
    if (card && card.hidden) { region.value = 'all'; render(); }
  }));
  document.querySelectorAll('.pk-more').forEach(button => button.addEventListener('click', () => {
    button.closest('.pk-card').classList.add('is-open');
    button.hidden = true;
  }));
  region.addEventListener('change', render);
  product.addEventListener('change', render);
  document.getElementById('learning-reset').addEventListener('click', () => { tag = 'all'; product.value = 'all'; render(); });
  render();
})();
