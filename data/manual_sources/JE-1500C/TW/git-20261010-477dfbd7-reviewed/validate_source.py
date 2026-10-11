"""Validate native copy in the final Web body and frozen artwork/table bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import re
import unicodedata

from bs4 import BeautifulSoup

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
from tools.rtd.deployment_receipt import _dependencies
from tools.web.symbol_asset_admission import require_symbol_asset_admission

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


def validate(output):
    rendered = output / "manual_je1500c_tw_zh-TW.html"
    is_html = rendered.is_file()
    if not is_html:
        rendered = output / "manual_je1500c_tw_zh-TW.md"
    soup = BeautifulSoup(rendered.read_text(), "html.parser")
    main = soup.select_one("[role=main]") if is_html else soup
    for hidden in main.select(
        '[hidden], [aria-hidden="true"], .hb-app-download-semantic'
    ):
        hidden.decompose()
    corpus = normalized(main.get_text(" "))
    ledger = json.loads((PACKAGE / "source/zh-TW/coverage.json").read_text())
    content = json.loads((PACKAGE / "source/zh-TW/content.json").read_text())
    failures = []
    for decision in json.loads((PACKAGE / "source/asset_decisions.json").read_text()):
        if digest(PACKAGE / decision["final_path"]) == decision.get(
            "prior_candidate_sha256"
        ):
            failures.append(
                "rejected incomplete artwork restored: " + decision["final_path"]
            )
    if ledger["unmapped"]:
        failures.append("unclassified source words")
    covered = 0
    for selection in ledger["selections"]:
        if selection["purpose"] not in ["live-copy", "live-figure-label"]:
            continue
        for line in selection["raw"].splitlines():
            line = line.translate({0xF6BE + i: str(i) for i in range(10)})
            token = normalized(line)
            if not token:
                continue
            if token not in corpus:
                failures.append({"page": selection["page"], "line": line})
            else:
                covered += 1
    specs = list(components(content))
    tables = main.select(".hb-spec-table")
    spec_specs = [s for s in specs if s["component_id"] == "HB-TABLE-SPEC"]
    if len(tables) != 4 or len(spec_specs) != 4:
        failures.append("four native spec grids missing")
    for spec, table in zip(spec_specs, tables, strict=True):
        groups = next(s["content"] for s in spec["slots"] if s["role"] == "rows")
        expected = [
            (normalized(g["label"]), normalized(v["text"]))
            for g in groups
            for v in g["values"]
        ]
        actual = [
            (
                normalized(r.find(["td", "th"]).get_text(" ")),
                normalized(r.find_all(["td", "th"])[-1].get_text(" ")),
            )
            for r in table.select("tbody > tr")
        ]
        if expected != actual:
            failures.append("native spec row/value mismatch")
    for identity, count in [
        ("HB-TABLE-LCD-ICON", 22),
        ("HB-TABLE-SYMBOL-SIGNAL", 4),
        ("HB-TABLE-TROUBLESHOOTING", 10),
    ]:
        table = main.select_one(f'[data-component-id="{identity}"]')
        if table is None or len(table.select("tbody > tr")) != count:
            failures.append(identity + " row inventory mismatch")
    icons = main.select_one('[data-component-id="HB-TABLE-SYMBOL-ICON"]')
    if icons is None or len(icons.select("img")) != 6:
        failures.append("six native symbol/caption pairs missing")

    # Every structured rich-copy field must survive in visible semantic output.
    def strings(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key.endswith("_text") or key == "text":
                    yield str(child)
                elif key != "metadata":
                    yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)

    for spec in specs:
        for value in strings(spec["slots"]):
            if normalized(value) not in corpus:
                failures.append({"component": spec["component_id"], "text": value})
    labels = json.loads((PACKAGE / "source/figure_labels.json").read_text())
    actual_labels = main.select(".hb-reference-live-label")
    if len(actual_labels) != len(labels) or [
        normalized(e.get_text(" ")) for e in actual_labels
    ] != [normalized(r["text"]) for r in labels]:
        failures.append("editable caption inventory/order changed")
    restricted = main.select_one(".native-restricted-table")
    if restricted is None or len(restricted.select("tr")) != 5:
        failures.append("restricted-substances table missing")
    else:
        rows = [
            [v.get_text(strip=True) for v in row.select("td,th")]
            for row in restricted.select("tr")[1:]
        ]
        expected = [
            [name, *(["○"] * 6)]
            for name in ["塑膠外殼", "金屬鐵件", "電路板", "電源線"]
        ]
        expected[2][1] = expected[3][1] = "－"
        if rows != expected:
            failures.append("native restricted substance vector marks changed")
    for token in ["F" + str(i) for i in range(10)] + [
        "2." + str(i) for i in range(1, 6)
    ]:
        if normalized(token) not in corpus:
            failures.append("missing " + token)
    if re.search(r"[\uf6be-\uf6c7]", main.get_text()):
        failures.append("unrecovered PDF digit encoding")
    for image in main.find_all("img"):
        path = output / str(image.get("src", ""))
        original = PACKAGE / "assets" / path.name
        if (
            not path.is_file()
            or not original.is_file()
            or digest(path) != digest(original)
        ):
            failures.append("missing/changed asset: " + str(path))
    if is_html:
        for chapter in content["chapters"]:
            if len(main.select("#native-" + chapter["id"])) != 1:
                failures.append("missing chapter " + chapter["id"])
    plus = main.select(".hb-inline-add-device-icon")
    if len(plus) != 1 or plus[0].get_text(strip=True) != "+":
        failures.append("native App 2.1 editable plus control missing")
    closure = set()
    pending = [rendered.name]
    if is_html:
        while pending:
            name = pending.pop()
            if name in closure:
                continue
            path = output / name
            if not path.is_file():
                failures.append("missing HTML/CSS dependency: " + name)
                continue
            closure.add(name)
            pending.extend(
                _dependencies(name, path.read_bytes(), "https://frozen.local/")
            )
    if failures:
        raise ValueError(json.dumps(failures, ensure_ascii=False, indent=2))
    return {
        "language": "zh-TW",
        "visible_native_lines": covered,
        "chapters": len(content["chapters"]),
        "live_labels": len(labels),
        "spec_rows": [len(t.select("tbody > tr")) for t in tables],
        "unmapped_words": 0,
        "resource_closure": len(closure),
        "editable_app_plus": 1,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-dir", type=Path)
    args = parser.parse_args()
    result = validate(args.output)
    if args.markdown_dir:
        manifest = json.loads((PACKAGE / "source_manifest.json").read_text())
        result["symbol_admission"] = require_symbol_asset_admission(
            args.markdown_dir, PACKAGE, manifest, "zh-TW"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
