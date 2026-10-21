/* Progressive local filtering; every event row and its details are server-rendered. */
(() => {
  "use strict";
  const FIELDS = ["market", "status", "review"];
  const matches = (entry, filters) => (
    (filters.market === "all" || entry.market === filters.market)
    && (filters.status === "all" || entry.status === filters.status)
    && (filters.review === "all" || entry.review === filters.review)
    && filters.search.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean)
      .every(word => entry.text.toLocaleLowerCase().includes(word))
  );
  // A quick tile is pressed while the filters are exactly its own condition.
  const pressed = (tile, filters) => (
    !filters.search.trim()
    && FIELDS.every(key => key === tile.field || filters[key] === "all")
    && (tile.field === "all" || filters[tile.field] === tile.value)
  );
  const hashId = hash => {
    try { return decodeURIComponent(hash.replace(/^#/, "")); }
    catch { return ""; }
  };
  globalThis.ProductResearchFilters = {matches, pressed, hashId};
  if (typeof document === "undefined") return;
  const controls = document.getElementById("research-filters");
  if (!controls) return;
  const selects = {
    market: document.getElementById("research-market"),
    status: document.getElementById("research-status"),
    review: document.getElementById("research-review"),
  };
  const search = document.getElementById("research-search");
  const count = document.getElementById("research-count");
  const reset = document.getElementById("research-reset");
  const empty = document.getElementById("research-empty");
  const entries = [...document.querySelectorAll(".research-event")].map(element => ({
    element, market: element.dataset.market, status: element.dataset.status,
    review: element.dataset.review, text: element.textContent,
  }));
  const tiles = [...document.querySelectorAll("[data-quick-field]")].map(element => ({
    element, field: element.dataset.quickField, value: element.dataset.quickValue || "all",
  }));
  const current = () => ({
    market: selects.market.value, status: selects.status.value, review: selects.review.value, search: search.value,
  });
  const apply = () => {
    const filters = current();
    let visible = 0;
    entries.forEach(entry => {
      const show = matches(entry, filters);
      entry.element.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = `${visible} 个外部事件 / 共 ${entries.length} 个`;
    empty.hidden = visible !== 0;
    reset.hidden = FIELDS.every(key => filters[key] === "all") && !filters.search;
    tiles.forEach(tile => tile.element.setAttribute("aria-pressed", String(pressed(tile, filters))));
  };
  const clear = () => {
    FIELDS.forEach(key => { selects[key].value = "all"; });
    search.value = "";
    apply();
  };
  const revealHash = () => {
    const target = document.getElementById(hashId(location.hash));
    const entry = target && target.closest(".research-event");
    if (!entry) return;
    if (entry.hidden) clear();
    const row = entry.querySelector("details.event-entry");
    if (row) row.open = true;
    let details = target.closest("details");
    while (details) {
      details.open = true;
      details = details.parentElement && details.parentElement.closest("details");
    }
    target.scrollIntoView({block: "start"});
  };
  FIELDS.forEach(key => selects[key].addEventListener("change", apply));
  search.addEventListener("input", apply);
  reset.addEventListener("click", clear);
  tiles.forEach(tile => tile.element.addEventListener("click", () => {
    FIELDS.forEach(key => { selects[key].value = "all"; });
    search.value = "";
    if (tile.field !== "all") selects[tile.field].value = tile.value;
    apply();
  }));
  document.getElementById("research-empty-reset").addEventListener("click", () => {
    clear();
    search.focus();
  });
  window.addEventListener("hashchange", revealHash);
  controls.hidden = false;
  apply();
  revealHash();
})();
