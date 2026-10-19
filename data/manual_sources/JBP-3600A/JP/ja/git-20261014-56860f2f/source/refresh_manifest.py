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
SHARED = REPO / "docs/renderers/web/assets/shared/symbols"
NORMALIZATIONS = [
    "Production sheet: the twelve 130x185 mm panels are read as pages in panel-local points; panel 1 (cover), "
    "panel 2 (contents) and the sheet's frame grid, title block, revision table and production notes are "
    "classified and excluded (source/ja/coverage.json).",
    "Shared Manual IR: content.json is replayed through the shared flow renderer and shared components "
    "(callout strip, warning lockup, reference figure, inbox, warranty lead and sections).",
    "Print line breaks: at a Japanese junction a wrapped line joins without a space; a line the print ended at "
    "least one em short after closing punctuation, or three ems short anywhere, keeps its line break "
    "(logged in source/ja/coverage.json).",
    "Print weights: bold print runs stay strong; headings keep the print's band levels (chapter bands h2, "
    "sub-bands and bulleted subheads h3).",
    "Lists: ・ bullets and numbered print items become unordered or ordered lists; ※ and * notes stay printed "
    "paragraphs; the 保証内容 numbered subheads stay bold paragraphs, as printed.",
    "Tables keep the print's structure; only the troubleshooting table has a printed header row.",
    "LiFePO4 keeps the print's subscript 4.",
    "Two visible marks drawn as outlines (UN38.3, the ■ before the p03 notice) are restored from "
    "source/text-recovery.json; heading disc markers and pills are left to the shared heading style.",
    "Labelled figures are text-free art (printed label lines removed with the redact_text operator, 4x raster) "
    "with those lines as live Japanese copy on their print positions; other artwork words stay in the art; "
    "no figure carries a visible caption.",
    "Troubleshooting uses the shared troubleshooting table (JBP-2000B reference); tables the shared components "
    "would change (signal, LCD, symbols, specifications) stay native grids, as printed.",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh():
    destination = SOURCE / "source_manifest.json"
    manifest = json.loads(destination.read_text())
    manifest["normalizations"] = NORMALIZATIONS
    manifest["validation_boundary"]["native_body"] = [
        "word coverage of the whole sheet: panels 1-12 and the production metadata (source/ja/coverage.json)",
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
    for record in json.loads((SOURCE / "source/figures.json").read_text()):
        if record["acquisition"]["kind"] == "reuse":  # reused shared and EU artwork stays pinned
            dependencies.add(REPO / record["acquisition"]["from"])
    manifest["repo_inputs"] = [{"path": p.relative_to(REPO).as_posix(), "size": p.stat().st_size,
                                "sha256": digest(p)} for p in sorted(dependencies)]
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(
        destination, SOURCE / "source/__pycache__", SOURCE / "__pycache__")))
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
