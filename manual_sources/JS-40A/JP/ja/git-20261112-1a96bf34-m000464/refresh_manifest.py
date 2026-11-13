"""Inventory immutable package inputs; optional frozen mode includes rendered Web/evidence."""

import json
import hashlib
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parent


def entry(path):
    return {
        "path": path.relative_to(PACKAGE).as_posix(),
        "size": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


manifest = PACKAGE / "source_manifest.json"
data = json.loads(manifest.read_text())
files = [
    p
    for p in PACKAGE.rglob("*")
    if p.is_file()
    and "__pycache__" not in p.parts
    and (
        p.relative_to(PACKAGE).parts[0] in ["source", "assets"]
        or p.name
        in [
            "README.md",
            "build_content.py",
            "rebuild.py",
            "refresh_manifest.py",
            "derive_assets.py",
        ]
    )
]
data["inputs"] = [entry(p) for p in sorted(files)]
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
if "frozen" in sys.argv:
    frozen = PACKAGE / "frozen_source_manifest.json"
    data["inputs"] = [
        entry(p)
        for p in sorted(PACKAGE.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p != frozen
    ]
    frozen.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"package": PACKAGE.name, "inputs": len(data["inputs"])}))
