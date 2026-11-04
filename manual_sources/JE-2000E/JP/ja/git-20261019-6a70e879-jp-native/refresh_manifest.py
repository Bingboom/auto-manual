"""Refresh ``source_manifest.json:inputs`` over every file of this package.

Run from the repository root after ``derive_symbols.py`` and after copying a
fresh render into ``web/ja``:

    python manual_sources/JE-2000E/JP/ja/git-20261019-6a70e879-jp-native/refresh_manifest.py

``rebuild.py`` checks every listed hash except the stored ``web/ja`` render
outputs (only ``web/ja/assets`` are inputs there), so run this before
``rebuild.py`` and again after the stored render is replaced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent


def entry(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(PACKAGE).as_posix(), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    path = PACKAGE / "source_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    found = [p for p in PACKAGE.rglob("*") if p.is_file() and p != path and "__pycache__" not in p.parts]
    manifest["inputs"] = [entry(p) for p in sorted(found, key=lambda p: p.relative_to(PACKAGE).as_posix())]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inputs": len(manifest["inputs"])}))


if __name__ == "__main__":
    main()
