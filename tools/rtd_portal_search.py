"""Build the portal's local keyword index from rendered canonical manuals."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path

from tools.utils.path_utils import static_dir_of


class ManualSections(HTMLParser):
    """Collect visible main content, preserving rendered section anchors."""

    def __init__(self):
        super().__init__()
        self.stack = []
        self.rows = []
        self.title = "Manual overview"
        self.anchor = ""
        self.parts = []
        self.heading = None

    def flush(self):
        text = " ".join(" ".join(self.parts).split())
        if text:
            self.rows.append({"title": self.title, "anchor": self.anchor, "text": text})
        self.parts = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        parent = self.stack[-1] if self.stack else ("", False, False, "")
        main = parent[1] or tag == "main" or values.get("role") == "main"
        skip = parent[2] or tag in {"script", "style", "nav"} or "headerlink" in values.get("class", "").split()
        anchor = values.get("id", parent[3]) if tag == "section" else parent[3]
        if tag not in {"img", "br", "hr", "input", "meta", "link", "source", "wbr", "area", "base", "col", "embed", "param"}:
            self.stack.append((tag, main, skip, anchor))
        if main and not skip and tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.flush()
            self.heading = []
            self.anchor = values.get("id") or anchor

    def handle_endtag(self, tag):
        if self.heading is not None and tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.title = " ".join(" ".join(self.heading).split())
            self.heading = None
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.stack and self.stack[-1][1] and not self.stack[-1][2]:
            if self.heading is not None:
                self.heading.append(data)
            else:
                self.parts.append(data)


def write_search_index(app, exception):
    if exception is not None or app.builder.format != "html":
        return
    from tools.rtd_portal import ASSETS, catalog

    settings = json.loads((ASSETS / "settings.json").read_text(encoding="utf-8"))
    rows = []
    for product in catalog(Path(app.srcdir).resolve(), settings):
        for publication in product["publications"]:
            rendered = Path(app.outdir) / publication["url"]
            parser = ManualSections()
            parser.feed(rendered.read_text(encoding="utf-8"))
            parser.flush()
            lang = publication["lang"] if publication["language_scope"] == "single" else "legacy"
            for section in parser.rows:
                rows.append({
                    **section,
                    "url": publication["url"] + ("#" + section["anchor"] if section["anchor"] else ""),
                    "model": product["model"], "name": product["name"],
                    "region": product["region"], "category": product["category"],
                    "lang": lang, "language": settings["language_labels"].get(lang, "Language scope unverified"),
                    "version": publication.get("version"),
                })
    output = static_dir_of(Path(app.outdir)) / "portal-search-index.js"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("window.manualSearchIndex = " + json.dumps(rows, ensure_ascii=True) + ";\n", encoding="utf-8")
