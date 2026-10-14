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
    "Shared Manual IR: content.json is replayed through the shared flow renderer and shared components "
    "(callout strip, warning lockup, reference figure, App download, warranty lead and sections).",
    "Print line breaks: a line the print ended while the next word would still have fitted is kept as a "
    "line break; every other line end is a wrap (logged in source/en/coverage.json).",
    "Print weights: bold and semibold runs stay strong; headings keep print case and the print's two subheading sizes.",
    "Lists: numbered and bullet print items become ordered or unordered lists; asterisk notes and FCC dash "
    "lines stay as printed lines.",
    "Tables keep the print's merged cells (row and column spans); the specification table has no header row, as printed.",
    "Ligatures are expanded; two print-split words are rejoined (consump-/tion, approxi/mately).",
    "Five visible lines absent from the PDF text layer are restored from source/text-recovery.json.",
    "Artwork words stay in the reviewed figure crops; the figures carry no visible caption.",
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh():
    destination = SOURCE / "source_manifest.json"
    manifest = json.loads(destination.read_text())
    manifest["normalizations"] = NORMALIZATIONS
    manifest["validation_boundary"]["native_body"] = [
        "word coverage of PDF pages 3-24 (source/en/coverage.json)",
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
    for name in ["symbol_warning_triangle.svg", "symbol_electric_shock.svg", "symbol_read_manual.svg"]:
        dependencies.add(SHARED / "native-v1" / name)
    manifest["repo_inputs"] = [{"path": p.relative_to(REPO).as_posix(), "size": p.stat().st_size,
                                "sha256": digest(p)} for p in sorted(dependencies)]
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(
        destination, SOURCE / "source/__pycache__", SOURCE / "__pycache__")))
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
