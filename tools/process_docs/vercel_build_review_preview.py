from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.process_docs.build_review_preview import assert_preview_output_contract, read_json_if_exists


VENV_DIR = ROOT / ".vercel-python"
DIST_DIR = ROOT / "site" / "review-preview" / "dist"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def venv_python() -> Path:
    candidates = [
        VENV_DIR / "bin" / "python",
        VENV_DIR / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def existing_preview_is_ready() -> bool:
    workspace = read_json_if_exists(DIST_DIR / "generated" / "workspace.json")
    try:
        assert_preview_output_contract(DIST_DIR, workspace, require_word=True)
    except RuntimeError:
        return False
    return True


def main() -> int:
    if existing_preview_is_ready():
        print("[vercel-review-preview] Reusing existing preview package under site/review-preview/dist")
        return 0

    python_exe = venv_python()

    if not python_exe.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        python_exe = venv_python()

    run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"])
    run(
        [
            str(python_exe),
            "tools/process_docs/build_review_preview.py",
            "--config",
            "config.yaml",
            "--model",
            "JE-1000F",
            "--region",
            "US",
            "--source",
            "review",
            "--from-ref",
            os.environ.get("FROM_REF", "HEAD~1"),
            "--to-ref",
            os.environ.get("TO_REF", "HEAD"),
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
