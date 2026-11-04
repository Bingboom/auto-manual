"""Re-inventory this frozen source after a reviewed edit.

Never changes content, art or live data. Keeps the target, original-source and
page records, pins the shared repository inputs the replay depends on, and
keeps any recorded operator acceptance status (the acceptance itself binds the
inputs, so an edit still voids it).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

from tools.web.language_release_evidence import _file_inventory  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
LANGUAGES = ("ja",)
SHARED = REPO / "docs/renderers/web/assets/shared/symbols"
NORMALIZATIONS = [
    "Outlined PDF: original.pdf has no text layer; every Japanese line is a manual transcription from 300 dpi "
    "renders (500 dpi clips for small or ambiguous glyphs), kept as printed (source/intake.py names the physical "
    "page of each block). No Japanese wording, punctuation or spelling is changed; suspected source errors are "
    "listed in source_manifest.json:source_concerns.",
    "Shared Manual IR: content.json is replayed through the shared flow renderer and shared components. "
    "No package class or inline style (prepared-document shared-style gate).",
    "Print weights: bold print runs stay strong. Printed bullet (・/●/■) and number marks become lists; "
    "nested marks nest under their item. Subscripts stay subscript.",
    "Line ends inside a paragraph are wraps; the print's explicit line breaks inside one block stay line breaks.",
    "Figures are source panels cropped just inside the print's panel frame (the decorative frame is drawn by "
    "the shared theme); Japanese words drawn in the art stay in the art and the alt text carries them. "
    "Notes and cautions the print boxes inside a panel are shared callout strips under the figure.",
    "Pictogram warning grids (警告/注意): each printed row becomes a shared warning/caution callout with the "
    "print's bold title and body; the row pictograms are not repeated per row (JE-1000D JP V2 precedent), their "
    "meanings are carried by the shared symbol table.",
    "Cover and table of contents are not Web content (operator decision for this batch).",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh():
    destination = SOURCE / "source_manifest.json"
    manifest = json.loads(destination.read_text())
    manifest["normalizations"] = NORMALIZATIONS
    manifest["validation_boundary"]["native_body"] = [
        "line-by-line transcription review against 300 dpi renders of the named PDF pages",
        "shared Manual IR validation and replay",
        "cold replay byte parity",
        "strict Sphinx",
        "desktop/tablet/mobile browser",
    ]
    dependencies = {REPO / "tools/markdown_bundle.py", REPO / "tools/build_paths.py", SHARED / "manifest.json"}
    for relative in ["tools/manual_ir", "tools/component_specs", "tools/web", "tools/asset_pipeline",
                     "tools/utils", "docs/renderers/contracts"]:
        dependencies.update(p for p in (REPO / relative).rglob("*")
                            if p.is_file() and p.suffix in {".py", ".css", ".json", ".yaml", ".yml"})
    symbols = json.loads((SOURCE / "source/symbols.json").read_text())
    glyphs = json.loads((SOURCE / "source/glyphs.json").read_text())
    for row in symbols + glyphs:
        if "shared_path" in row:
            dependencies.add(REPO / row["shared_path"])
    figures = json.loads((SOURCE / "source/figures.json").read_text())
    dependencies.update(REPO / g["source"] for g in figures if "source" in g)
    # The shared symbol admission re-reads these source-bound rows at release.
    keys = ("asset_ref", "asset_sha256", "shared_symbol_key", "physical_page", "drawing_indices",
            "glyph_bbox", "caption_bbox", "row_bbox", "caption_text", "caption_sha256", "caption_mode")
    # Admission covers the rows the shared symbol table renders; a mark set outside
    # the table (e.g. the recycling note) is shared bytes but not a symbol-table row.
    tabled = set()

    def collect(item):
        if isinstance(item, dict):
            if item.get("component_id") == "HB-TABLE-SYMBOL-ICON":
                tabled.update(re.findall(r"assets/[A-Za-z0-9_.\-]+", json.dumps(item)))
            for value in item.values():
                collect(value)
        elif isinstance(item, list):
            for value in item:
                collect(value)

    collect(json.loads((SOURCE / "source/ja/content.json").read_text()))
    symbols = [row for row in symbols if row["local_path"] in tabled]
    manifest["symbol_asset_admission"] = {
        "schema_version": "auto-manual-symbol-asset-admission/v1",
        "locales": {language: [{key: {"asset_ref": row["local_path"], "asset_sha256": row.get("sha256")}.get(key, row.get(key))
                                for key in keys} for row in symbols if row["language"] == language]
                    for language in LANGUAGES},
    }
    manifest["target"]["languages"] = list(LANGUAGES)
    manifest["web_roots"] = {language: "web/" + language for language in LANGUAGES}
    manifest["repo_inputs"] = [{"path": p.relative_to(REPO).as_posix(), "size": p.stat().st_size,
                                "sha256": digest(p)} for p in sorted(dependencies)]
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(
        destination, SOURCE / "source/__pycache__", SOURCE / "__pycache__")))
    manifest["pending_source_review"] = (
        ["symbol rows without a shared variant await the operator's decision"]
        if any(row.get("shared_symbol_key") is None for row in symbols) else [])
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
