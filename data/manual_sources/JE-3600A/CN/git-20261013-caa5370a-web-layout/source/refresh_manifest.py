"""Rebind the frozen-source inventory of this JE-3600A Web-layout edition.

The same file lives in the CN and JP editions. This source-local maintenance
command never changes content, art or live data: it re-hashes every package file
(except source_manifest.json itself) and the shared repository files rebuild.py
pins, and keeps an operator acceptance already recorded in the manifest.
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
APPROVED = {"CN": "git-20261012-caa5370a-reviewed", "JP": "git-20261012-fd06cd04-reviewed"}
LANGUAGE = {"CN": "zh", "JP": "ja"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh() -> None:
    region = SOURCE.parent.name
    reviewed = SOURCE.parent / APPROVED[region]
    base = json.loads((reviewed / "source_manifest.json").read_text())
    language = LANGUAGE[region]
    manifest = {
        "schema_version": "auto-manual-frozen-web-source/v1",
        "target": {"model": "JE-3600A", "region": region, "technical_version": SOURCE.name,
                   "languages": [language]},
        "derived_from": {"technical_version": APPROVED[region],
                         "path": reviewed.relative_to(REPO).as_posix(),
                         "derivation": "derive_web_layout.py"},
        "original_source": base["original_source"],
        "scope": f"Git-only native {region}/{language} Web-layout edition; no online-table writes",
        "live_bitable_dependency": False,
        "phase2_enrolled": False,
        "web_roots": {language: "web/" + language},
        "repository_regression_gate": base["repository_regression_gate"],
    }
    # rebuild.py replays through the same shared modules the reviewed edition pinned.
    manifest["repo_inputs"] = [{"path": row["path"], "size": (REPO / row["path"]).stat().st_size,
                                "sha256": digest(REPO / row["path"])} for row in base["repo_inputs"]]
    destination = SOURCE / "source_manifest.json"
    if destination.is_file():
        # Operator acceptance is recorded separately and survives an inventory refresh.
        status = json.loads(destination.read_text()).get("publication_status")
        if status:
            manifest["publication_status"] = status
    manifest["inputs"] = list(_file_inventory(SOURCE, excluded_roots=(
        destination, SOURCE / "__pycache__", SOURCE / "source/__pycache__")))
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"source_inputs": len(manifest["inputs"]),
                      "repository_inputs": len(manifest["repo_inputs"])}, indent=2))


if __name__ == "__main__":
    refresh()
