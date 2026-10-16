"""Rebind the frozen-source inventory of this JE-3600A shared-component edition.

The same file lives in the CN and JP editions. It never changes content, art or
live data: it re-hashes every package file (except source_manifest.json itself)
and the shared repository modules the replay depends on, and keeps any operator
acceptance status already recorded in the manifest.
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
BASE = {"CN": "git-20261013-caa5370a-web-layout", "JP": "git-20261013-fd06cd04-web-layout"}
LANGUAGE = {"CN": "zh", "JP": "ja"}
SHARED_MODULES = ["tools/manual_ir", "tools/component_specs", "tools/web", "tools/asset_pipeline",
                  "tools/utils", "docs/renderers/contracts"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh() -> None:
    region = SOURCE.parent.name
    base_dir = SOURCE.parent / BASE[region]
    base = json.loads((base_dir / "source_manifest.json").read_text())
    language = LANGUAGE[region]
    manifest = {
        "schema_version": "auto-manual-frozen-web-source/v1",
        "target": {"model": "JE-3600A", "region": region, "technical_version": SOURCE.name,
                   "languages": [language]},
        "derived_from": {"technical_version": BASE[region], "path": base_dir.relative_to(REPO).as_posix(),
                         "derivation": "derive_shared.py"},
        "original_source": base["original_source"],
        "scope": f"Git-only native {region}/{language} shared-component edition; no online-table writes",
        "live_bitable_dependency": False,
        "phase2_enrolled": False,
        "web_roots": {language: "web/" + language},
        "repository_regression_gate": base["repository_regression_gate"],
        "publication_status": "git-only-source-candidate",
    }
    dependencies = {REPO / "tools/markdown_bundle.py", REPO / "tools/build_paths.py",
                    REPO / "docs/renderers/web/assets/shared/symbols/manifest.json"}
    for relative in SHARED_MODULES:
        dependencies.update(p for p in (REPO / relative).rglob("*")
                            if p.is_file() and p.suffix in {".py", ".css", ".json", ".yaml", ".yml"}
                            and "__pycache__" not in p.parts
                            # The shared-style baseline lists other packages; it never shapes this replay.
                            and p.name != "prepared_style_baseline.json")
    manifest["repo_inputs"] = [{"path": p.relative_to(REPO).as_posix(), "size": p.stat().st_size,
                                "sha256": digest(p)} for p in sorted(dependencies)]
    destination = SOURCE / "source_manifest.json"
    if destination.is_file():
        previous = json.loads(destination.read_text())
        manifest["publication_status"] = previous.get("publication_status", manifest["publication_status"])
        for key in ("symbol_asset_admission", "shared_component_exceptions"):
            if key in previous:
                manifest[key] = previous[key]
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(
        destination, SOURCE / "__pycache__", SOURCE / "source/__pycache__")))
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
