"""Refresh the input inventory of this package.

Run from the repository root after ``derive_assets.py`` and ``build_content.py``:

    python manual_sources/JE-1000D/JP/ja/git-20261026-00c43a89-v2/refresh_manifest.py

It rewrites ``source_manifest.json:inputs`` over the original PDF, README,
scripts, ``source/`` and ``assets/``. ``rebuild.py`` checks every listed hash,
and the IR it writes embeds the manifest, so run this before ``rebuild.py``.
The stored ``web/ja`` render and ``evidence/`` are outputs, not inputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
FILES = ("JE-1000D-JP-V2.pdf", "README.md", "build_content.py", "derive_assets.py", "rebuild.py",
         "refresh_manifest.py")


def entry(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(PACKAGE).as_posix(), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    found = [PACKAGE / name for name in FILES]
    for folder in ("source", "assets"):
        found += [p for p in (PACKAGE / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    path = PACKAGE / "source_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["inputs"] = [entry(p) for p in sorted(found, key=lambda p: p.relative_to(PACKAGE).as_posix())]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inputs": len(manifest["inputs"])}))


if __name__ == "__main__":
    main()
