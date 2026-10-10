"""Rebind the existing frozen-source inventory after an explicitly reviewed edit.

This source-local maintenance command never changes content, art or live data.
It reconstructs native symbol references from the pinned PDF, and fails when
shared-copy hashes do not belong to the current shared catalog.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

import fitz  # noqa: E402
from tools.web.language_release_evidence import _file_inventory  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
SHARED = REPO / "docs/renderers/web/assets/shared/symbols"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(value):
    return "".join(value.split()).replace("ﬁ", "fi").replace("ﬂ", "fl")


def symbols(doc, language, catalog):
    content = json.loads((SOURCE / f"source/{language}/content.json").read_text())
    spec = next(n["component_spec"] for c in content["chapters"] for n in c["nodes"]
                if n.get("component_spec", {}).get("component_id") == "HB-TABLE-SYMBOL-ICON")
    panels = next(s["content"] for s in spec["slots"] if s["role"] == "panels")
    rows = [r for panel in panels for r in panel]
    number = {"en": 5, "fr": 29, "es": 53}[language]
    page = doc[number - 1]
    drawings = page.get_drawings()
    cells = [row.cells for table in page.find_tables().tables[1:3] for row in table.rows[1:]]
    result = []
    for row, (iconcell, captioncell) in zip(rows, cells, strict=True):
        box = fitz.Rect(iconcell) + (0.5,0.5,-0.5,-0.5)
        indices = [i for i, drawing in enumerate(drawings) if box.contains(drawing["rect"])]
        if not indices: raise ValueError("native symbol has no drawings")
        bounds = [drawings[i]["rect"] for i in indices]
        glyph = [min(b.x0 for b in bounds)-.1, min(b.y0 for b in bounds)-.1,
                 max(b.x1 for b in bounds)+.1, max(b.y1 for b in bounds)+.1]
        meaning = row["meaning_text"]
        ref = spec["assets"][row["asset_index"]]["asset_ref"]
        shared = next(a for a in catalog["assets"] if a["sha256"] == digest(SOURCE / ref))
        c = list(fitz.Rect(captioncell) + (0.6,0.6,-0.6,-0.6))
        band = [min(glyph[0],c[0])-1, min(glyph[1],c[1])-1,
                max(glyph[2],c[2])+1, max(glyph[3],c[3])+1]
        pixels = page.get_pixmap(matrix=fitz.Matrix(4,4), clip=fitz.Rect(c), alpha=False)
        result.append({"asset_ref": ref, "asset_sha256": digest(SOURCE/ref),
                       "shared_symbol_key": shared["key"], "physical_page": number,
                       "drawing_indices": indices, "glyph_bbox": glyph, "caption_bbox": c,
                       "row_bbox": band, "caption_text": meaning,
                       "caption_sha256": hashlib.sha256(pixels.tobytes("png")).hexdigest(),
                       "caption_mode": "native-extractable-text"})
    return result


def refresh():
    pdf = SOURCE / "Jackery HomePower 5000 Plus.pdf"
    catalog = json.loads((SHARED / "manifest.json").read_text())
    manifest = {
        "schema_version": "auto-manual-frozen-web-source/v1",
        "target": {"model": "JHP-5000C", "region": "US",
                   "technical_version": "git-20261009-051169dd", "languages": ["en","fr","es"]},
        "original_source": {"filename": pdf.name, "sha256": digest(pdf),
                            "page_count": 76, "printed_version": "unknown"},
        "physical_page_map": {"en": [4, 27], "fr": [28, 51], "es": [52, 75],
                              "language_prefaces": 2, "shared_contacts": 76},
        "web_roots": {l: "web/"+l for l in ["en","fr","es"]},
        "live_bitable_dependency": False, "phase2_enrolled": False,
        "build_py_check_scope": "fixture-backed shared-family regression only; native target bodies use source-local validation",
        "symbol_asset_admission": {"schema_version": "auto-manual-symbol-asset-admission/v1",
                                   "locales": {}},
    }
    with fitz.open(pdf) as doc:
        for language in [l for l in ["en","fr","es"] if (SOURCE/f"source/{l}/content.json").is_file()]:
            manifest["symbol_asset_admission"]["locales"][language] = symbols(doc, language, catalog)
    dependencies = {REPO / "data/asset_recipes/manual_jhp5000c_us_native.json",
                    REPO / "data/asset_recipes/asset-extraction-recipe-v1.schema.json",
                    REPO / "tools/markdown_bundle.py", REPO / "tools/build_paths.py",
                    SHARED / "manifest.json"}
    for relative in ["tools/manual_ir", "tools/component_specs", "tools/web", "tools/asset_pipeline",
                     "tools/utils", "docs/renderers/contracts"]:
        dependencies.update(p for p in (REPO / relative).rglob("*")
                            if p.is_file() and p.suffix in {".py", ".css", ".json", ".yaml", ".yml"})
    decisions = json.loads((SOURCE / "source/asset_decisions.json").read_text())
    for decision in decisions:
        candidate = decision.get("candidate")
        if candidate and (REPO / candidate).is_file():
            dependencies.add(REPO / candidate)
    manifest["repo_inputs"] = [{"path": p.relative_to(REPO).as_posix(), "size": p.stat().st_size,
                                "sha256": digest(p)} for p in sorted(dependencies)]
    destination = SOURCE / "source_manifest.json"
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(destination, SOURCE/"source/__pycache__")))
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
