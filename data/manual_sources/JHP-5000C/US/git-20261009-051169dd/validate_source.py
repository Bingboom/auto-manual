"""Validate native copy in the final Web body and frozen artwork/table bindings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    value = unicodedata.normalize("NFC", value).casefold()
    for old, new in LIGATURES.items():
        value = value.replace(old, new)
    return re.sub(r"\W", "", value)


def components(content):
    def walk(node):
        if node.get("kind") == "component":
            yield node["component_spec"]
        for child in node.get("children", []):
            yield from walk(child)
    for chapter in content["chapters"]:
        for node in chapter["nodes"]:
            yield from walk(node)


def validate(language, output):
    filename = f"manual_jhp5000c_us_{language}"
    rendered = output / (filename + ".html")
    is_html = rendered.is_file()
    if not is_html:
        rendered = output / (filename + ".md")
    soup = BeautifulSoup(rendered.read_text(), "html.parser")
    main = soup.select_one("[role=main]") if is_html else soup
    if main is None:
        raise ValueError("missing rendered manual body")
    # Semantic/ARIA attributes and hidden source carriers cannot pay visible-copy coverage.
    for hidden in main.select('[hidden], [aria-hidden="true"], .hb-app-download-semantic'):
        hidden.decompose()
    corpus = normalized(main.get_text(" "))
    ledger = json.loads((PACKAGE / f"source/{language}/coverage.json").read_text())
    content = json.loads((PACKAGE / f"source/{language}/content.json").read_text())
    failures = []
    if any(not h.get_text(strip=True) for h in main.select('h1,h2,h3')):
        failures.append('empty visible heading')
    covered = 0
    if ledger["unmapped"]:
        failures.append("unclassified native words")
    for selection in ledger["selections"]:
        if selection["purpose"] != "live-copy":
            continue
        for line in selection["raw"].splitlines():
            value = re.sub(r"^\s*\d+\.\s+", "", line)
            token = normalized(value)
            if len(token) < 3:
                continue
            if token not in corpus:
                failures.append({"page": selection["page"], "line": line})
            else:
                covered += 1
    specs = list(components(content))
    tables = main.select(".hb-spec-table")
    spec_specs = [s for s in specs if s["component_id"] == "HB-TABLE-SPEC"]
    if len(tables) != 12 or len(spec_specs) != 12:
        failures.append("twelve native specification grids missing")
    for spec, table in zip(spec_specs, tables, strict=True):
        groups = next(s["content"] for s in spec["slots"] if s["role"] == "rows")
        expected = [(normalized(g["label"]), normalized(v["text"]))
                    for g in groups for v in g["values"]]
        actual = [(normalized(r.find(["td", "th"]).get_text(" ")),
                   normalized(r.find_all(["td", "th"])[-1].get_text(" ")))
                  for r in table.select("tbody > tr")]
        if expected != actual:
            failures.append("source specification fields/values changed")
    lcd = main.select_one('[data-component-id="HB-TABLE-LCD-ICON"]')
    if lcd is None or len(lcd.select("tbody > tr")) != 26:
        failures.append("26 native LCD glossary entries missing")
    fcc = main.select_one('[data-component-id="HB-SPECIAL-FCC"]')
    if fcc is None or len(fcc.select("li")) != 4:
        failures.append("FCC four measures missing")
    app_steps = [p for p in main.select("p")
                 if not p.find_parent("figure") and re.match(r"^2\.[1-5]\s", p.get_text(" ", strip=True))]
    if [p.get_text(" ", strip=True)[:3] for p in app_steps] != [f"2.{i}" for i in range(1, 6)]:
        failures.append("App add-device steps 2.1–2.5 missing or reordered")
    plus = app_steps[0].select(".native-inline-plus") if app_steps else []
    if len(plus) != 1 or plus[0].get_text(strip=True) != "+":
        failures.append("App 2.1 editable plus button missing")
    figures = main.select('[data-component-id="HB-SPECIAL-REFERENCE-FIGURE"]')
    expected_labels = sum(len(s["content"]) for spec in specs
                          if spec["component_id"] == "HB-SPECIAL-REFERENCE-FIGURE"
                          for s in spec["slots"] if s["role"] == "captions")
    if len(figures) != 27 or len(main.select(".hb-reference-live-label")) != expected_labels:
        failures.append("figure/live-label inventory changed")
    decisions = json.loads((PACKAGE / "source/asset_decisions.json").read_text())
    rejected = {candidate["sha256"] for d in decisions
                for candidate in d.get("rejected_candidates", [])
                if candidate["status"].startswith("superseded-do-not-reuse")}
    for image in main.find_all("img"):
        path = output / str(image.get("src", ""))
        original = PACKAGE / "assets" / path.name
        if not path.is_file() or not original.is_file() or digest(path) != digest(original):
            failures.append("missing or changed consumed asset: " + str(path))
        elif digest(path) in rejected:
            failures.append("rejected source-specific glyph reused: " + str(path))
    prefix = language.upper() + " "
    title = main.select_one("h1.hb-preface-heading")
    if title is None or not title.get_text(" ", strip=True).startswith(prefix):
        failures.append("outlined native language badge missing")
    if is_html:
        ids = [e["id"] for e in main.select("[id]")]
        if len(ids) != len(set(ids)):
            failures.append("duplicate chapter/navigation IDs")
        for c in content["chapters"]:
            if len(main.select('#native-' + c["id"])) != 1:
                failures.append("chapter anchor missing: " + c["id"])
    if failures:
        raise ValueError(json.dumps(failures, ensure_ascii=False, indent=2))
    return {"language": language, "visible_native_lines": covered,
            "chapters": len(content["chapters"]), "figures": len(figures),
            "live_figure_labels": expected_labels, "lcd_entries": 26, "spec_rows": [len(t.select("tbody > tr")) for t in tables],
            "app_steps": len(app_steps), "editable_app_plus": len(plus),
            "unmapped_words": 0, "failures": []}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=["en", "fr", "es"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.language, args.output), indent=2))
