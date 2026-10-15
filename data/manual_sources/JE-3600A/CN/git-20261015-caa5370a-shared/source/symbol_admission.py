"""Bind every shared symbol-table row of this edition to its row on the printed PDF.

The same file lives in the CN and JP editions. For each HB-TABLE-SYMBOL-ICON row it
finds the printed caption (the row's exact copy, word by word), the glyph drawings to
its left, and the caption pixels, and records them as symbol_asset_admission rows in
source_manifest.json. The shared gate (tools/web/symbol_asset_admission.py) re-derives
the glyph from these drawings and compares it with the shared catalog bytes.

Usage: python3 source/symbol_admission.py [--check WEB_DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

import fitz  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
SHARED = REPO / "docs/renderers/web/assets/shared/symbols"
LANGUAGE = {"CN": "zh", "JP": "ja"}
SCHEMA = "auto-manual-symbol-asset-admission/v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def component_rows(content: dict) -> list[tuple[str, str]]:
    rows = []

    def walk(node):
        if isinstance(node, dict):
            spec = node.get("component_spec")
            if spec and spec["component_id"] == "HB-TABLE-SYMBOL-ICON":
                panels = next(s["content"] for s in spec["slots"] if s["role"] == "panels")
                rows.extend((spec["assets"][item["asset_index"]]["asset_ref"], item["meaning_text"])
                            for panel in panels for item in panel)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(content)
    return rows


def find_caption(doc, meaning: str, start_page: int):
    """The printed lines, top to bottom in one column, whose concatenation is exactly the row copy."""
    target = compact(meaning)
    for number in range(start_page, len(doc) + 1):
        lines = [(fitz.Rect(w[:4]), compact(w[4])) for w in doc[number - 1].get_text("words")]
        for rect, token in lines:
            if not token or not target.startswith(token):
                continue
            chosen, remaining, current = [rect], target[len(token):], rect
            while remaining:
                following = [(r, t) for r, t in lines if t and remaining.startswith(t)
                             and ((abs(r.x0 - rect.x0) < 15 and current.y0 < r.y0 < current.y1 + 40)
                                  or (abs(r.y0 - current.y0) < 2 and 0 <= r.x0 - current.x1 < 6))]
                if not following:
                    break
                r, t = min(following, key=lambda item: (item[0].y0, item[0].x0))
                chosen.append(r)
                remaining = remaining[len(t):]
                current = r
            if remaining:
                # Grid-set lists: walk the block in reading order below the first line.
                chosen, remaining = [rect], target[len(token):]
                for r, t in sorted(lines, key=lambda item: (round(item[0].y0), item[0].x0)):
                    if not remaining or r.y0 > rect.y0 + 250:
                        break
                    if (r.y0 > rect.y0 - 1 and r is not rect and r.x0 >= rect.x0 - 10 and t
                            and remaining.startswith(t) and r not in chosen):
                        chosen.append(r)
                        remaining = remaining[len(t):]
            if not remaining:
                box = fitz.Rect(chosen[0])
                for r in chosen[1:]:
                    box |= r
                return number, box
    raise ValueError(f"printed caption not found: {meaning[:40]}")


def find_glyph(page, caption: fitz.Rect):
    """Drawings left of the caption, vertically within the caption's first lines."""
    drawings = page.get_drawings()
    top, bottom = caption.y0 - 30, caption.y1 + 30
    candidates = [(i, d["rect"]) for i, d in enumerate(drawings)
                  if d["rect"].x1 <= caption.x0 + 0.5 and d["rect"].x0 >= caption.x0 - 45
                  and d["rect"].y0 >= top and d["rect"].y1 <= bottom
                  and 2 < d["rect"].width < 40 and 2 < d["rect"].height < 40]
    if not candidates:
        candidates = [(i, d["rect"]) for i, d in enumerate(drawings)
                      if d["rect"].x1 <= caption.x0 + 0.5 and d["rect"].x0 >= caption.x0 - 45
                      and d["rect"].y0 >= top and d["rect"].y1 <= bottom]
    if not candidates:
        raise ValueError("no glyph drawings beside caption")
    # The glyph is the cluster nearest the caption's vertical centre.
    centre = (caption.y0 + caption.y1) / 2
    anchor = min(candidates, key=lambda c: abs((c[1].y0 + c[1].y1) / 2 - centre))[1]
    cluster = fitz.Rect(anchor)
    grown = True
    chosen = []
    while grown:
        grown = False
        for index, rect in candidates:
            if index in chosen:
                continue
            if fitz.Rect(cluster.x0 - 1, cluster.y0 - 1, cluster.x1 + 1, cluster.y1 + 1).intersects(rect) \
                    or cluster.contains(rect):
                chosen.append(index)
                cluster |= rect
                grown = True
    # The gate re-derives the glyph from every drawing inside its bounds: select them all.
    box = fitz.Rect(cluster.x0 - .1, cluster.y0 - .1, cluster.x1 + .1, cluster.y1 + .1)
    indices = sorted(i for i, d in enumerate(drawings) if box.contains(d["rect"]))
    return indices, [box.x0, box.y0, box.x1, box.y1]


def admission(web: Path) -> list[dict]:
    region = SOURCE.parent.name
    language = LANGUAGE[region]
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    catalog = {a["sha256"]: a["key"] for a in json.loads((SHARED / "manifest.json").read_text())["assets"]}
    content = json.loads((SOURCE / f"source/{language}/content.json").read_text())
    pdf = SOURCE / manifest["original_source"]["filename"]
    rows, page_hint = [], 1
    with fitz.open(pdf) as doc:
        for ref, meaning in component_rows(content):
            asset = web / ref
            key = catalog.get(digest(asset))
            number, caption = find_caption(doc, meaning, page_hint)
            page_hint = number
            page = doc[number - 1]
            indices, glyph = find_glyph(page, caption)
            c = [caption.x0 - .6, caption.y0 - .6, caption.x1 + .6, caption.y1 + .6]
            band = [min(glyph[0], c[0]) - 1, min(glyph[1], c[1]) - 1,
                    max(glyph[2], c[2]) + 1, max(glyph[3], c[3]) + 1]
            pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=fitz.Rect(c), alpha=False)
            rows.append({"asset_ref": ref, "asset_sha256": digest(asset), "shared_symbol_key": key,
                         "physical_page": number, "drawing_indices": indices, "glyph_bbox": glyph,
                         "caption_bbox": c, "row_bbox": band, "caption_text": meaning,
                         "caption_sha256": hashlib.sha256(pixels.tobytes("png")).hexdigest(),
                         "caption_mode": "native-extractable-text"})
    return rows


def audit(rows: list[dict], web: Path) -> list[dict]:
    """Each row through the shared gate's own checks; the result is recorded, not waived."""
    from tools.web.shared_symbol_assets import require_shared_symbol_binding
    from tools.web.symbol_asset_admission import _reference, compare_symbol

    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    report = []
    with fitz.open(SOURCE / manifest["original_source"]["filename"]) as doc:
        for row in rows:
            candidate = web / row["asset_ref"]
            entry = {"asset_ref": row["asset_ref"], "physical_page": row["physical_page"],
                     "caption": row["caption_text"][:24]}
            try:
                require_shared_symbol_binding(row, candidate)
                reference = _reference(doc[row["physical_page"] - 1], row, row["caption_text"])
                entry.update(status="admitted", **compare_symbol(candidate.read_bytes(), candidate.suffix, reference))
            except (ValueError, KeyError) as exc:
                entry.update(status="blocked", reason=str(exc))
            report.append(entry)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("web", type=Path, help="a rebuilt web/<language> directory")
    args = parser.parse_args()
    rows = admission(args.web.resolve())
    report = audit(rows, args.web.resolve())
    (SOURCE / "audit").mkdir(exist_ok=True)
    (SOURCE / "audit/symbol-admission.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    path = SOURCE / "source_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["symbol_asset_admission"] = {"schema_version": SCHEMA,
                                          "locales": {LANGUAGE[SOURCE.parent.name]: rows}}
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "admitted": sum(r["status"] == "admitted" for r in report),
                      "blocked": sum(r["status"] == "blocked" for r in report)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
