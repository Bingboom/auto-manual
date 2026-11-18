(() => {
  // 产品演进时间轴 (tools/rtd_portal_assets/product_timeline.html). Builds the SVG swimlane timeline from escaped JSON
  // using createElementNS / textContent only; exports pure helpers on globalThis.ProductTimeline for unit tests.
  const SVG_NS = "http://www.w3.org/2000/svg";
  const PALETTE = ["#4355d6", "#6f42df", "#0b6bcb", "#c23030", "#96620f", "#0d7a68", "#8b3d7a", "#475569"];
  const TIER_OFFSETS = [-15, -34, 22, 41, -53, 60];
  const LANE_ORDERS = {
    series_portable: ["Pro", "Plus", "Ultra", "标准", "充电宝", "卫士", "PlusV2"],
    capacity: ["5 度电", "3.6 度电", "3 度电", "2 度电", "1.5 – 1.8 度电", "1 – 1.2 度电", "1 度以下", "无容量档（板 / 配件）"],
    market: ["美规 (US)", "日规 (JP)", "欧规 (EU)", "其他市场"],
    category: ["便携储能", "家庭备电", "加电包", "太阳能板", "配件", "其他"]
  };

  function parseYearFrac(dateStr) {
    const parts = String(dateStr || "").split("-").map(Number);
    const y = parts[0] || 2025;
    const m = Math.min(12, Math.max(1, parts[1] || 1));
    const d = Math.min(31, Math.max(1, parts[2] || 15));
    return y + ((m - 1) + (d - 1) / 30.4) / 12;
  }

  function capacityBucket(cap) {
    if (!cap) return "无容量档（板 / 配件）";
    const map = {
      "5度电": "5 度电", "3.6度电": "3.6 度电", "3度电": "3 度电", "2度电": "2 度电",
      "1.8度电": "1.5 – 1.8 度电", "1.5度电": "1.5 – 1.8 度电",
      "1.2度电": "1 – 1.2 度电", "1度电": "1 – 1.2 度电", "1度以下": "1 度以下"
    };
    return map[cap] || cap;
  }

  function approxTextWidth(str) {
    let w = 0;
    const s = String(str || "");
    for (let i = 0; i < s.length; i++) w += s.charCodeAt(i) > 255 ? 12.2 : 6.8;
    return w + 10;
  }

  function selectPoints(products, state) {
    const effectiveMarket = state.yAxis === "market" && state.market === "EARLIEST" ? "ALL_ROWS" : state.market;
    const points = [];
    for (const prod of products || []) {
      if (state.category !== "ALL" && prod.category !== state.category) continue;
      const dated = (prod.markets || []).filter(m => m.date);
      if (!dated.length) continue;
      if (effectiveMarket === "ALL_ROWS") {
        for (const m of dated) points.push({ ...prod, market: m.market, date: m.date, upper: Boolean(m.upper) });
      } else if (effectiveMarket === "EARLIEST") {
        const first = dated[0];
        points.push({ ...prod, market: first.market, date: first.date, upper: Boolean(first.upper) });
      } else {
        const hit = dated.find(m => m.market === effectiveMarket);
        if (hit) points.push({ ...prod, market: hit.market, date: hit.date, upper: Boolean(hit.upper) });
      }
    }
    return points;
  }

  function laneKeyOf(pt, state, labels) {
    if (state.yAxis === "series") return state.category === "ALL" ? `${pt.category} · ${pt.series}` : pt.series;
    if (state.yAxis === "capacity") return capacityBucket(pt.cap);
    if (state.yAxis === "market") {
      if (["US", "JP", "EU"].includes(pt.market)) return `${labels[pt.market] || pt.market} (${pt.market})`;
      return "其他市场";
    }
    return pt.category;
  }

  function labelTextOf(pt, state) {
    const suffix = state.market === "ALL_ROWS" && state.yAxis !== "market" ? ` (${pt.market})` : "";
    if (state.labelMode === "model") return pt.model + suffix;
    if (state.labelMode === "both") return `${pt.short_name} · ${pt.model}${suffix}`;
    return pt.short_name + suffix;
  }

  function packLaneNodes(items, xOf, minX, maxX, state) {
    const sorted = items.slice().sort((a, b) => a.date.localeCompare(b.date) || a.model.localeCompare(b.model));
    const nodes = sorted.map(it => {
      const rx = xOf(parseYearFrac(it.date));
      return { ...it, rawX: rx, x: rx, label: labelTextOf(it, state) };
    });
    const minDotGap = 11.5;
    for (let pass = 0; pass < 4; pass++) {
      for (let i = 1; i < nodes.length; i++) {
        const gap = nodes[i].x - nodes[i - 1].x;
        if (gap < minDotGap) {
          const push = (minDotGap - gap) / 2;
          nodes[i - 1].x = Math.max(minX, nodes[i - 1].x - push);
          nodes[i].x = Math.min(maxX, nodes[i].x + push);
        }
      }
    }
    const tierEnds = TIER_OFFSETS.map(() => -Infinity);
    let minDy = -24;
    let maxDy = 20;
    for (const n of nodes) {
      const w = approxTextWidth(n.label);
      const x1 = n.x - w / 2;
      const x2 = n.x + w / 2;
      let chosen = 0;
      let bestOverlap = Infinity;
      for (let t = 0; t < TIER_OFFSETS.length; t++) {
        if (x1 >= tierEnds[t] + 6) {
          chosen = t;
          break;
        }
        const ov = tierEnds[t] - x1;
        if (ov < bestOverlap) {
          bestOverlap = ov;
          chosen = t;
        }
      }
      n.tier = chosen;
      n.dy = TIER_OFFSETS[chosen];
      tierEnds[chosen] = Math.max(tierEnds[chosen], x2);
      if (n.dy - 14 < minDy) minDy = n.dy - 14;
      if (n.dy + 10 > maxDy) maxDy = n.dy + 10;
    }
    return { nodes, topRoom: Math.max(42, -minDy + 12), botRoom: Math.max(30, maxDy + 12) };
  }

  function svgEl(tag, attrs, text) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) el.setAttribute(k, String(v));
    if (text !== undefined) el.textContent = text;
    return el;
  }

  function htmlEl(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }

  function initTimeline(root, payload) {
    if (!root || !payload || !Array.isArray(payload.products)) return;
    root.hidden = false;

    const itemBase = root.dataset.itemBase || "";
    const compareBase = root.dataset.compareBase || "";
    const labels = payload.labels || {};
    const byModel = new Map(payload.products.map(p => [p.model, p]));

    const state = {
      yAxis: "series",
      category: payload.default_category || "ALL",
      market: "EARLIEST",
      labelMode: "short",
      zoom: 1,
      activeModel: null,
      pinnedModel: null
    };

    const mount = root.querySelector("[data-tl-mount]");
    const statEl = root.querySelector("[data-tl-stat]");
    const crossHint = root.querySelector("[data-tl-cross]");
    const emptyHint = root.querySelector("[data-tl-empty]");
    const detailBox = root.querySelector("[data-tl-detail]");

    function sortLanes(laneMap) {
      let orderRef = [];
      if (state.yAxis === "series" && state.category === "便携储能") orderRef = LANE_ORDERS.series_portable;
      else if (state.yAxis === "capacity") orderRef = LANE_ORDERS.capacity;
      else if (state.yAxis === "market") orderRef = LANE_ORDERS.market;
      else if (state.yAxis === "category") orderRef = LANE_ORDERS.category;

      return Array.from(laneMap.keys()).sort((a, b) => {
        const ia = orderRef.indexOf(a);
        const ib = orderRef.indexOf(b);
        if (ia !== -1 && ib !== -1) return ia - ib;
        if (ia !== -1) return -1;
        if (ib !== -1) return 1;
        const minA = laneMap.get(a).reduce((m, x) => (x.date < m ? x.date : m), "9999");
        const minB = laneMap.get(b).reduce((m, x) => (x.date < m ? x.date : m), "9999");
        return minA.localeCompare(minB);
      });
    }

    function renderInspector(model) {
      if (!model || !byModel.has(model)) {
        emptyHint.hidden = false;
        detailBox.hidden = true;
        detailBox.replaceChildren();
        return;
      }
      const info = byModel.get(model);
      emptyHint.hidden = true;
      detailBox.hidden = false;
      detailBox.replaceChildren();

      const left = htmlEl("div", "tl-ins-main");
      left.appendChild(htmlEl("span", "tl-ins-name", info.short_name));
      left.appendChild(htmlEl("code", "tl-ins-code", info.model));
      const metaParts = [info.category, info.series];
      if (info.cap) metaParts.push(info.cap);
      left.appendChild(htmlEl("span", "tl-ins-meta", metaParts.join(" · ")));
      if (state.pinnedModel === model) {
        left.appendChild(htmlEl("span", "tl-ins-pin", "已固定（再次点击取消）"));
      }

      const mid = htmlEl("div", "tl-ins-markets");
      for (const m of info.markets || []) {
        const pill = htmlEl("span", "tl-mkt-pill");
        pill.appendChild(document.createTextNode((labels[m.market] || m.market) + " "));
        const dateTxt = m.date ? (m.upper ? `不晚于 ${m.date.slice(0, 7)}` : m.date.slice(0, 7)) : "暂无";
        pill.appendChild(htmlEl("em", "", dateTxt));
        mid.appendChild(pill);
      }

      const right = htmlEl("div", "tl-ins-links");
      if (payload.has_profiles && info.page && itemBase.includes("__MODEL__")) {
        const profileLink = htmlEl("a", "", "查看产品档案 →");
        profileLink.href = itemBase.replace("__MODEL__", encodeURIComponent(info.model));
        right.appendChild(profileLink);
      }
      if (compareBase) {
        const cmpLink = htmlEl("a", "", "加入对比");
        cmpLink.href = `${compareBase}?p=${encodeURIComponent(info.model)}`;
        right.appendChild(cmpLink);
      }

      detailBox.append(left, mid, right);
    }

    function applyHighlight(model) {
      const allEls = mount.querySelectorAll("[data-model]");
      const connectorLayer = mount.querySelector("[data-tl-connectors]");
      if (connectorLayer) connectorLayer.replaceChildren();

      if (!model || !byModel.has(model)) {
        allEls.forEach(el => el.classList.remove("tl-dim", "is-active"));
        renderInspector(null);
        return;
      }

      const matchingDots = [];
      allEls.forEach(el => {
        const match = el.getAttribute("data-model") === model;
        el.classList.toggle("tl-dim", !match);
        if (el.classList.contains("tl-dot")) {
          el.classList.toggle("is-active", match);
          if (match) matchingDots.push(el);
        }
      });

      if (matchingDots.length > 1 && connectorLayer) {
        const coords = matchingDots
          .map(d => ({ x: Number(d.getAttribute("cx")), y: Number(d.getAttribute("cy")) }))
          .sort((a, b) => a.x - b.x || a.y - b.y);
        const dPath = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(" ");
        connectorLayer.appendChild(svgEl("path", {
          d: dPath, fill: "none", stroke: "#4355d6", "stroke-width": "1.8", "stroke-dasharray": "4 3"
        }));
      }
      renderInspector(model);
    }

    function render() {
      const points = selectPoints(payload.products, state);
      if (crossHint) crossHint.hidden = !(state.yAxis === "market" || state.market === "ALL_ROWS");
      mount.replaceChildren();

      if (!points.length) {
        mount.appendChild(htmlEl("p", "tl-empty-state", "当前筛选条件下暂无带 SKU 创建时间的机型记录。"));
        if (statEl) statEl.textContent = "0 款机型";
        renderInspector(null);
        return;
      }

      const laneMap = new Map();
      for (const pt of points) {
        const key = laneKeyOf(pt, state, labels);
        if (!laneMap.has(key)) laneMap.set(key, []);
        laneMap.get(key).push(pt);
      }
      const laneKeys = sortLanes(laneMap);

      const minYear = Number(payload.min_year) || 2023;
      const maxYear = Number(payload.max_year) || 2027;
      const startFrac = minYear;
      const endFrac = maxYear + 0.32;
      const leftPad = 152;
      const rightPad = 56;
      const plotW = Math.round(1020 * state.zoom);
      const svgW = leftPad + plotW + rightPad;
      const xOf = frac => leftPad + ((frac - startFrac) / (endFrac - startFrac)) * plotW;

      const topHeaderH = 54;
      let cursorY = topHeaderH;
      const lanes = laneKeys.map((key, idx) => {
        const packed = packLaneNodes(laneMap.get(key), xOf, leftPad + 6, leftPad + plotW - 6, state);
        const laneY = cursorY + packed.topRoom;
        cursorY = laneY + packed.botRoom;
        return { key, color: PALETTE[idx % PALETTE.length], laneY, nodes: packed.nodes };
      });
      const svgH = cursorY + 26;

      const svg = svgEl("svg", {
        class: "tl-svg", width: svgW, height: svgH, viewBox: `0 0 ${svgW} ${svgH}`,
        role: "img", "aria-label": "产品演进时间轴"
      });

      for (let yr = minYear; yr <= maxYear; yr++) {
        const x = xOf(yr).toFixed(1);
        svg.appendChild(svgEl("line", { x1: x, y1: topHeaderH - 12, x2: x, y2: svgH - 16, stroke: "#e6eaf2", "stroke-width": 1 }));
        svg.appendChild(svgEl("text", { x, y: 32, "text-anchor": "middle", fill: "#687387", "font-size": 13, "font-weight": 600 }, String(yr)));
        if (yr < maxYear) {
          const xm = xOf(yr + 0.5).toFixed(1);
          svg.appendChild(svgEl("line", { x1: xm, y1: topHeaderH - 12, x2: xm, y2: svgH - 16, stroke: "#eef1f7", "stroke-width": 1, "stroke-dasharray": "2 4" }));
        }
      }

      for (const lane of lanes) {
        svg.appendChild(svgEl("line", { x1: leftPad, y1: lane.laneY, x2: leftPad + plotW + 18, y2: lane.laneY, stroke: "#e5e9f2", "stroke-width": 1 }));
        svg.appendChild(svgEl("text", { x: leftPad - 18, y: lane.laneY + 4.5, "text-anchor": "end", fill: "#273043", "font-size": 13.5, "font-weight": 600 }, lane.key));
      }

      svg.appendChild(svgEl("g", { "data-tl-connectors": "1" }));

      if (payload.today) {
        const tf = parseYearFrac(payload.today);
        if (tf >= startFrac && tf <= endFrac) {
          const tx = xOf(tf).toFixed(1);
          svg.appendChild(svgEl("text", { x: tx, y: 17, "text-anchor": "middle", fill: "#9c7326", "font-size": 12.5, "font-weight": 600 }, "今天"));
          svg.appendChild(svgEl("line", { x1: tx, y1: 24, x2: tx, y2: svgH - 12, stroke: "#ad8330", "stroke-width": 1.6, "stroke-dasharray": "4.5 4.5" }));
        }
      }

      for (const lane of lanes) {
        for (const n of lane.nodes) {
          const cy = lane.laneY;
          const ly = cy + n.dy;
          if (Math.abs(n.dy) > 24 || Math.abs(n.x - n.rawX) > 3) {
            const endY = n.dy < 0 ? ly + 4 : ly - 11;
            svg.appendChild(svgEl("line", {
              "data-model": n.model, x1: n.x.toFixed(1), y1: cy, x2: n.x.toFixed(1), y2: endY.toFixed(1),
              stroke: lane.color, "stroke-opacity": "0.32", "stroke-width": 1
            }));
          }
          const lbl = svgEl("text", {
            class: "tl-label", "data-model": n.model, x: n.x.toFixed(1), y: ly.toFixed(1),
            "text-anchor": "middle", fill: "#232b3d", "font-size": 12, "font-weight": 600
          }, n.label);
          const circleAttrs = n.upper
            ? { class: "tl-dot", "data-model": n.model, cx: n.x.toFixed(1), cy, r: 6, fill: "#f7f8fc", stroke: lane.color, "stroke-width": 2.4 }
            : { class: "tl-dot", "data-model": n.model, cx: n.x.toFixed(1), cy, r: 6.2, fill: lane.color, stroke: "#ffffff", "stroke-width": 1.4 };
          const dot = svgEl("circle", circleAttrs);
          const mktLabel = labels[n.market] || n.market;
          const dateLabel = n.upper ? `不晚于 ${n.date.slice(0, 7)}` : n.date.slice(0, 7);
          dot.appendChild(svgEl("title", {}, `${n.short_name} (${n.model}) · ${dateLabel} · ${mktLabel}`));

          for (const interactive of [lbl, dot]) {
            interactive.addEventListener("mouseenter", () => {
              state.activeModel = n.model;
              applyHighlight(state.pinnedModel || state.activeModel);
            });
            interactive.addEventListener("mouseleave", () => {
              state.activeModel = null;
              applyHighlight(state.pinnedModel);
            });
            interactive.addEventListener("click", ev => {
              ev.stopPropagation();
              state.pinnedModel = state.pinnedModel === n.model ? null : n.model;
              applyHighlight(state.pinnedModel || state.activeModel);
            });
          }
          svg.append(lbl, dot);
        }
      }

      mount.appendChild(svg);
      const uniqueModels = new Set(points.map(p => p.model)).size;
      if (statEl) statEl.textContent = `${lanes.length} 条泳道 · ${uniqueModels} 款机型（${points.length} 个时间节点）`;
      applyHighlight(state.pinnedModel || state.activeModel);
    }

    function setCategory(cat) {
      state.category = cat;
      root.querySelectorAll("[data-tl-cats] button").forEach(btn => {
        btn.setAttribute("aria-pressed", String(btn.dataset.cat === cat));
      });
    }

    root.querySelectorAll("[data-tl-yaxis] button").forEach(btn => {
      btn.addEventListener("click", () => {
        state.yAxis = btn.dataset.yaxis;
        if (state.yAxis === "category" && state.category !== "ALL" && root.querySelector('[data-tl-cats] button[data-cat="ALL"]')) {
          setCategory("ALL");
        }
        root.querySelectorAll("[data-tl-yaxis] button").forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
        render();
      });
    });

    root.querySelectorAll("[data-tl-cats] button").forEach(btn => {
      btn.addEventListener("click", () => {
        setCategory(btn.dataset.cat);
        render();
      });
    });

    const mktSel = root.querySelector("[data-tl-market]");
    if (mktSel) mktSel.addEventListener("change", () => { state.market = mktSel.value; render(); });
    const lblSel = root.querySelector("[data-tl-label]");
    if (lblSel) lblSel.addEventListener("change", () => { state.labelMode = lblSel.value; render(); });
    const zoomSel = root.querySelector("[data-tl-zoom]");
    if (zoomSel) zoomSel.addEventListener("change", () => { state.zoom = Number(zoomSel.value) || 1; render(); });
    const scrollWrap = root.querySelector("[data-tl-scroll]");
    if (scrollWrap) scrollWrap.addEventListener("click", () => {
      if (state.pinnedModel) { state.pinnedModel = null; applyHighlight(null); }
    });

    render();
  }

  globalThis.ProductTimeline = { parseYearFrac, capacityBucket, selectPoints, packLaneNodes, initTimeline };

  if (typeof document !== "undefined") {
    const appEl = document.querySelector("[data-tl]");
    const dataEl = document.getElementById("tl-data");
    if (appEl && dataEl) {
      try {
        initTimeline(appEl, JSON.parse(dataEl.textContent || "{}"));
      } catch {
        // Leave empty fallback if JSON is malformed.
      }
    }
  }
})();
