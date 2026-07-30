from __future__ import annotations

import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=2)

from tools.process_docs.build_review_preview import assert_preview_output_contract, read_json_if_exists
from tools.process_docs.build_review_preview_targets import FAMILY_ORDER
from tools.config_loader import load_config_mapping
from tools.utils.path_utils import Paths


VENV_DIR = ROOT / ".vercel-python"
DIST_DIR = ROOT / "site" / "review-preview" / "dist"
REVIEW_ROOT = Paths(root=ROOT).review_dir
DEFAULT_PREVIEW_DATA_ROOT = "tests/fixtures/phase2"


def _preview_config_score(config_path: Path, build_cfg: dict[str, object], region: str) -> int:
    """Prefer a family config over its language-specific config variants."""

    languages = build_cfg.get("languages", [])
    language_count = len(languages) if isinstance(languages, list) else 0
    score = 0
    if not bool(build_cfg.get("include_lang_in_output_path", False)):
        score += 100
    if bool(build_cfg.get("queue_by_document_key", False)):
        score += 20
    if language_count == 1:
        score += 10
    if config_path.stem == f"config.{region.lower()}":
        score += 1
    return score


def discover_default_preview_configs(configs_dir: Path = ROOT / "configs") -> dict[str, str]:
    """Derive preview family configs from the repository's config files.

    The preview package only has default families for ``FAMILY_ORDER``. A
    family config is selected over a language-specific config by the same
    output-path and queue semantics that distinguish the current defaults.
    """

    candidates: dict[str, list[tuple[int, Path]]] = {family: [] for family in FAMILY_ORDER}
    for config_path in sorted(configs_dir.glob("config*.yaml")):
        config = load_config_mapping(config_path)
        build_cfg_raw = config.get("build", {})
        build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
        region = str(build_cfg.get("default_region") or "").strip().upper()
        if region not in candidates:
            continue
        candidates[region].append((_preview_config_score(config_path, build_cfg, region), config_path))

    defaults: dict[str, str] = {}
    for family in FAMILY_ORDER:
        family_candidates = candidates[family]
        if not family_candidates:
            raise RuntimeError(f"No preview config found for family {family!r} under {configs_dir}")
        family_candidates.sort(key=lambda item: (-item[0], item[1].name))
        best_score = family_candidates[0][0]
        best_paths = [path for score, path in family_candidates if score == best_score]
        if len(best_paths) > 1:
            names = ", ".join(path.name for path in best_paths)
            raise RuntimeError(f"Preview config resolution is ambiguous for family {family!r}: {names}")
        resolved = best_paths[0].resolve()
        try:
            defaults[family] = resolved.relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            defaults[family] = resolved.as_posix()
    return defaults


@lru_cache(maxsize=1)
def default_preview_configs() -> dict[str, str]:
    return discover_default_preview_configs()


# Compatibility surface for callers that imported the old constant. The
# source of truth is now the config scan above rather than a second map.
DEFAULT_PREVIEW_CONFIGS = default_preview_configs()


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


def default_preview_config(region: str, *, configs_dir: Path = ROOT / "configs") -> str:
    config_name = discover_default_preview_configs(configs_dir).get((region or "").strip().upper())
    if config_name is None:
        raise RuntimeError(
            "PREVIEW_CONFIG is required when PREVIEW_REGION is outside the supported defaults "
            "(US, JP, CN)."
        )
    return config_name


def discover_default_preview_target_from_configs(
    configs_dir: Path = ROOT / "configs",
) -> tuple[str, str] | None:
    """Return the first registered preview target when review output is absent."""

    defaults = discover_default_preview_configs(configs_dir)
    for family in FAMILY_ORDER:
        config_path = Path(defaults[family])
        if not config_path.is_absolute():
            config_path = ROOT / config_path
        config_path = config_path.resolve()
        config = load_config_mapping(config_path)
        build_cfg_raw = config.get("build", {})
        build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
        model = str(build_cfg.get("default_model") or "").strip()
        region = str(build_cfg.get("default_region") or "").strip().upper()
        if model and region:
            return model, region
    return None


def resolve_preview_target(
    review_root: Path = REVIEW_ROOT,
    *,
    configs_dir: Path = ROOT / "configs",
) -> tuple[str, str]:
    model = os.environ.get("PREVIEW_MODEL", "").strip()
    region = os.environ.get("PREVIEW_REGION", "").strip()
    if model and region:
        return model, region

    discovered = discover_default_preview_target(review_root)
    if discovered is None:
        discovered = discover_default_preview_target_from_configs(configs_dir)
    if discovered is None:
        raise RuntimeError(
            "PREVIEW_MODEL and PREVIEW_REGION are required when no review target or registered config target exists."
        )

    discovered_model, discovered_region = discovered
    return model or discovered_model, region or discovered_region


def build_preview_command(
    python_exe: Path,
    *,
    review_root: Path = REVIEW_ROOT,
    configs_dir: Path = ROOT / "configs",
) -> list[str]:
    model, region = resolve_preview_target(review_root, configs_dir=configs_dir)
    config = os.environ.get("PREVIEW_CONFIG", "").strip() or default_preview_config(
        region,
        configs_dir=configs_dir,
    )
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
