"""Refresh the input inventories of this package.

Run from the repository root:

    python manual_sources/JA-CK01A-BK/JP/ja/git-20261023-3ea84ec6-manual/refresh_manifest.py inputs
    python manual_sources/JA-CK01A-BK/JP/ja/git-20261023-3ea84ec6-manual/refresh_manifest.py frozen

``inputs`` rewrites ``source_manifest.json:inputs`` (scripts, ``source/`` and
``assets/``) and the pinned repository inputs; run it before ``render.py``,
whose IR embeds that manifest. ``frozen`` writes ``frozen_source_manifest.json``
over every file of the package except itself, for ``seal_frozen_web_evidence``;
run it after the stored ``web/ja`` render and ``evidence/`` are in place.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parent
ROOT = next(parent for parent in PACKAGE.parents if (parent / "build.py").is_file())
SCRIPTS = ("derive_assets.py", "refresh_manifest.py", "render.py")
REPO_INPUTS = ("docs/renderers/contracts/web_presentation/target_overlays.json",)


def entry(path: Path, base: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(base).as_posix(), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def files(*roots: Path) -> list[Path]:
    found = []
    for root in roots:
        found += [root] if root.is_file() else [p for p in root.rglob("*") if p.is_file()]
    return sorted((p for p in found if "__pycache__" not in p.parts), key=lambda p: p.relative_to(PACKAGE).as_posix())


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(mode: str) -> None:
    manifest_path = PACKAGE / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if mode == "inputs":
        manifest["inputs"] = [entry(p, PACKAGE) for p in files(
            *(PACKAGE / name for name in SCRIPTS), PACKAGE / "source", PACKAGE / "assets")]
        manifest["repo_inputs"] = [{"path": name, "sha256": entry(ROOT / name, ROOT)["sha256"]}
                                   for name in REPO_INPUTS]
        write(manifest_path, manifest)
    elif mode == "frozen":
        frozen = PACKAGE / "frozen_source_manifest.json"
        manifest["inputs"] = [entry(p, PACKAGE) for p in files(PACKAGE) if p != frozen]
        write(frozen, manifest)
    else:
        raise SystemExit("usage: refresh_manifest.py inputs|frozen")
    print(json.dumps({"mode": mode, "inputs": len(manifest["inputs"])}))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
