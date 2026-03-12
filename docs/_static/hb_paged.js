(function () {
    // ===== Helpers =====
    function mmToPx(mm) {
      // 1in = 25.4mm; CSS reference: 96px/in
      return (mm / 25.4) * 96;
    }
  
    // Config (should match hb_paged.css)
    const PAGE_H_MM = 297;      // A4
    const PAGE_MARGIN_MM = 18;  // inner padding in CSS
  
    const pageHeightPx = mmToPx(PAGE_H_MM);
    const marginPx = mmToPx(PAGE_MARGIN_MM);
  
    function createBook() {
      const book = document.createElement("div");
      book.className = "hb-book";
      return book;
    }
  
    function createPage(pageNo) {
      const page = document.createElement("div");
      page.className = "hb-page";
  
      const content = document.createElement("div");
      content.className = "hb-page__content";
  
      const footerLine = document.createElement("div");
      footerLine.className = "hb-page__footerline";
  
      const num = document.createElement("div");
      num.className = "hb-page__num";
      num.textContent = String(pageNo);
  
      page.appendChild(content);
      page.appendChild(footerLine);
      page.appendChild(num);
  
      return { page, content, num };
    }
  
    // ===== Furo main content detection =====
    function getMainContent() {
      // Furo typically: main.content > article
      // Also possible: main#furo-main-content or main#main-content
      const candidates = [
        "main.content article",
        "main.content",
        "main#furo-main-content article",
        "main#furo-main-content",
        "main#main-content article",
        "main#main-content",
        "article[role='main']",
        "article",
        "main",
      ];
  
      for (const sel of candidates) {
        const el = document.querySelector(sel);
        if (el) return el;
      }
      return null;
    }
  
    function isMeaningfulElement(el) {
      // Ignore common "noise" nodes (Furo + Sphinx)
      const ignoreSelectors = [
        // Sphinx anchors / permalinks
        ".headerlink",
        "a.headerlink",
        // Toctree wrappers, sidebars, nav, search, etc.
        ".toctree-wrapper",
        "nav",
        ".sidebar-drawer",
        ".sidebar-container",
        ".toc-drawer",
        ".toc-tree",
        ".toc",
        ".toc-overlay",
        // Furo header/footer wrappers if accidentally inside main
        "header",
        "footer",
        // Theme UI fragments
        ".theme-toggle-container",
        ".theme-toggle",
        ".search",
        ".search-input",
        // Empty containers used by themes
        ".only",
      ];
      if (ignoreSelectors.some((sel) => el.matches && el.matches(sel))) return false;
  
      // Skip hidden elements
      const style = window.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden") return false;
  
      // Skip "empty" elements: no text and no media/structure
      const text = (el.textContent || "").replace(/\s+/g, "").trim();
      const hasMedia =
        el.querySelector &&
        el.querySelector("img,svg,video,canvas,table,pre,code,blockquote,ul,ol,dl");
      if (!text && !hasMedia) return false;
  
      return true;
    }
  
    function flattenNodes(container) {
      // Prefer using children of an article to get “block-level” pagination
      let base = container;
  
      // If container is main.content, it often contains article as first child
      const article = base.querySelector && base.querySelector("article");
      if (article && article !== base) base = article;
  
      // In some pages article has a single wrapper div; unwrap 1 level
      if (base.children && base.children.length === 1 && base.firstElementChild) {
        const onlyChild = base.firstElementChild;
        // Avoid unwrapping if it is clearly meaningful content container
        if (onlyChild.tagName && ["DIV", "SECTION"].includes(onlyChild.tagName)) {
          base = onlyChild;
        }
      }
  
      const out = [];
      for (const n of Array.from(base.childNodes)) {
        if (n.nodeType === Node.TEXT_NODE) {
          if (n.textContent.trim().length > 0) {
            const p = document.createElement("p");
            p.textContent = n.textContent.trim();
            out.push(p);
          }
          continue;
        }
  
        if (n.nodeType === Node.ELEMENT_NODE) {
          const el = n;
          if (!isMeaningfulElement(el)) continue;
          out.push(el);
        }
      }
  
      return out;
    }
  
    function availableHeightPx() {
      return pageHeightPx - marginPx * 2;
    }
  
    function measureOverflow(pageContent) {
      return pageContent.scrollHeight > availableHeightPx() + 1;
    }
  
    function isPageVisiblyEmpty(pageEl) {
      const content = pageEl.querySelector(".hb-page__content");
      if (!content) return true;
  
      const textLen = (content.textContent || "").trim().length;
      const elemCount = content.querySelectorAll("*").length;
  
      // Treat as empty if almost no text and almost no elements
      return textLen < 5 && elemCount < 3;
    }
  
    function renumberPages(book) {
      const nums = book.querySelectorAll(".hb-page__num");
      const total = nums.length;
      nums.forEach((el, idx) => {
        // You can change format here:
        // el.textContent = `Page ${idx + 1} / ${total}`;
        el.textContent = `Page ${idx + 1} / ${total}`;
      });
    }
  
    function paginate() {
      const main = getMainContent();
      if (!main) return;
  
      // Avoid paginating twice
      if (document.querySelector(".hb-book")) return;
  
      const nodes = flattenNodes(main);
      if (!nodes.length) return;
  
      const book = createBook();
      main.parentNode.insertBefore(book, main);
  
      let pageNo = 1;
      let { page, content } = createPage(pageNo);
      book.appendChild(page);
  
      for (const node of nodes) {
        const clone = node.cloneNode(true);
        content.appendChild(clone);
  
        if (measureOverflow(content)) {
          // If the page was empty except this node, keep it anyway (avoid infinite loop)
          content.removeChild(content.lastChild);
  
          pageNo += 1;
          const next = createPage(pageNo);
          page = next.page;
          content = next.content;
          book.appendChild(page);
  
          content.appendChild(clone);
  
          // If single node itself overflows, we accept overflow rather than split inside it.
          // (Advanced splitting can be added later for tables/large blocks.)
        }
      }
  
      // Remove original main content to avoid duplicates
      main.remove();
  
      // Remove leading empty pages (fix "blank first page" issue)
      const pages = Array.from(book.querySelectorAll(".hb-page"));
      while (pages.length > 1 && isPageVisiblyEmpty(pages[0])) {
        pages[0].remove();
        pages.shift();
      }
  
      // Renumber
      renumberPages(book);
    }
  
    // Run after layout (images/fonts can affect heights)
    window.addEventListener("load", () => {
      // Delay to let fonts/images settle
      setTimeout(paginate, 80);
    });
  })();