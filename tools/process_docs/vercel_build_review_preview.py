from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)

from tools.process_docs.build_review_preview import assert_preview_output_contract, read_json_if_exists
from tools.utils.path_utils import Paths


VENV_DIR = ROOT / ".vercel-python"
DIST_DIR = ROOT / "site" / "review-preview" / "dist"
REVIEW_ROOT = Paths(root=ROOT).review_dir
DEFAULT_PREVIEW_CONFIGS = {
    "US": "configs/config.us.yaml",
    "JP": "configs/config.ja.yaml",
    "CN": "configs/config.zh.yaml",
}
DEFAULT_PREVIEW_DATA_ROOT = "tests/fixtures/phase2"


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


def discover_default_preview_target(review_root: Path = REVIEW_ROOT) -> tuple[str, str] | None:
    if not review_root.exists():
        return None

    model_dirs = sorted(path for path in review_root.iterdir() if path.is_dir())
    for model_dir in model_dirs:
        region_dirs = sorted(path for path in model_dir.iterdir() if path.is_dir())
        for region_dir in region_dirs:
            return model_dir.name, region_dir.name
    return None


def default_preview_config(region: str) -> str:
    config_name = DEFAULT_PREVIEW_CONFIGS.get((region or "").strip().upper())
    if config_name is None:
        raise RuntimeError(
            "PREVIEW_CONFIG is required when PREVIEW_REGION is outside the supported defaults "
            "(US, JP, CN)."
        )
    return config_name


def resolve_preview_target(review_root: Path = REVIEW_ROOT) -> tuple[str, str]:
    model = os.environ.get("PREVIEW_MODEL", "").strip()
    region = os.environ.get("PREVIEW_REGION", "").strip()
    if model and region:
        return model, region

    discovered = discover_default_preview_target(review_root)
    if discovered is None:
        raise RuntimeError(
            "PREVIEW_MODEL and PREVIEW_REGION are required when no docs/_review/<model>/<region> target exists."
        )

    discovered_model, discovered_region = discovered
    return model or discovered_model, region or discovered_region


def build_preview_command(
    python_exe: Path,
    *,
    review_root: Path = REVIEW_ROOT,
) -> list[str]:
    model, region = resolve_preview_target(review_root)
    config = os.environ.get("PREVIEW_CONFIG", "").strip() or default_preview_config(region)
    cmd = [
        str(python_exe),
        "tools/process_docs/build_review_preview.py",
        "--config",
        config,
        "--model",
        model,
        "--region",
        region,
        "--source",
        os.environ.get("PREVIEW_SOURCE", "review"),
        "--from-ref",
        os.environ.get("FROM_REF", "HEAD~1"),
        "--to-ref",
        os.environ.get("TO_REF", "HEAD"),
        "--all-review-models",
    ]
    data_root = os.environ.get("PREVIEW_DATA_ROOT", DEFAULT_PREVIEW_DATA_ROOT).strip()
    if data_root:
        cmd.extend(["--data-root", data_root])
    return cmd


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
    run(build_preview_command(python_exe))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
