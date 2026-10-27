"""Refresh the two package manifests.

``source_manifest.json`` keeps the release metadata and inventories the
reviewed inputs (``source/``, ``assets/`` and the package scripts) that
``render.py`` checks. ``frozen_source_manifest.json`` is the same metadata
inventorying every package file except itself, including ``web/ja`` and
``evidence/``; release sealing binds it. Run from the repository root after
any change, and again after replacing ``web/ja``. A second run leaves both
files unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
MANIFEST = PACKAGE / "source_manifest.json"
FROZEN = PACKAGE / "frozen_source_manifest.json"
SCRIPTS = ("derive_assets.py", "refresh_manifest.py", "render.py")
REPO_INPUTS = ("docs/renderers/contracts/web_presentation/target_overlays.json",)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row(path: Path) -> dict:
    return {"path": path.relative_to(PACKAGE).as_posix(), "size": path.stat().st_size, "sha256": sha256(path)}


def files(*roots: str) -> list[Path]:
    found = []
    for root in roots:
        base = PACKAGE / root
        found += [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file()]
    return sorted((p for p in found if "__pycache__" not in p.parts), key=lambda p: p.relative_to(PACKAGE).as_posix())


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["inputs"] = [row(path) for path in files("assets", "source", *SCRIPTS)]
    manifest["repo_inputs"] = [{"path": path, "sha256": sha256(ROOT / path)} for path in REPO_INPUTS]
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frozen = dict(manifest, inputs=[row(path) for path in sorted(
        (p for p in PACKAGE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p != FROZEN),
        key=lambda p: p.relative_to(PACKAGE).as_posix())])
    FROZEN.write_text(json.dumps(frozen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(manifest['inputs'])} reviewed inputs, {len(frozen['inputs'])} package files")


if __name__ == "__main__":
    main()
