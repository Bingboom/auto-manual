(function () {
  function normalizeLabelText(text) {
    return (text || "")
      .replace(/\s+/g, " ")
      .trim()
      .toUpperCase();
  }

  function prefaceLanguageForLabel(label) {
    const normalized = normalizeLabelText(label);
    if (normalized === "IMPORTANT") return "en";
    if (normalized === "FR IMPORTANT") return "fr";
    if (normalized === "ES IMPORTANTE") return "es";
    return "";
  }

  function isPrefaceLabelParagraph(node) {
    if (!node || node.tagName !== "P") {
      return false;
    }
    const children = Array.from(node.children);
    if (children.length !== 1 || children[0].tagName !== "STRONG") {
      return false;
    }
    return Boolean(prefaceLanguageForLabel(children[0].textContent || ""));
  }

  function initPrefaceLayout() {
    const main = document.querySelector("#furo-main-content");
    if (!main || main.querySelector(".hb-preface")) {
      return;
    }

    const leadingNodes = [];
    for (const child of Array.from(main.children)) {
      if (child.classList && child.classList.contains("hb-safety")) {
        break;
      }
      if (child.tagName !== "P") {
        return;
      }
      leadingNodes.push(child);
    }

    if (!leadingNodes.length || !isPrefaceLabelParagraph(leadingNodes[0])) {
      return;
    }

    const preface = document.createElement("section");
    preface.className = "hb-preface";
    preface.setAttribute("aria-label", "Important notice");

    let currentBlock = null;
    let currentBody = null;

    for (const node of leadingNodes) {
      if (isPrefaceLabelParagraph(node)) {
        const label = normalizeLabelText(node.textContent || "");
        const block = document.createElement("section");
        block.className = "hb-preface__block";
        block.dataset.lang = prefaceLanguageForLabel(label);

        const eyebrow = document.createElement("p");
        eyebrow.className = "hb-preface__eyebrow";
        eyebrow.textContent = label;

        const body = document.createElement("div");
        body.className = "hb-preface__body";

        block.appendChild(eyebrow);
        block.appendChild(body);
        preface.appendChild(block);

        currentBlock = block;
        currentBody = body;
        node.remove();
        continue;
      }

      if (!currentBlock || !currentBody) {
        continue;
      }

      if ((node.textContent || "").trim().startsWith("*")) {
        node.classList.add("hb-preface__note");
      }
      currentBody.appendChild(node);
    }

    main.insertBefore(preface, main.firstChild);
  }

  function normalizeHeadingText(text) {
    return (text || "")
      .replace(/\s+/g, " ")
      .replace(/\s*¶\s*$/, "")
      .trim();
  }

  function headingLevel(node) {
    if (!node) return 0;
    if (node.tagName === "H1") return 1;
    if (node.tagName === "H2") return 2;
    return 0;
  }

  function ensureHeadingTarget(node) {
    const section = node.closest("section[id]");
    if (section && section.id) {
      return section.id;
    }

    if (node.id) {
      return node.id;
    }

    const text = normalizeHeadingText(node.textContent || "");
    if (!text) {
      return "";
    }

    const slug = text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");

    if (!slug) {
      return "";
    }

    node.id = slug;
    return slug;
  }

  function initManualSidebar(manualMode) {
    const main = document.querySelector("#furo-main-content");
    const sidebarTree = document.querySelector(".sidebar-tree");
    const sidebarDrawer = document.querySelector(".sidebar-drawer");
    if (!main || !sidebarTree || !sidebarDrawer) {
      return;
    }
    if (sidebarTree.querySelector(".hb-manual-toc")) {
      return;
    }

    const headings = Array.from(main.querySelectorAll("h1, h2"))
      .filter((node) => !node.closest(".hb-preface"))
      .map((node) => ({
        node,
        text: normalizeHeadingText(node.textContent || ""),
        level: headingLevel(node),
      }))
      .filter((item) => item.text && item.level > 0);

    if (!headings.length) {
      sidebarDrawer.classList.add("is-empty");
      return;
    }

    const brand = document.querySelector(".sidebar-brand-text");
    if (manualMode && brand) {
      brand.textContent = "Contents";
    }

    sidebarTree.innerHTML = "";
    const list = document.createElement("ul");
    list.className = manualMode ? "hb-manual-toc" : "current hb-manual-toc";

    for (const item of headings) {
      const targetId = ensureHeadingTarget(item.node);
      if (!targetId) {
        continue;
      }

      const li = document.createElement("li");
      const furoLevel = item.level === 1 ? "toctree-l1" : "toctree-l2";
      li.className = `${manualMode ? "" : `${furoLevel} `}hb-manual-toc__item is-level-${item.level}`.trim();

      const link = document.createElement("a");
      link.className = `${manualMode ? "" : "reference internal "}hb-manual-toc__link`.trim();
      link.href = `#${targetId}`;
      link.textContent = item.text;

      li.appendChild(link);
      list.appendChild(li);
    }

    sidebarTree.appendChild(list);
  }

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
    const manualMode = Boolean(document.body && document.body.classList.contains("hb-manual-switcher-body"));
    if (manualMode) {
      initPrefaceLayout();
    }
    initManualSidebar(manualMode);
    document.querySelectorAll(".hb-manual-switcher").forEach(initSwitcher);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
