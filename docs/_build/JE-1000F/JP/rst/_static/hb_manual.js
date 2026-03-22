(function () {
  function setActiveRegion(root, region) {
    const buttons = root.querySelectorAll("[data-hb-region-button]");
    const groups = root.querySelectorAll("[data-hb-region-group]");

    buttons.forEach((button) => {
      const active = button.getAttribute("data-hb-region-button") === region;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });

    groups.forEach((group) => {
      const active = group.getAttribute("data-hb-region-group") === region;
      group.classList.toggle("is-active", active);
    });
  }

  function initSwitcher(root) {
    const buttons = root.querySelectorAll("[data-hb-region-button]");
    if (!buttons.length) {
      return;
    }

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const region = button.getAttribute("data-hb-region-button");
        if (!region) {
          return;
        }
        setActiveRegion(root, region);
      });
    });

    root.setAttribute("data-js-ready", "true");
    const initialRegion = root.getAttribute("data-current-region") || buttons[0].getAttribute("data-hb-region-button") || "";
    setActiveRegion(root, initialRegion);
  }

  function initAll() {
    document.querySelectorAll(".hb-manual-switcher").forEach(initSwitcher);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
