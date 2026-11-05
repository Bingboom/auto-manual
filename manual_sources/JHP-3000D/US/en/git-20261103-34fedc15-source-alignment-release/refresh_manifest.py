"""Refresh reviewed input hashes, or freeze the completed package with `frozen`."""
from pathlib import Path
import hashlib
import json
import sys

PACKAGE = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in PACKAGE.parents if (p / "build.py").is_file())


def entry(path, base):
    data = path.read_bytes()
    return {"path": path.relative_to(base).as_posix(), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main(mode=""):
    manifest_path = PACKAGE / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    frozen_path = PACKAGE / "frozen_source_manifest.json"
    if mode == "frozen":
        found = [p for p in PACKAGE.rglob("*") if p.is_file() and p != frozen_path
                 and "__pycache__" not in p.parts]
        manifest["inputs"] = [entry(p, PACKAGE) for p in sorted(found)]
        frozen_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        return
    if mode:
        raise SystemExit("usage: refresh_manifest.py [frozen]")
    manifest["repo_inputs"] = [entry(REPO_ROOT / r["path"], REPO_ROOT)
                               for r in manifest["repo_inputs"]]
    found = [p for p in PACKAGE.rglob("*") if p.is_file()
             and p not in (manifest_path, frozen_path) and "__pycache__" not in p.parts
             and not p.is_relative_to(PACKAGE / "web")
             and not p.is_relative_to(PACKAGE / "evidence")]
    manifest["inputs"] = [entry(p, PACKAGE) for p in sorted(found)]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
