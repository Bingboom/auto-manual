from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VENV_DIR = ROOT / ".vercel-python"


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


def main() -> int:
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
            "HEAD~1",
            "--to-ref",
            "HEAD",
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
