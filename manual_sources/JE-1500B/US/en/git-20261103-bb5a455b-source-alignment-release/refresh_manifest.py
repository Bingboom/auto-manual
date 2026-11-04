"""Refresh the input inventories of this package.

Run from the repository root after ``derive_assets.py`` and ``build_content.py``:

    python manual_sources/JE-1500B/US/en/git-20261027-bb5a455b/refresh_manifest.py
    python manual_sources/JE-1500B/US/en/git-20261027-bb5a455b/refresh_manifest.py frozen

The default mode rewrites ``source_manifest.json:inputs`` over the original PDF, README,
scripts, ``source/`` and ``assets/``. ``rebuild.py`` checks every listed hash,
and the IR it writes embeds the manifest, so run this before ``rebuild.py``.
The stored ``web/en`` render and ``evidence/`` are outputs, not inputs.
``frozen`` writes ``frozen_source_manifest.json`` over every file of the
package except itself, for ``seal_frozen_web_evidence``; run it last, after
the stored render and ``evidence/`` are in place.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parent
FILES = ("JE-1500B-US-EN.pdf", "README.md", "build_content.py", "derive_assets.py", "rebuild.py",
         "refresh_manifest.py")


def entry(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": path.relative_to(PACKAGE).as_posix(), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main(mode: str = "") -> None:
    path = PACKAGE / "source_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if mode == "frozen":
        frozen = PACKAGE / "frozen_source_manifest.json"
        found = [p for p in PACKAGE.rglob("*") if p.is_file() and p != frozen and "__pycache__" not in p.parts]
        manifest["inputs"] = [entry(p) for p in sorted(found, key=lambda p: p.relative_to(PACKAGE).as_posix())]
        frozen.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"mode": mode, "inputs": len(manifest["inputs"])}))
        return
    if mode:
        raise SystemExit("usage: refresh_manifest.py [frozen]")
    found = [PACKAGE / name for name in FILES]
    for folder in ("source", "assets"):
        found += [p for p in (PACKAGE / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    manifest["inputs"] = [entry(p) for p in sorted(found, key=lambda p: p.relative_to(PACKAGE).as_posix())]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inputs": len(manifest["inputs"])}))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
