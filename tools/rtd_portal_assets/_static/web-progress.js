/* 网页说明书进度 (web_progress.html): the cumulative timeline and the coverage-matrix filters. No network. */
(() => {
  const SVG = "http://www.w3.org/2000/svg";
  const SERIES = [
    { key: "langs", name: "语言版本", color: "#b44a0f" },
    { key: "editions", name: "市场版本", color: "#1f5fae" },
    { key: "models", name: "型号", color: "#7d838e" },
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
    const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": "累计上线的语言版本、市场版本和型号" }, box);
    const last = rows[rows.length - 1];
    const top = niceMax(last.langs);
    const ticks = [0, top / 4, top / 2, (3 * top) / 4, top].map(Math.round);
    const measure = (text) => {
      const probe = el("text", {}, svg);
      probe.textContent = text;
      const size = probe.getComputedTextLength();
      probe.remove();
      return size;
    };
    const ends = SERIES.map((s) => ({ ...s, text: `${s.name} ${last[s.key]}` }));
    const ml = Math.max(...ticks.map((t) => measure(String(t)))) + 10;
    const mr = Math.max(...ends.map((e) => measure(e.text))) + 16;
    const mt = 8;
    const mb = 22;
    const x0 = day(rows[0].date).getTime();
    const x1 = Math.max(day(last.date).getTime(), x0 + 86400000);
    const x = (date) => ml + ((day(date).getTime() - x0) / (x1 - x0)) * (width - ml - mr);
    const y = (value) => height - mb - (value / top) * (height - mb - mt);
    ticks.forEach((t) => {
      el("line", { x1: ml, x2: width - mr, y1: y(t), y2: y(t), stroke: "#eef0f3" }, svg);
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
    SERIES.forEach((s) => {
      // A running total holds its value until the next day that adds to it.
      let d = `M${x(rows[0].date)},${y(rows[0][s.key])}`;
      for (let i = 1; i < rows.length; i += 1) d += `H${x(rows[i].date)}V${y(rows[i][s.key])}`;
      el("path", { d, fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
      el("circle", { cx: x(last.date), cy: y(last[s.key]), r: 3, fill: s.color }, svg);
    });
    const placed = ends.map((e) => ({ ...e, y: y(last[e.key]) })).sort((a, b) => a.y - b.y);
    for (let i = 1; i < placed.length; i += 1) placed[i].y = Math.max(placed[i].y, placed[i - 1].y + 15);
    const over = placed[placed.length - 1].y - (height - mb);
    if (over > 0) placed.forEach((p) => { p.y -= over; });
    placed.forEach((p) => {
      const text = el("text", { class: "wp-end", x: width - mr + 8, y: p.y, dy: "0.32em", fill: p.color }, svg);
      text.textContent = p.text;
    });
    const tip = document.createElement("div");
    tip.className = "wp-tip";
    tip.hidden = true;
    box.append(tip);
    const rule = el("line", { y1: mt, y2: height - mb, stroke: "#c4c8cf", visibility: "hidden" }, svg);
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

  const category = document.getElementById("wp-category");
  const open = document.getElementById("wp-gaps");
  const empty = document.getElementById("wp-empty");
  const groups = [...document.querySelectorAll(".wp-table tbody[data-category]")];
  if (!category || !open || !groups.length) return;
  function filter() {
    let shown = 0;
    groups.forEach((group) => {
      let rows = 0;
      group.querySelectorAll("tr[data-open]").forEach((row) => {
        const visible = (!category.value || group.dataset.category === category.value) && (!open.checked || row.dataset.open === "1");
        row.hidden = !visible;
        if (visible) rows += 1;
      });
      group.hidden = rows === 0;
      shown += rows;
    });
    if (empty) empty.hidden = shown !== 0;
  }
  category.addEventListener("change", filter);
  open.addEventListener("change", filter);
})();
