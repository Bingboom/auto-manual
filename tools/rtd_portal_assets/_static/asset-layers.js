/* 四类资产 pages (tools/rtd_portal_assets/asset_*.html): the list filters of a layer's 清单.
   A form [data-al-filters] holds selects [data-al-filter=<key>] and an optional [data-al-unfinished] checkbox; the
   rows of the table [data-al-list] carry data-category, data-models, data-regions, data-languages (space-separated),
   data-neutral and data-finished. A row whose models or regions include ALL, or that has no language-specific text,
   matches every model, region or language. Without JavaScript the form stays hidden and every row shows. */
(() => {
  const words = value => (value || "").split(" ").filter(Boolean);

  function matches(row, filters) {
    if (filters.category && row.category !== filters.category) return false;
    if (filters.unfinished && row.finished === "true") return false;
    const models = words(row.models), regions = words(row.regions), languages = words(row.languages);
    if (filters.model && !models.includes(filters.model) && !models.includes("ALL")) return false;
    if (filters.region && !regions.includes(filters.region) && !regions.includes("ALL")) return false;
    if (filters.language && row.neutral !== "true" && !languages.includes(filters.language)
        && !languages.includes("shared") && languages.length) return false;
    return true;
  }

  function bind(form, table, empty) {
    const rows = [...table.querySelectorAll("tbody tr")];
    const selects = [...form.querySelectorAll("[data-al-filter]")];
    const unfinished = form.querySelector("[data-al-unfinished]");
    const count = form.querySelector("[data-al-count]");
    const apply = () => {
      const filters = {unfinished: Boolean(unfinished && unfinished.checked)};
      selects.forEach(select => { filters[select.dataset.alFilter] = select.value; });
      let shown = 0;
      rows.forEach(row => {
        const on = matches(row.dataset, filters);
        row.hidden = !on;
        if (on) shown += 1;
      });
      if (count) count.textContent = `${shown} / ${rows.length} 项`;
      if (empty) empty.hidden = shown > 0;
    };
    selects.forEach(select => select.addEventListener("change", apply));
    if (unfinished) unfinished.addEventListener("change", apply);
    form.addEventListener("submit", event => event.preventDefault());
    form.hidden = false;
    apply();
  }

  const scope = typeof window === "undefined" ? globalThis : window;
  scope.assetLayers = {matches};
  if (typeof document === "undefined") return;
  const form = document.querySelector("[data-al-filters]"), table = document.querySelector("[data-al-list]");
  if (form && table) bind(form, table, document.querySelector("[data-al-empty]"));
})();
