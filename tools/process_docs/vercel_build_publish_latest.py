from __future__ import annotations

import subprocess
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)

from tools.process_docs.build_publish_latest_site import build_site, copy_contents
from tools.utils.path_utils import Paths


VENV_DIR = ROOT / ".vercel-python"
DIST_DIR = ROOT / "site" / "publish-latest" / "dist"
RELEASES_ROOT = Paths(root=ROOT).releases_dir


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


def existing_publish_site_is_ready() -> bool:
    return (DIST_DIR / "index.html").exists()


def main() -> int:
    if existing_publish_site_is_ready():
        # A staged site can come from an older whole-tree artifact. Validate
        # and trim it before reuse, retaining the original until copy succeeds.
        with TemporaryDirectory(dir=DIST_DIR.parent) as temporary:
            staged = Path(temporary) / "dist"
            copy_contents(DIST_DIR, staged)
            shutil.rmtree(DIST_DIR)
            shutil.move(str(staged), str(DIST_DIR))
        print("[vercel-publish-latest] Reusing trimmed static site under site/publish-latest/dist")
        return 0

    if RELEASES_ROOT.exists():
        build_site(releases_root=RELEASES_ROOT, output_dir=DIST_DIR)
        return 0

    python_exe = venv_python()
    if not python_exe.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        python_exe = venv_python()

    run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"])
    run([str(python_exe), str(ROOT / "tools" / "process_docs" / "build_publish_latest_site.py")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
