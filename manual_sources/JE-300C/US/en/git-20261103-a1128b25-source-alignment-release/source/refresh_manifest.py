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
LANGUAGES = ("en",)
SHARED = REPO / "docs/renderers/web/assets/shared/symbols"
NORMALIZATIONS = ['Outlined current original.pdf physical p2 and p4–18 reviewed in both directions; no source paragraph silently rewritten or legacy-source paragraph retained.', 'Native ManualIR retained. Source-local geometry restores source pairing and shared theme typography remains a Web carrier difference. Troubleshooting uses native rowspan only where the actual source merges cells.', 'Bold wording, signal-word colons and V_oc/LiFePO₄ subscripts are retained. LCD table uses original circled Unicode row numbers and one shared high/low-temperature number cell.', 'Only responsive wraps and repeated spaces differ. Native text preserves original punctuation, technical statements and source concerns; no stylistic content corrections inferred.', 'Original source figure panels and their own pictograms retained. Safety black-risk and white-warning symbols extracted from this exact PDF. Safety/operating columns, FCC opening+two-column body, LCD button/table and input-indicator/table relationships restored.', 'Front coverp1 and paperTOCp3 remain excluded by explicit operator scope. Backcontactp18 native company/address/phone/email/web and ownphone/mail/webpictograms plus originalQR are retained.']


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
