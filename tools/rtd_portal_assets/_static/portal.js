'use strict';
// 说明书资料库: manuals grouped by 产品类别 (a .family per category) and 产品系列 (a .group per series). The region,
// the search box and the language filter decide which cards show; the category chips link to their sections and
// count what the region shows. A category without a manual in the region keeps its heading and says so, unless a
// search or language filter is narrowing the list.
const $ = selector => document.querySelector(selector);
const cards = [...document.querySelectorAll('.card')];
let resultLimit = 12;

function render() {
  const selected = $('#region').selectedOptions[0];
  const query = $('#search').value.trim().toLowerCase();
  let count = 0;
  cards.forEach(card => {
    card.hidden = card.dataset.region !== selected.dataset.binding
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
  renderFamilies(selected, Boolean(query) || $('#search-language').value !== 'all');
  $('#empty').hidden = count !== 0;
  $('#clear').hidden = !$('#search').value;
  renderContent(query, selected.dataset.binding);
}

function renderFamilies(selected, narrowed) {
  document.querySelectorAll('.group').forEach(group => {
    const visible = group.querySelectorAll('.card:not([hidden])').length;
    group.hidden = visible === 0;
    const count = group.querySelector('.group-count');
    if (count) count.textContent = `${visible} 份`;
  });
  document.querySelectorAll('.family').forEach(family => {
    const visible = family.querySelectorAll('.card:not([hidden])').length;
    const empty = visible === 0;
    // 其他说明书 is not a category of its own: with nothing to show it leaves, chip included.
    const quiet = family.dataset.family === 'other';
    family.hidden = empty && (narrowed || quiet);
    family.classList.toggle('is-empty', empty);
    family.querySelector('.family-count').textContent = empty ? '' : `${visible} 份`;
    const note = family.querySelector('.family-empty');
    note.hidden = !empty;
    note.textContent = empty ? `${selected.value} 暂无说明书 · 其他区域 ${family.dataset.models} 款` : '';
    const chip = document.querySelector(`[data-chip="${CSS.escape(family.dataset.family)}"]`);
    if (!chip) return;
    chip.hidden = empty && quiet;
    chip.classList.toggle('is-empty', empty);
    chip.querySelector('.cat-chip-count').textContent = String(visible);
  });
}

// The region follows the reader: the last choice is restored on the next visit; the configured
// default applies only when nothing valid is stored (first visit, cleared or blocked storage).
// 产品知识 (product-knowledge.js) shares the region by name; picking one here also ends its 全部区域.
const REGION_KEY = 'hello-docs.manual-portal.region';
const ALL_KEY = 'hello-docs.manual-portal.region-all';
function restoreRegion() {
  let saved = null;
  try { saved = localStorage.getItem(REGION_KEY); } catch (error) { return; }
  if (saved && [...$('#region').options].some(option => option.value === saved)) $('#region').value = saved;
}
function rememberRegion() {
  try {
    localStorage.setItem(REGION_KEY, $('#region').value);
    localStorage.removeItem(ALL_KEY);
  } catch (error) { /* storage blocked: keep this visit's choice only */ }
}

$('#region').addEventListener('change', () => {
  rememberRegion();
  render();
});
$('#search').addEventListener('input', () => { resultLimit = 12; render(); });
$('#search-language').addEventListener('change', render);
$('#clear').addEventListener('click', () => {
  $('#search').value = '';
  render();
  $('#search').focus();
});
$('#reset').addEventListener('click', () => {
  $('#search').value = '';
  $('#search-language').value = 'all';
  render();
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
      const option = new Option(item.display, item.url);
      option.selected = new URL(item.url, document.baseURI).href === link.href;
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
    && (language === 'all' || language === item.lang)
    && tokens.every(t => (item.model + ' ' + item.name + ' ' + (item.short_name || '') + ' ' + item.title + ' ' + item.text).toLowerCase().includes(t)))
    .map(item => ({...item, score: tokens.reduce((score, t) => score + (item.model.toLowerCase().includes(t) || (item.short_name || '').toLowerCase().includes(t) ? 100 : 0) + (item.title.toLowerCase().includes(t) ? 20 : 0), 0)}))
    .sort((a,b) => b.score - a.score || a.model.localeCompare(b.model));
  const productCount = cards.filter(card => !card.hidden).length;
  $('#count').textContent = `${productCount} 份说明书 · ${hits.length} 个章节`;
  $('#content-status').textContent = window.manualSearchIndex
    ? `找到 ${hits.length} 个相关章节 · 当前显示 ${Math.min(resultLimit, hits.length)} 个`
    : '说明书内容索引暂不可用，仍可继续浏览下方资料。';
  hits.slice(0,resultLimit).forEach(item => {
    const article = document.createElement('article'); article.className = 'search-hit';
    const meta = document.createElement('div'); meta.className = 'meta';
    meta.textContent = `${item.name} · ${item.model}${item.short_name ? ' · ' + item.short_name : ''} · ${item.region === 'EU' ? 'EUUK' : item.region} · ${item.language}${item.version ? ' · ' + item.version : ''}`;
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
restoreRegion();
render();
