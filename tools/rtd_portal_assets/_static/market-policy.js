/* Local filtering only; policy text and original evidence remain readable without JS. */
(() => {
  "use strict";
  const controls = document.getElementById("policy-filters");
  if (!controls) return;
  const country = document.getElementById("policy-country");
  const status = document.getElementById("policy-status");
  const search = document.getElementById("policy-search");
  const count = document.getElementById("policy-count");
  const reset = document.getElementById("policy-reset");
  const empty = document.getElementById("policy-empty");
  const buttons = [...controls.querySelectorAll("[data-tag]")];
  const entries = [...document.querySelectorAll(".policy-item")].map(element => ({
    element,
    country: element.dataset.country,
    status: element.dataset.status,
    tags: JSON.parse(element.dataset.tags),
    text: element.textContent.toLocaleLowerCase(),
  }));
  let tag = "all";
  const apply = () => {
    const words = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let visible = 0;
    entries.forEach(entry => {
      const show = (country.value === "all" || country.value === entry.country)
        && (status.value === "all" || status.value === entry.status)
        && (tag === "all" || entry.tags.includes(tag))
        && words.every(word => entry.text.includes(word));
      entry.element.hidden = !show;
      if (show) visible += 1;
    });
    buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.tag === tag)));
    count.textContent = `${visible} 条资料 / 共 ${entries.length} 条`;
    reset.hidden = country.value === "all" && status.value === "all" && tag === "all" && !search.value;
    empty.hidden = visible !== 0;
  };
  const clear = () => {
    country.value = "all";
    status.value = "all";
    search.value = "";
    tag = "all";
    apply();
  };
  const revealHash = () => {
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
    catch { return; }
    const entry = target && target.closest(".policy-item");
    if (entry && entry.hidden) {
      clear();
      target.scrollIntoView({block: "start"});
    }
  };
  country.addEventListener("change", apply);
  status.addEventListener("change", apply);
  search.addEventListener("input", apply);
  buttons.forEach(button => button.addEventListener("click", () => {
    tag = button.dataset.tag;
    apply();
  }));
  reset.addEventListener("click", clear);
  document.getElementById("policy-empty-reset").addEventListener("click", clear);
  window.addEventListener("hashchange", revealHash);
  controls.hidden = false;
  apply();
  revealHash();
})();
