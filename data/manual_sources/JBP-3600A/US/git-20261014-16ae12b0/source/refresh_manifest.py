"""Re-inventory this frozen source after a reviewed edit.

Never changes content, art or live data. Keeps the target, original-source and
page records, pins the shared repository inputs the replay depends on, and
keeps any recorded operator acceptance status (the acceptance itself binds the
inputs, so an edit still voids it).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

from tools.web.language_release_evidence import _file_inventory  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
LANGUAGES = ("en", "fr", "es")
OFFSET = {"en": 0, "fr": 8, "es": 16}
SHARED = REPO / "docs/renderers/web/assets/shared/symbols"
NORMALIZATIONS = [
    "Shared Manual IR: content.json is replayed through the shared flow renderer and shared components "
    "(callout strip, symbol signal and icon tables, FCC, in-the-box, reference figure, troubleshooting, "
    "specification tables, warranty lead, years and sections).",
    "Print line breaks: a line the print ended while the next word would still have fitted is kept as a "
    "line break; every other line end is a wrap (logged in source/en/coverage.json).",
    "Print weights: bold runs stay strong; headings keep print case and level.",
    "Lists: only printed bullet marks become a list (EN/ES STORAGE, FR exclusions); unmarked printed "
    "statements stay lines.",
    "Ligatures are expanded (fi, fl, ff); hyphenated line-end splits are rejoined (FR conformé-/ment, "
    "ES comunica-/ciones, completa-/mente), logged in source/<lang>/coverage.json.",
    "Visible lines set as vector outlines (no PDF text layer) are restored from source/text-recovery.json "
    "(EN 48, FR 59, ES 61); their statement starts are reviewed from source pixels.",
    "Artwork words stay in the reviewed figure crops; the figures carry no visible caption.",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh():
    destination = SOURCE / "source_manifest.json"
    manifest = json.loads(destination.read_text())
    manifest["normalizations"] = NORMALIZATIONS
    manifest["validation_boundary"]["native_body"] = [
        "word coverage per printed body: EN PDF 4-11, FR 12-19, ES 20-27 (source/<lang>/coverage.json)",
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
    manifest["symbol_asset_admission"] = {
        "schema_version": "auto-manual-symbol-asset-admission/v1",
        "locales": {language: [{key: {"asset_ref": row["local_path"], "asset_sha256": row.get("sha256")}.get(key, row.get(key))
                                for key in keys} for row in symbols if row["language"] == language]
                    for language in LANGUAGES},
    }
    manifest["target"]["languages"] = list(LANGUAGES)
    manifest["web_roots"] = {language: "web/" + language for language in LANGUAGES}
    manifest["included_pages"] = {language: {
        "physical_pages": list(range(4 + offset, 12 + offset)),
        "printed_pages": [f"{1 + offset:02d}", f"{8 + offset:02d}"]} for language, offset in OFFSET.items()}
    manifest["excluded_pages"] = {"printed_cover": [1], "preface_us_fr_es": [2], "contents": [3], "back_cover": [28]}
    manifest["repo_inputs"] = [{"path": p.relative_to(REPO).as_posix(), "size": p.stat().st_size,
                                "sha256": digest(p)} for p in sorted(dependencies)]
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(
        destination, SOURCE / "source/__pycache__", SOURCE / "__pycache__")))
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
