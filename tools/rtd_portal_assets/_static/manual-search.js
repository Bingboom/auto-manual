'use strict';
// 搜索说明书正文 (search.html, the 2026-11 design). It searches window.manualSearchIndex, which
// tools/rtd/portal_search.py writes with one row per manual section (title, section url, text, model, short name,
// product name, region, language). Results are grouped by product, then by manual (a product in one region). Each
// manual shows one language edition, and the other languages that also match are listed with their section counts.
// The pure functions are on ManualSearch, which tests/manual_search_ui.test.mjs runs; the wiring at the end only reads
// and writes the page.
var ManualSearch = (() => {
  const ALL = 'all';
  const WORD = /[0-9A-Za-z]/;
  const PRODUCT = 100;   // the query names the product (model, short name or product name)
  const TITLE = 20;      // the section title has it
  const TEXT_CAP = 5;    // each occurrence in the text counts once, up to five
  const SHOWN = 2;       // sections a manual shows before 展开
  const PAGE = 10;       // products per page
  const escapeRegExp = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // The page config lists languages as [code, display code] pairs in the settings order.
  const codesOf = config => ((config && config.languages) || []).map(([code]) => code);

  function tokens(query) {
    return String(query || '').trim().toLowerCase().split(/\s+/).filter(Boolean);
  }

  // A token that starts with a letter or digit matches whole words, so UPS finds "UPS" and "UPS機能" but not
  // "upside". Group 1 holds the character before the word (no lookbehind needed). Other tokens, such as Chinese or
  // Japanese words, match as written.
  function compile(token, whole) {
    const body = escapeRegExp(token);
    let source = `()(${body})`;
    if (WORD.test(token[0])) {
      source = `(^|[^0-9A-Za-z])(${body})${whole && WORD.test(token[token.length - 1]) ? '(?![0-9A-Za-z])' : ''}`;
    }
    return {token, whole, test: new RegExp(source, 'i'), all: new RegExp(source, 'gi')};
  }
  function found(matcher, row) {
    return matcher.test.test(row.product) || matcher.test.test(row.title) || matcher.test.test(row.text);
  }
  // Whole words first. If no section anywhere has the whole word, the token matches the beginnings of words instead.
  function matcher(token, rows, cache) {
    if (cache && cache.has(token)) return cache.get(token);
    let result = compile(token, true);
    const wordy = WORD.test(token[0]) && WORD.test(token[token.length - 1]);
    if (wordy && !rows.some(row => found(result, row))) result = compile(token, false);
    if (cache) cache.set(token, result);
    return result;
  }
  function count(m, text, cap) {
    m.all.lastIndex = 0;
    let n = 0;
    while (n < cap && m.all.exec(text)) n += 1;
    return n;
  }

  // Index rows with what the search reads: the product words, the manual (model and region), the published page and
  // the 产品分类 category and series the page config names for the model.
  function prepare(rows, config) {
    const models = (config && config.models) || {};
    return rows.map((row, index) => {
      const info = models[row.model] || {};
      return {
        index, model: row.model, name: row.name || '', short: row.short_name || '', region: row.region, lang: row.lang,
        title: row.title || '', text: row.text || '', url: row.url, page: String(row.url).split('#')[0],
        product: [row.model, row.short_name || '', row.name || ''].join(' '), manual: `${row.model}|${row.region}`,
        category: info.category || '', series: info.series || '',
      };
    });
  }

  // Every token must match the product words, the section title or its text. A match in the product words counts
  // most, then one in the title, then each occurrence in the text.
  function search(rows, query, cache) {
    const list = tokens(query);
    const matchers = list.map(token => matcher(token, rows, cache));
    const hits = [];
    if (!matchers.length) return {tokens: list, matchers, hits};
    for (const row of rows) {
      let score = 0;
      let ok = true;
      for (const m of matchers) {
        const inProduct = m.test.test(row.product);
        const inTitle = m.test.test(row.title);
        const inText = count(m, row.text, TEXT_CAP);
        if (!inProduct && !inTitle && !inText) { ok = false; break; }
        score += (inProduct ? PRODUCT : 0) + (inTitle ? TITLE : 0) + inText;
      }
      if (ok) hits.push({row, score});
    }
    return {tokens: list, matchers, hits};
  }

  function keep(row, state, skip) {
    return (skip === 'region' || state.region === ALL || row.region === state.region)
      && (skip === 'cat' || state.cat === ALL || row.category === state.cat)
      && (skip === 'lang' || state.lang === ALL || row.lang === state.lang);
  }
  // Manuals per value of one filter, under the other two filters; `all` is the total across its values.
  function manualCounts(hits, state, skip, key) {
    const sets = new Map();
    const every = new Set();
    for (const {row} of hits) {
      if (!keep(row, state, skip)) continue;
      if (!sets.has(row[key])) sets.set(row[key], new Set());
      sets.get(row[key]).add(row.manual);
      every.add(row.manual);
    }
    const counts = {[ALL]: every.size};
    sets.forEach((set, value) => { counts[value] = set.size; });
    return counts;
  }
  function facets(hits, state) {
    return {
      region: manualCounts(hits, state, 'region', 'region'),
      cat: manualCounts(hits, state, 'cat', 'category'),
      lang: manualCounts(hits, state, 'lang', 'lang'),
    };
  }

  function order(list) {
    return value => { const at = list.indexOf(value); return at < 0 ? list.length : at; };
  }
  const byScore = (a, b) => b.score - a.score || a.row.index - b.row.index;

  // One market per manual: its English edition when it has one, else its first language in the settings order.
  function market(manual, languagePosition) {
    const langs = [...manual.editions.keys()].sort((a, b) => languagePosition(a) - languagePosition(b));
    const shown = langs.includes('en') ? 'en' : langs[0];
    const sections = manual.editions.get(shown).sort(byScore);
    const others = langs.filter(lang => lang !== shown).map(lang => {
      const edition = manual.editions.get(lang).sort(byScore);
      return {lang, count: edition.length, url: edition[0].row.url};
    });
    return {region: manual.region, lang: shown, sections, others, url: sections[0].row.page,
            score: sections[0].score + 2 * Math.min(sections.length, TEXT_CAP)};
  }
  function product(model, markets, regionPosition) {
    markets.sort((a, b) => b.score - a.score || regionPosition(a.region) - regionPosition(b.region));
    const rows = markets.flatMap(item => item.sections.map(hit => hit.row));
    const named = rows.find(row => row.lang === 'en') || rows[0];
    return {
      model, markets, score: markets[0].score, short: named.short, category: named.category, series: named.series,
      name: named.name.replace(new RegExp(`\\s*·\\s*${escapeRegExp(model)}$`), ''),
      sections: markets.reduce((sum, item) => sum + item.sections.length, 0),
    };
  }
  // The hits the filters keep, as products (best first), each with its markets (best first).
  function group(hits, state, config) {
    const languagePosition = order([...codesOf(config), 'legacy']);
    const regionPosition = order((config && config.regions) || []);
    const manuals = new Map();
    for (const hit of hits) {
      if (!keep(hit.row, state)) continue;
      const {row} = hit;
      if (!manuals.has(row.manual)) manuals.set(row.manual, {model: row.model, region: row.region, editions: new Map()});
      const editions = manuals.get(row.manual).editions;
      if (!editions.has(row.lang)) editions.set(row.lang, []);
      editions.get(row.lang).push(hit);
    }
    const byModel = new Map();
    let sections = 0;
    for (const manual of manuals.values()) {
      const item = market(manual, languagePosition);
      sections += item.sections.length;
      if (!byModel.has(manual.model)) byModel.set(manual.model, []);
      byModel.get(manual.model).push(item);
    }
    const products = [...byModel].map(([model, markets]) => product(model, markets, regionPosition))
      .sort((a, b) => b.score - a.score || a.model.localeCompare(b.model));
    return {products, manuals: manuals.size, sections};
  }

  // The part of a section's text around its first match.
  function snippet(text, matchers, width = 180) {
    let first = -1;
    for (const m of matchers) {
      m.all.lastIndex = 0;
      const hit = m.all.exec(text);
      if (hit) {
        const at = hit.index + hit[1].length;
        if (first < 0 || at < first) first = at;
      }
    }
    let start = Math.max(0, Math.min(first - 60, text.length - width));
    const space = text.indexOf(' ', start);
    if (start > 0 && space > -1 && space < start + 15 && space < first) start = space + 1;
    const end = Math.min(text.length, start + width);
    return {text: text.slice(start, end), lead: start > 0, trail: end < text.length};
  }
  // [text, marked] pieces of a string, with every matched word marked.
  function pieces(text, matchers) {
    const spans = [];
    for (const m of matchers) {
      m.all.lastIndex = 0;
      let hit;
      while ((hit = m.all.exec(text))) spans.push([hit.index + hit[1].length, hit.index + hit[0].length]);
    }
    spans.sort((a, b) => a[0] - b[0]);
    const out = [];
    let at = 0;
    for (const [start, end] of spans) {
      if (end <= at) continue;
      if (start > at) out.push([text.slice(at, start), false]);
      out.push([text.slice(Math.max(start, at), end), true]);
      at = end;
    }
    if (at < text.length) out.push([text.slice(at), false]);
    return out;
  }

  // What the index covers: manuals, products, language editions and sections, with manuals per region and editions
  // per language in the configured order.
  function coverage(rows, config) {
    const manuals = new Set();
    const models = new Set();
    const pages = new Set();
    const regions = new Map();
    const languages = new Map();
    const add = (map, key, value) => { if (!map.has(key)) map.set(key, new Set()); map.get(key).add(value); };
    for (const row of rows) {
      manuals.add(row.manual);
      models.add(row.model);
      pages.add(row.page);
      add(regions, row.region, row.manual);
      add(languages, row.lang, row.page);
    }
    const regionPosition = order((config && config.regions) || []);
    const languagePosition = order([...codesOf(config), 'legacy']);
    const listed = (map, position) => [...map].sort((a, b) => position(a[0]) - position(b[0]))
      .map(([key, set]) => [key, set.size]);
    return {manuals: manuals.size, products: models.size, editions: pages.size, sections: rows.length,
            regions: listed(regions, regionPosition), languages: listed(languages, languagePosition)};
  }
  // The languages a region's manuals are published in (legacy pages are left out: their language is unconfirmed).
  function languagesOf(rows, region) {
    return [...new Set(rows.filter(row => row.region === region && row.lang !== 'legacy').map(row => row.lang))];
  }

  function readState(query, config) {
    const params = new URLSearchParams(query);
    const pick = (value, allowed) => (value && allowed.includes(value) ? value : ALL);
    return {
      q: params.get('q') || '',
      region: pick(params.get('region'), (config && config.regions) || []),
      cat: pick(params.get('cat'), Object.keys((config && config.categories) || {})),
      lang: pick(params.get('lang'), [...codesOf(config), 'legacy']),
    };
  }
  function writeState(state) {
    const params = new URLSearchParams();
    if (state.q.trim()) params.set('q', state.q.trim());
    ['region', 'cat', 'lang'].forEach(key => { if (state[key] !== ALL) params.set(key, state[key]); });
    const text = params.toString();
    return text ? `?${text}` : '';
  }

  return {ALL, SHOWN, PAGE, tokens, matcher, prepare, search, facets, group, snippet, pieces, coverage, languagesOf,
          readState, writeState};
})();

(() => {
  if (typeof document === 'undefined') return;
  const configNode = document.getElementById('ms-config');
  if (!configNode) return;
  const config = JSON.parse(configNode.textContent);
  const S = ManualSearch;
  const ALL = S.ALL;
  const MAX = 50;   // sections a manual lists once expanded
  const $ = id => document.getElementById(id);
  const input = $('ms-query');
  const status = $('ms-status');
  const index = typeof window !== 'undefined' ? window.manualSearchIndex : undefined;
  if (!Array.isArray(index)) {
    status.textContent = '说明书正文索引暂不可用，可以回到说明书资料库按产品查看说明书。';
    return;
  }
  const rows = S.prepare(index, config);
  const cache = new Map();
  const state = S.readState(window.location.search, config);
  let limit = S.PAGE;
  let timer = null;
  const displays = new Map(config.languages || []);
  const code = lang => (lang === 'legacy' ? config.legacy : (displays.get(lang) || lang));
  const el = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const marked = (parent, text, matchers) => {
    S.pieces(text, matchers).forEach(([part, mark]) => parent.append(mark ? el('mark', '', part) : document.createTextNode(part)));
    return parent;
  };
  const regionButtons = [...document.querySelectorAll('[data-region]')];
  const categoryButtons = [...document.querySelectorAll('[data-cat]')];
  const languageSelect = $('ms-lang');

  function renderCoverage() {
    const cover = S.coverage(rows, config);
    [[cover.manuals, '份说明书'], [cover.products, '款产品'], [cover.editions, '个语言版本'], [cover.sections, '个章节']]
      .forEach(([value, label]) => {
        const item = el('div', 'ms-stat');
        item.append(el('b', '', value.toLocaleString('en-US')), el('span', '', label));
        $('ms-stats').append(item);
      });
    const pills = (target, list, label) => list.forEach(([key, value]) => {
      const pill = el('span', 'ms-pill', label(key));
      pill.append(el('b', '', String(value)));
      target.append(pill);
    });
    pills($('ms-cover-regions'), cover.regions, region => region);
    pills($('ms-cover-langs'), cover.languages, code);
  }
  // Example queries show how many manuals they find now; one that finds nothing leaves.
  function renderExamples() {
    document.querySelectorAll('[data-q]').forEach(link => {
      const found = S.facets(S.search(rows, link.dataset.q, cache).hits, {region: ALL, cat: ALL, lang: ALL}).region[ALL];
      link.hidden = !found;
      link.querySelector('b').textContent = `${found} 份`;
      link.addEventListener('click', event => {
        event.preventDefault();
        input.value = link.dataset.q;
        update(true);
        input.focus();
      });
    });
  }

  function renderFilters(counts) {
    regionButtons.forEach(button => {
      const value = button.dataset.region;
      const found = counts.region[value] || 0;
      button.setAttribute('aria-pressed', String(state.region === value));
      button.classList.toggle('is-zero', !found && state.region !== value);
      button.querySelector('b').textContent = String(found);
    });
    categoryButtons.forEach(button => {
      const value = button.dataset.cat;
      const found = counts.cat[value] || 0;
      button.setAttribute('aria-pressed', String(state.cat === value));
      button.classList.toggle('is-zero', !found && state.cat !== value);
      button.querySelector('b').textContent = String(found);
    });
    [...languageSelect.options].forEach(option => {
      if (option.value === ALL) return;
      const found = counts.lang[option.value] || 0;
      option.textContent = `${code(option.value)}（${found}）`;
      option.disabled = !found && option.value !== state.lang;
    });
    languageSelect.value = state.lang;
  }

  function sectionItem(hit, matchers, hidden) {
    const item = el('li');
    item.hidden = hidden;
    const link = el('a');
    link.href = hit.row.url;
    marked(link, hit.row.title || '（无标题）', matchers);
    const part = S.snippet(hit.row.text, matchers);
    item.append(link, marked(el('p'), `${part.lead ? '…' : ''}${part.text}${part.trail ? '…' : ''}`, matchers));
    return item;
  }
  function marketBlock(market, matchers) {
    const block = el('section', 'ms-market');
    const head = el('div', 'ms-mhead');
    const open = el('a', 'ms-open', '打开说明书 →');
    open.href = market.url;
    head.append(el('span', 'ms-mk', market.region), el('span', 'ms-ml', code(market.lang)),
                el('span', 'ms-mc', `${market.sections.length} 个章节`), open);
    const list = el('ul', 'ms-hits');
    const listed = market.sections.slice(0, MAX);
    listed.forEach((hit, at) => list.append(sectionItem(hit, matchers, at >= S.SHOWN)));
    block.append(head, list);
    const foot = el('div', 'ms-mfoot');
    const rest = listed.length - S.SHOWN;
    if (rest > 0) {
      const toggle = el('button', 'ms-expand', `展开其余 ${rest} 个章节`);
      toggle.type = 'button';
      toggle.setAttribute('aria-expanded', 'false');
      toggle.addEventListener('click', () => {
        const open = toggle.getAttribute('aria-expanded') !== 'true';
        [...list.children].forEach((item, at) => { item.hidden = !open && at >= S.SHOWN; });
        toggle.setAttribute('aria-expanded', String(open));
        toggle.textContent = open ? '收起' : `展开其余 ${rest} 个章节`;
      });
      foot.append(toggle);
    }
    if (market.others.length) {
      const others = el('span', 'ms-others', '其他语言也写到：');
      market.others.forEach(other => {
        const link = el('a', '', `${code(other.lang)} ${other.count}`);
        link.href = other.url;
        others.append(link);
      });
      foot.append(others);
    }
    if (rest > 0 || market.others.length) block.append(foot);
    return block;
  }
  function productCard(item, matchers) {
    const card = el('article', 'ms-prod');
    const head = el('header', 'ms-phead');
    const id = el('div', 'ms-pid');
    id.append(el('b', '', item.model));
    if (item.short) id.append(el('span', 'ms-short', item.short));
    if (item.name && item.name !== item.model) id.append(el('span', 'ms-name', item.name));
    const meta = el('div', 'ms-pmeta');
    const category = config.categories[item.category] || '';
    const kind = [category, item.series !== category ? item.series : ''].filter(Boolean).join(' · ');
    if (kind) meta.append(el('span', '', kind));
    meta.append(el('span', '', `${item.markets.length} 份说明书 · ${item.sections} 个章节`));
    head.append(id, meta);
    card.append(head);
    item.markets.forEach(entry => card.append(marketBlock(entry, matchers)));
    return card;
  }

  function renderSummary(query, grouped) {
    const text = $('ms-summary-text');
    text.replaceChildren(el('b', '', `「${query}」`), '写在 ', el('b', '', String(grouped.products.length)), ' 款产品、',
                         el('b', '', String(grouped.manuals)), ' 份说明书的 ', el('b', '', String(grouped.sections)),
                         ' 个章节里');
    $('ms-summary-note').textContent = `型号或简称写到的排最前，其次是章节标题写到的 · ${
      state.lang === ALL ? '每份说明书显示一种语言，有英文显示英文' : `只看 ${code(state.lang)} 版本`}`;
  }
  function renderNone(query, result) {
    const elsewhere = $('ms-none-elsewhere');
    const reset = $('ms-reset');
    if (!result.hits.length) {
      $('ms-none-title').textContent = `没有找到写到「${query}」的章节`;
      elsewhere.hidden = true;
      reset.hidden = true;
      $('ms-none-hint').textContent = '英文和数字按整词匹配，可以检查拼写，或者只写词的开头几个字母。正文以英文和日文为主，'
        + '中文词多半只命中中规、台规说明书；换成英文或日文术语再搜。';
      return;
    }
    const scope = [state.region !== ALL ? state.region : '', state.cat !== ALL ? config.categories[state.cat] : '',
                   state.lang !== ALL ? code(state.lang) : ''].filter(Boolean).join(' · ');
    $('ms-none-title').textContent = `当前筛选（${scope}）下没有写到「${query}」的章节`;
    const counts = S.facets(result.hits, {region: ALL, cat: ALL, lang: ALL}).region;
    const where = config.regions.filter(region => counts[region]).map(region => `${region} ${counts[region]}`).join('、');
    elsewhere.textContent = `去掉筛选后有 ${counts[ALL]} 份说明书写到（${where}）。`;
    elsewhere.hidden = false;
    reset.hidden = false;
    const only = state.region !== ALL ? S.languagesOf(rows, state.region) : [];
    $('ms-none-hint').textContent = only.length === 1
      ? `${state.region} 的说明书只有 ${code(only[0])} 版本，可以换成这种语言的术语再搜。` : '';
  }

  function render() {
    const query = state.q.trim();
    $('ms-clear').hidden = !input.value;
    const results = $('search-results');
    results.replaceChildren();
    $('ms-start').hidden = Boolean(query);
    if (!query) {
      ['ms-filters', 'ms-summary', 'ms-more', 'ms-none'].forEach(id => { $(id).hidden = true; });
      return;
    }
    const result = S.search(rows, query, cache);
    const grouped = S.group(result.hits, state, config);
    $('ms-filters').hidden = !result.hits.length;
    renderFilters(S.facets(result.hits, state));
    $('ms-none').hidden = grouped.products.length > 0;
    $('ms-summary').hidden = !grouped.products.length;
    if (!grouped.products.length) {
      $('ms-more').hidden = true;
      renderNone(query, result);
      return;
    }
    renderSummary(query, grouped);
    grouped.products.slice(0, limit).forEach(item => results.append(productCard(item, result.matchers)));
    const left = grouped.products.length - limit;
    $('ms-more').hidden = left <= 0;
    $('ms-more').textContent = `显示更多产品（还有 ${left} 款）`;
  }
  function update(now) {
    clearTimeout(timer);
    const run = () => {
      state.q = input.value;
      limit = S.PAGE;
      render();
      try {
        window.history.replaceState(null, '', `${window.location.pathname}${S.writeState(state)}`);
      } catch (error) { /* a sandboxed frame may refuse; the page still works */ }
    };
    if (now) run(); else timer = setTimeout(run, 150);
  }

  input.addEventListener('input', () => update(false));
  $('ms-form').addEventListener('submit', event => { event.preventDefault(); update(true); });
  $('ms-clear').addEventListener('click', () => { input.value = ''; update(true); input.focus(); });
  regionButtons.forEach(button => button.addEventListener('click', () => { state.region = button.dataset.region; update(true); }));
  categoryButtons.forEach(button => button.addEventListener('click', () => {
    state.cat = state.cat === button.dataset.cat ? ALL : button.dataset.cat;
    update(true);
  }));
  languageSelect.addEventListener('change', () => { state.lang = languageSelect.value; update(true); });
  $('ms-reset').addEventListener('click', () => { state.region = ALL; state.cat = ALL; state.lang = ALL; update(true); });
  $('ms-more').addEventListener('click', () => {
    limit += S.PAGE;
    render();
  });

  input.value = state.q;
  status.hidden = true;
  renderCoverage();
  renderExamples();
  render();
})();
