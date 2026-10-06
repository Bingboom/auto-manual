'use strict';
const $ = selector => document.querySelector(selector);
const cards = [...document.querySelectorAll('.card')];
let category = 'All products';
let resultLimit = 12;
const filtersOf = card => (card.dataset.filters || card.dataset.category).split('|');
const modelFilters = new Map(cards.map(card => [card.querySelector('[data-manual]').dataset.model, filtersOf(card)]));

function render() {
  const selected = $('#region').selectedOptions[0];
  const query = $('#search').value.trim().toLowerCase();
  let count = 0;
  cards.forEach(card => {
    card.hidden = card.dataset.region !== selected.dataset.binding
      || (category !== 'All products' && !filtersOf(card).includes(category))
      || (query && !query.split(/\s+/).every(token => card.dataset.search.includes(token)))
      || ($('#search-language').value !== 'all' && !JSON.parse(card.querySelector('[data-manual]').dataset.languages).some(item => item.url && (item.code === $('#search-language').value || (item.code === 'current' && $('#search-language').value === 'legacy'))));
    if (!card.hidden) count += 1;
  });
  $('#market-title').textContent = query ? `搜索结果 · ${selected.value}` : `${selected.value} 区域`;
  const marketNotes = {
    US: '美规说明书资料。',
    EU: '欧规和英规共用 EUUK 版本。',
    CN: '中规说明书资料。',
    JP: '日规说明书资料。',
  };
  $('#market-note').textContent = marketNotes[selected.dataset.binding] || `${selected.value} 区域说明书资料。`;
  $('#count').textContent = `${count} 份说明书`;
  document.querySelectorAll('.group').forEach(group => {
    const visible = group.querySelectorAll('.card:not([hidden])').length;
    group.hidden = visible === 0;
    group.querySelector('.group-count').textContent = `${visible} 份`;
  });
  document.querySelectorAll('.family').forEach(family => {
    family.hidden = !family.querySelector('.card:not([hidden])');
  });
  renderNeeds(selected.dataset.binding);
  $('#empty').hidden = count !== 0;
  $('#clear').hidden = !$('#search').value;
  renderContent(query, selected.dataset.binding);
}

function chooseCategory(value) {
  category = value;
  document.querySelectorAll('button[data-category]').forEach(button => {
    const active = button.dataset.category === category;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  render();
}

function renderNeeds(region) {
  // Scenario tiles follow the region: hide models without a manual there, and empty tiles.
  document.querySelectorAll('.need').forEach(tile => {
    const names = [...tile.querySelectorAll('.need-models i')];
    names.forEach(name => { name.hidden = name.dataset.region !== region; });
    const shown = names.filter(name => !name.hidden).length;
    tile.hidden = shown === 0;
    tile.querySelector('.need-count').textContent = `${shown} 份说明书`;
  });
  const needs = document.querySelector('.needs');
  if (needs) needs.hidden = !needs.querySelector('.need:not([hidden])');
  const inRegion = cards.filter(card => card.dataset.region === region);
  const eco = document.querySelector('.needs-eco');
  if (eco) eco.hidden = !inRegion.some(card => filtersOf(card).includes('ecosystem'));
  // Only offer filters that have a manual in this region.
  document.querySelectorAll('button[data-category]').forEach(button => {
    const value = button.dataset.category;
    button.hidden = value !== 'All products' && !inRegion.some(card => filtersOf(card).includes(value));
  });
}

document.querySelectorAll('[data-need]').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();
    $('#search').value = '';
    chooseCategory(link.dataset.need);
    $('#products').scrollIntoView({block: 'start'});
    $('#products').focus({preventScroll: true});
  });
});

$('#region').addEventListener('change', () => {
  const chip = document.querySelector(`button[data-category="${CSS.escape(category)}"]`);
  renderNeeds($('#region').selectedOptions[0].dataset.binding);
  if (chip && chip.hidden) chooseCategory('All products'); else render();
});
$('#search').addEventListener('input', () => { resultLimit = 12; render(); });
$('#search-language').addEventListener('change', render);
$('#clear').addEventListener('click', () => {
  $('#search').value = '';
  render();
  $('#search').focus();
});
document.querySelectorAll('button[data-category]').forEach(button => {
  button.addEventListener('click', () => chooseCategory(button.dataset.category));
});
$('#reset').addEventListener('click', () => {
  $('#search').value = '';
  $('#search-language').value = 'all';
  chooseCategory('All products');
});
document.querySelectorAll('[data-manual]').forEach(link => {
  link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
        || typeof $('#manual-dialog').showModal !== 'function') return;
    event.preventDefault();
    $('#dialog-title').textContent = link.dataset.name;
    $('#dialog-model').textContent = `${link.dataset.model} · ${link.dataset.edition} 版本`;
    $('#language').replaceChildren();
    JSON.parse(link.dataset.languages).forEach(item => {
      const option = new Option(item.label + (item.url ? '' : ` — ${item.unavailable_reason}`), item.url || '');
      option.disabled = !item.url;
      option.selected = Boolean(item.url) && new URL(item.url, document.baseURI).href === link.href;
      $('#language').add(option);
    });
    $('#open-manual').href = link.href;
    $('#manual-dialog').showModal();
  });
});
$('#language').addEventListener('change', () => {
  if ($('#language').value) $('#open-manual').href = $('#language').value;
});
$('.close').addEventListener('click', () => $('#manual-dialog').close());

function highlight(element, text, tokens) {
  const escaped = tokens.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp('(' + escaped.join('|') + ')', 'gi');
  text.split(regex).forEach((part, i) => {
    if (i % 2) { const mark = document.createElement('mark'); mark.textContent = part; element.append(mark); }
    else element.append(document.createTextNode(part));
  });
}
function renderContent(query, region) {
  const section = $('#content-results');
  section.hidden = !query;
  $('#content-list').replaceChildren();
  if (!query) return;
  const tokens = query.split(/\s+/).filter(Boolean);
  const language = $('#search-language').value;
  const hits = (window.manualSearchIndex || []).filter(item => item.region === region
    && (category === 'All products' || (modelFilters.get(item.model) || [item.category]).includes(category))
    && (language === 'all' || language === item.lang)
    && tokens.every(t => (item.model + ' ' + item.name + ' ' + item.title + ' ' + item.text).toLowerCase().includes(t)))
    .map(item => ({...item, score: tokens.reduce((score, t) => score + (item.model.toLowerCase().includes(t) ? 100 : 0) + (item.title.toLowerCase().includes(t) ? 20 : 0), 0)}))
    .sort((a,b) => b.score - a.score || a.model.localeCompare(b.model));
  const productCount = cards.filter(card => !card.hidden).length;
  $('#count').textContent = `${productCount} 份说明书 · ${hits.length} 个章节`;
  $('#content-status').textContent = window.manualSearchIndex
    ? `找到 ${hits.length} 个相关章节 · 当前显示 ${Math.min(resultLimit, hits.length)} 个`
    : '说明书内容索引暂不可用，仍可继续浏览下方资料。';
  hits.slice(0,resultLimit).forEach(item => {
    const article = document.createElement('article'); article.className = 'search-hit';
    const meta = document.createElement('div'); meta.className = 'meta';
    meta.textContent = `${item.name} · ${item.model} · ${item.region === 'EU' ? 'EUUK' : item.region} · ${item.language}${item.version ? ' · ' + item.version : ''}`;
    const link = document.createElement('a'); link.href = item.url; highlight(link, item.title, tokens);
    const excerpt = document.createElement('p');
    const first = item.text.toLowerCase().indexOf(tokens[0]); const start = Math.max(0,first - 90);
    highlight(excerpt, (start ? '…' : '') + item.text.slice(start,start+310) + (item.text.length > start+310 ? '…' : ''), tokens);
    article.append(meta,link,excerpt); $('#content-list').append(article);
  });
  $('#more-results').hidden = hits.length <= resultLimit;
  if (hits.length) $('#empty').hidden = true;
}
$('#search').value = new URLSearchParams(location.search).get('q') || '';
$('#more-results').addEventListener('click', () => { resultLimit += 12; render(); });
render();
