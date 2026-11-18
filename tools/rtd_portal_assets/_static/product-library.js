'use strict';
// 产品矩阵 (step 13; tools/rtd_portal_assets/product_matrix.html). Without JavaScript every category shows stacked and
// the filters stay hidden. With it, the tabs show one category at a time (the hash names it, so links keep working),
// and 项目 / 市场 highlight the chips that match and dim the rest; nothing is hidden. The pure parts are on
// globalThis.ProductLibrary for tests/product_library_ui.test.mjs.
(() => {
  // A chip's model × market rows: data-rows holds them as a JSON array of [project, market] pairs, so a project
  // with a space or a "|" still reads as one value. Anything unreadable counts as no rows.
  const chipRows = text => {
    try {
      const rows = JSON.parse(text || '[]');
      return Array.isArray(rows) ? rows.filter(pair => Array.isArray(pair) && pair.length === 2).map(pair => pair.map(String)) : [];
    } catch (error) {
      return [];
    }
  };
  // A chip's state under a filter: '' when no filter is set, else 'on' when one of its model × market rows
  // satisfies every set filter, else 'off'.
  const chipState = (chip, filter) => {
    const query = (filter.q || '').trim().toLowerCase();
    if (!filter.project && !filter.market && !query) return '';
    // The search matches a chip's model codes, product names and project (data-search, lower case).
    if (query && !(chip.search || '').includes(query)) return 'off';
    if (!filter.project && !filter.market) return 'on';
    const hit = chipRows(chip.rows).some(([project, market]) => {
      const projectOk = !filter.project || (filter.project === '-' ? project === '' : project === filter.project);
      const marketOk = !filter.market || market === filter.market;
      return projectOk && marketOk;
    });
    return hit ? 'on' : 'off';
  };
  // The text of the active-filter pill: the chosen options' labels, joined.
  const activeText = labels => labels.filter(Boolean).join(' · ');
  globalThis.ProductLibrary = {chipState, chipRows, activeText};

  if (typeof document === 'undefined') return;
  const panels = [...document.querySelectorAll('[data-panel]')];
  if (!panels.length) return;
  const tabs = [...document.querySelectorAll('[data-tab]')];
  const form = document.querySelector('[data-pl-filters]');
  const selects = [...document.querySelectorAll('[data-pl-filter]')];
  const active = document.querySelector('[data-pl-active]');
  const activeLabel = document.querySelector('[data-pl-active-text]');
  const chips = [...document.querySelectorAll('.pl-chip')];
  const search = document.querySelector('[data-pl-q]');
  document.documentElement.classList.add('pl-js');
  tabs.forEach(tab => { tab.closest('nav').hidden = false; });
  if (form) form.hidden = false;

  const show = id => {
    panels.forEach(panel => { panel.hidden = panel.dataset.panel !== id; });
    tabs.forEach(tab => {
      const on = tab.dataset.tab === id;
      tab.classList.toggle('is-on', on);
      tab.setAttribute('aria-current', on ? 'true' : 'false');
    });
  };
  const setHash = hash => {
    try { history.replaceState(null, '', hash); } catch (error) { /* a file:// preview may refuse; the page still works */ }
  };
  const apply = () => {
    const filter = Object.fromEntries(selects.map(select => [select.dataset.plFilter, select.value]));
    filter.q = search ? search.value : '';
    chips.forEach(chip => {
      const state = chipState(chip.dataset, filter);
      chip.classList.toggle('is-on', state === 'on');
      chip.classList.toggle('is-off', state === 'off');
    });
    const labels = selects.filter(select => select.value).map(select => select.options[select.selectedIndex].text);
    if (filter.q.trim()) labels.unshift(`搜索：${filter.q.trim()}`);
    if (active) active.hidden = !labels.length;
    if (activeLabel) activeLabel.textContent = activeText(labels);
  };

  tabs.forEach(tab => tab.addEventListener('click', event => {
    event.preventDefault();
    show(tab.dataset.tab);
    setHash(`#cat-${tab.dataset.tab}`);
  }));
  // Open the tab holding the first highlighted chip (after a search or a project chosen from elsewhere).
  const showFirstMatch = () => {
    const first = chips.find(chip => chip.classList.contains('is-on'));
    const panel = first && panels.find(item => item.contains(first));
    if (panel) show(panel.dataset.panel);
  };
  selects.forEach(select => select.addEventListener('change', apply));
  if (search) search.addEventListener('input', () => { apply(); showFirstMatch(); });
  const clear = document.querySelector('[data-pl-clear]');
  if (clear) clear.addEventListener('click', () => {
    selects.forEach(select => { select.value = ''; });
    if (search) search.value = '';
    apply();
  });

  const fromHash = () => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    const panel = panels.find(item => item.id === id);
    show((panel || panels[0]).dataset.panel);
  };
  window.addEventListener('hashchange', fromHash);
  fromHash();
  // A product page links its project here as ?project=…; a link carrying ?q=… fills the search (no page sends one
  // yet). Preselect them.
  const params = new URLSearchParams(window.location.search);
  const wanted = params.get('project');
  const projectSelect = selects.find(select => select.dataset.plFilter === 'project');
  if (wanted && projectSelect && [...projectSelect.options].some(option => option.value === wanted)) {
    projectSelect.value = wanted;
  }
  if (search && params.get('q')) search.value = params.get('q');
  apply();
  if (wanted || params.get('q')) showFirstMatch();
})();
