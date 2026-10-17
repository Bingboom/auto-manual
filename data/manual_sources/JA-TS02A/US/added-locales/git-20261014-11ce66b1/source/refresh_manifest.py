"""Re-inventory this frozen source after a reviewed edit.

Never changes content, art or live data. Keeps the target, original-source and page
records, pins the repository inputs the replay and the asset extraction depend on (the
English package's PDF archive parts, its reused artwork and records, and the shared
renderers), and keeps the publication status (an operator acceptance binds the inputs,
so an edit still voids it).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))

from tools.web.language_release_evidence import _file_inventory  # noqa: E402
from tools.web.prepared_style_audit import table_text_sha256  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
SHARED = REPO / "docs/renderers/web/assets/shared/symbols"
# Plain shared tables (class manual-table only) where no shared component fits, by chapter.
TABLE_REASONS = {
    "safety": "Meaning of symbols. HB-TABLE-SYMBOL-ICON admits only shared catalogue symbols; the print's "
              "grounding, caution and electric-shock icons miss the fixed glyph gate against every shared "
              "variant, and the operator chose the print's own vectors (D1, 2026-10-15).",
    "what-you-need": "Optional cables: group labels and currents span four rows and the cable header spans two "
                     "columns, in five columns; no shared table component has row or column spans.",
    "product-overview": "LED indicators: each indicator name spans its two or three status rows; the shared "
                        "reference and LCD tables have fixed columns and no row spans.",
    "installation-guide": "Conductor tightening torque: grid and home-load sides in six columns; no shared table "
                          "component has six columns.",
}
NORMALIZATIONS = [
    "Shared Manual IR: content.json is replayed through the shared flow renderer and shared components "
    "(callout strip, warning lockup, reference figure, App download, warranty lead and sections), "
    "in the accepted English edition's order.",
    "Print line breaks: a line the print ended while the next word would still have fitted is kept as a "
    "line break; every other line end is a wrap (logged per language in source/<lang>/coverage.json).",
    "Print weights: bold and semibold runs stay strong; headings keep print case; table header cells the "
    "print sets in regular weight stay regular.",
    "Lists: numbered and bullet print items become ordered or unordered lists; asterisk notes and FCC dash "
    "lines stay as printed lines.",
    "Tables keep the print's merged cells (row and column spans); the specification table has no header row, as printed.",
    "Ligatures are expanded; print-split words are rejoined and logged (FR domes-/tique, automatique-/ment, "
    "immédi-/atement, alimenta/tion; ES concesion-/ario, recomien-/da, instruc-/ciones).",
    "Two visible French lines drawn as vector outlines (p42) are restored from source/text-recovery.json.",
    "The Spanish print repeats its p62 (PDF 64 and 65 are identical); the repeat is classified and left out.",
    "Artwork words stay in the reviewed figure crops; the figures carry no visible caption.",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain_tables(nodes):
    """Tables outside shared components, in reading order."""
    for item in nodes:
        if not isinstance(item, dict) or item.get("kind") == "component":
            continue
        if item.get("kind") == "table":
            yield item
        yield from plain_tables(item.get("children", []))


def table_exceptions(manifest):
    rows = []
    for language in manifest["target"]["languages"]:
        content = json.loads((SOURCE / "source" / language / "content.json").read_text())
        for chapter in content["chapters"]:
            for table in plain_tables(chapter["nodes"]):
                rows.append({"language": language, "page_id": chapter["id"], "kind": "table",
                             "text_sha256": table_text_sha256(table), "reason": TABLE_REASONS[chapter["id"]]})
    return rows


def refresh():
    destination = SOURCE / "source_manifest.json"
    manifest = json.loads(destination.read_text())
    english = REPO / manifest["english_baseline"]
    manifest["normalizations"] = NORMALIZATIONS
    manifest["shared_component_exceptions"] = table_exceptions(manifest)
    manifest["validation_boundary"] = {
        "build_py_check": "Existing JE-1000F/US fixture regression only; does not validate JA-TS02A or register it in phase2.",
        "native_body": [
            "word coverage of PDF pages 25-46 (fr) and 47-69 (es) (source/<lang>/coverage.json)",
            "shared Manual IR validation and replay",
            "cold replay byte parity",
            "strict Sphinx",
            "component, symbol (per locale) and caption-frame admissions",
            "Chromium sweep 320-1920 px",
        ],
    }
    dependencies = {REPO / "tools/markdown_bundle.py", REPO / "tools/build_paths.py", SHARED / "manifest.json"}
    for relative in ["tools/manual_ir", "tools/component_specs", "tools/web", "tools/asset_pipeline",
                     "tools/utils", "docs/renderers/contracts"]:
        dependencies.update(p for p in (REPO / relative).rglob("*")
                            if p.is_file() and p.suffix in {".py", ".css", ".json", ".yaml", ".yml"})
    dependencies.add(SHARED / "native-v1" / "symbol_read_manual.svg")
    # The English package: the archived PDF, and the records and artwork the extraction reuses.
    dependencies.update(REPO / part["path"] for part in manifest["original_source"]["archive_parts"])
    dependencies.update({english / "source/figures.json", english / "source/inline-controls.json"})
    dependencies.update(english / "assets" / p.name for p in (SOURCE / "assets").iterdir()
                        if (english / "assets" / p.name).is_file())
    manifest["repo_inputs"] = [{"path": p.relative_to(REPO).as_posix(), "size": p.stat().st_size,
                                "sha256": digest(p)} for p in sorted(dependencies)]
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(
        destination, SOURCE / "source/__pycache__", SOURCE / "__pycache__")))
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
