/* 网页说明书进度 (web_progress.html): the cumulative timeline and the coverage-matrix filters. No network.
   The chart draws one series, the language versions, as a filled step line in the page accent (CSS: .wp-line,
   .wp-area); the totals above it and the tooltip name all three. */
(() => {
  const SVG = "http://www.w3.org/2000/svg";
  const SERIES = [
    { key: "langs", name: "语言版本" },
    { key: "editions", name: "市场版本" },
    { key: "models", name: "型号" },
  ];
  const day = (text) => new Date(text + "T00:00:00Z");
  const label = (date) => `${date.getUTCMonth() + 1}月${date.getUTCDate()}日`;
  const el = (name, attrs, parent) => {
    const node = document.createElementNS(SVG, name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    if (parent) parent.append(node);
    return node;
  };

  function niceMax(value) {
    const step = 10 ** Math.floor(Math.log10(Math.max(1, value)));
    return Math.ceil(value / step) * step || 1;
  }

  function drawTrend(box, rows) {
    const width = box.clientWidth;
    if (!width) return;
    box.querySelectorAll("svg, .wp-tip").forEach((node) => node.remove());
    const height = 210;
    const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": `累计上线的语言版本，截至 ${rows[rows.length - 1].date} 共 ${rows[rows.length - 1].langs} 个` }, box);
    const last = rows[rows.length - 1];
    const top = niceMax(last.langs);
    const ticks = [0, top / 2, top].map(Math.round);
    const measure = (text) => {
      const probe = el("text", {}, svg);
      probe.textContent = text;
      const size = probe.getComputedTextLength();
      probe.remove();
      return size;
    };
    const ml = Math.max(...ticks.map((t) => measure(String(t)))) + 10;
    const mr = 10;
    const mt = 8;
    const mb = 22;
    const x0 = day(rows[0].date).getTime();
    const x1 = Math.max(day(last.date).getTime(), x0 + 86400000);
    const x = (date) => ml + ((day(date).getTime() - x0) / (x1 - x0)) * (width - ml - mr);
    const y = (value) => height - mb - (value / top) * (height - mb - mt);
    ticks.forEach((t) => {
      el("line", { class: t ? "wp-grid" : "wp-base", x1: ml, x2: width - mr, y1: y(t), y2: y(t) }, svg);
      const text = el("text", { x: ml - 8, y: y(t), dy: "0.32em", "text-anchor": "end" }, svg);
      text.textContent = String(t);
    });
    // Date ticks evenly spaced in time, at least 90px apart; the ends anchor to the plot's edges.
    const count = Math.max(2, Math.min(5, Math.floor((width - ml - mr) / 90) + 1));
    for (let i = 0; i < count; i += 1) {
      const at = new Date(x0 + ((x1 - x0) * i) / (count - 1));
      const iso = at.toISOString().slice(0, 10);
      const text = el("text", { x: x(iso), y: height - 4, "text-anchor": i === 0 ? "start" : i === count - 1 ? "end" : "middle" }, svg);
      text.textContent = label(at);
    }
    // A running total holds its value until the next day that adds to it.
    let d = `M${x(rows[0].date)},${y(rows[0].langs)}`;
    for (let i = 1; i < rows.length; i += 1) d += `H${x(rows[i].date)}V${y(rows[i].langs)}`;
    el("path", { class: "wp-area", d: `${d}V${y(0)}H${x(rows[0].date)}Z` }, svg);
    el("path", { class: "wp-line", d }, svg);
    el("circle", { class: "wp-dot", cx: x(last.date), cy: y(last.langs), r: 4.5 }, svg);
    const end = el("text", { class: "wp-end", x: x(last.date) - 10, y: y(last.langs) - 8, "text-anchor": "end" }, svg);
    end.textContent = String(last.langs);
    const tip = document.createElement("div");
    tip.className = "wp-tip";
    tip.hidden = true;
    box.append(tip);
    const rule = el("line", { class: "wp-rule", y1: mt, y2: height - mb, visibility: "hidden" }, svg);
    const hit = el("rect", { x: ml, y: mt, width: Math.max(0, width - ml - mr), height: height - mt - mb, fill: "transparent" }, svg);
    hit.addEventListener("pointermove", (event) => {
      const px = event.clientX - svg.getBoundingClientRect().left;
      const row = rows.reduce((best, r) => (Math.abs(x(r.date) - px) < Math.abs(x(best.date) - px) ? r : best), rows[0]);
      rule.setAttribute("x1", x(row.date));
      rule.setAttribute("x2", x(row.date));
      rule.setAttribute("visibility", "visible");
      tip.replaceChildren();
      const head = document.createElement("b");
      head.textContent = `${label(day(row.date))} · 当天新增 ${row.added} 个语言版本`;
      tip.append(head, ...SERIES.map((s) => {
        const line = document.createElement("div");
        line.textContent = `${s.name} ${row[s.key]}`;
        return line;
      }));
      tip.hidden = false;
      tip.style.left = `${Math.max(0, Math.min(width - tip.offsetWidth, x(row.date) + 10))}px`;
      tip.style.top = `${Math.max(0, y(row.langs) - tip.offsetHeight - 8)}px`;
    });
    hit.addEventListener("pointerleave", () => { tip.hidden = true; rule.setAttribute("visibility", "hidden"); });
  }

  document.querySelectorAll("[data-wp-trend]").forEach((box) => {
    let rows = [];
    try { rows = JSON.parse(box.querySelector('script[type="application/json"]').textContent) || []; } catch (error) { rows = []; }
    if (!rows.length) return;
    // The tab may be hidden at load: draw whenever the box gets (or changes) its width.
    let drawn = 0;
    const redraw = () => { if (box.clientWidth && box.clientWidth !== drawn) { drawn = box.clientWidth; drawTrend(box, rows); } };
    if ("ResizeObserver" in window) new ResizeObserver(redraw).observe(box);
    window.addEventListener("resize", redraw);
    redraw();
  });

  // 覆盖矩阵 (交付物 tab): category chips, search, 只看还有待办, the first rows of each group until 显示全部, and a
  // row's language versions underneath it. Without JavaScript every row shows and no detail opens.
  const table = document.querySelector(".wp-table");
  if (!table) return;
  const FIRST = 5;
  const chips = [...document.querySelectorAll(".wp-cat")];
  const find = document.getElementById("wp-find");
  const open = document.getElementById("wp-gaps");
  const empty = document.getElementById("wp-empty");
  const more = document.getElementById("wp-more");
  const groups = [...table.querySelectorAll("tbody[data-category]")];
  const state = { category: "", all: false };
  const detailOf = (row) => document.getElementById(row.querySelector(".wp-toggle").getAttribute("aria-controls"));
  function filter() {
    const query = (find ? find.value : "").trim().toLowerCase();
    const narrowed = Boolean(state.category || query || (open && open.checked));
    let shown = 0;
    let cut = 0;
    groups.forEach((group) => {
      let rows = 0;
      group.querySelectorAll("tr.wp-row").forEach((row) => {
        const match = (!state.category || group.dataset.category === state.category)
          && (!open || !open.checked || row.dataset.open === "1")
          && (!query || row.dataset.find.includes(query));
        const folded = match && !narrowed && !state.all && Number(row.dataset.rank) > FIRST;
        row.hidden = !match || folded;
        if (folded) cut += 1;
        if (!row.hidden) rows += 1;
        const detail = detailOf(row);
        if (detail) detail.hidden = row.hidden || row.querySelector(".wp-toggle").getAttribute("aria-expanded") !== "true";
      });
      group.hidden = rows === 0;
      shown += rows;
    });
    if (empty) empty.hidden = shown !== 0;
    if (more) more.hidden = cut === 0;
    chips.forEach((chip) => chip.setAttribute("aria-pressed", String(chip.dataset.cat === state.category)));
  }
  function toggle(row) {
    const button = row.querySelector(".wp-toggle");
    const opened = button.getAttribute("aria-expanded") !== "true";
    button.setAttribute("aria-expanded", String(opened));
    row.classList.toggle("is-open", opened);
    const detail = detailOf(row);
    if (detail) detail.hidden = !opened;
  }
  chips.forEach((chip) => chip.addEventListener("click", () => { state.category = chip.dataset.cat; filter(); }));
  if (find) find.addEventListener("input", filter);
  if (open) open.addEventListener("change", filter);
  if (more) more.addEventListener("click", () => { state.all = true; filter(); });
  table.addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    const row = event.target.closest("tr.wp-row");
    if (row) toggle(row);
  });
  filter();
})();
