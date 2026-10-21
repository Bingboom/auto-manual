/* Progressive local filtering; events, sources, appendices and revisions are server-rendered. */
(() => {
  "use strict";
  const matches = (entry, filters) => (
    (filters.market === "all" || entry.market === filters.market)
    && (filters.status === "all" || entry.status === filters.status)
    && (filters.review === "all" || entry.review === filters.review)
    && filters.search.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean)
      .every(word => entry.text.toLocaleLowerCase().includes(word))
  );
  const hashId = hash => {
    try { return decodeURIComponent(hash.replace(/^#/, "")); }
    catch { return ""; }
  };
  globalThis.ProductResearchFilters = {matches, hashId};
  if (typeof document === "undefined") return;
  const controls = document.getElementById("research-filters");
  if (!controls) return;
  const market = document.getElementById("research-market");
  const status = document.getElementById("research-status");
  const review = document.getElementById("research-review");
  const search = document.getElementById("research-search");
  const count = document.getElementById("research-count");
  const reset = document.getElementById("research-reset");
  const empty = document.getElementById("research-empty");
  const entries = [...document.querySelectorAll(".research-event")].map(element => ({
    element, market: element.dataset.market, status: element.dataset.status,
    review: element.dataset.review, text: element.textContent,
  }));
  const apply = () => {
    const filters = {market: market.value, status: status.value, review: review.value, search: search.value};
    let visible = 0;
    entries.forEach(entry => {
      const show = matches(entry, filters);
      entry.element.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = `${visible} 个外部事件 / 共 ${entries.length} 个`;
    empty.hidden = visible !== 0;
    reset.hidden = market.value === "all" && status.value === "all" && review.value === "all" && !search.value;
  };
  const clear = () => {
    market.value = "all";
    status.value = "all";
    review.value = "all";
    search.value = "";
    apply();
  };
  const revealHash = () => {
    const target = document.getElementById(hashId(location.hash));
    const entry = target && target.closest(".research-event");
    if (!entry) return;
    if (entry.hidden) clear();
    let details = target.closest("details");
    while (details) {
      details.open = true;
      details = details.parentElement && details.parentElement.closest("details");
    }
    target.scrollIntoView({block: "start"});
  };
  market.addEventListener("change", apply);
  status.addEventListener("change", apply);
  review.addEventListener("change", apply);
  search.addEventListener("input", apply);
  reset.addEventListener("click", clear);
  document.getElementById("research-empty-reset").addEventListener("click", () => {
    clear();
    search.focus();
  });
  window.addEventListener("hashchange", revealHash);
  controls.hidden = false;
  apply();
  revealHash();
})();
