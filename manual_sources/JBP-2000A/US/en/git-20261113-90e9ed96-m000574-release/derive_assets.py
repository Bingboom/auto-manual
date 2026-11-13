"""Reproduce quarantined source-bound crops; never promote an online/global asset row."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / "build.py").is_file())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(output):
    if output.exists() or output.is_relative_to(PACKAGE):
        raise ValueError("use unused scratch output outside package")
    recipe = PACKAGE / "source/asset_recipe.json"
    r = json.loads(recipe.read_text())
    subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.asset_intake",
            "--asset-source-key",
            r["source"]["source_key"],
            "--asset-source-file",
            str(PACKAGE / "source/original.pdf"),
            "--asset-recipe",
            str(recipe),
            "--asset-output-root",
            str(output),
        ],
        cwd=REPO,
        check=True,
    )
    decisions = json.loads((PACKAGE / "source/asset_decisions.json").read_text())["assets"]
    for slot, row in decisions.items():
        if row["mode"] == "reuse-packaged-donor":
            src = PACKAGE / row["path"]
        elif row["mode"] == "new-extraction":
            src = output / "artifacts/assets" / (slot + ".png")
        else:
            raise ValueError("unknown source artwork decision")
        if sha(src) != row["sha256"]:
            raise ValueError("candidate artwork bytes differ: " + slot)
        target = PACKAGE / row["path"]
        if src.resolve() != target.resolve():
            shutil.copy2(src, target)
    print(
        json.dumps(
            {
                "assets_verified": len(decisions),
                "gate": "quarantine; operator pixel review pending",
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    derive(p.parse_args().output.resolve())
