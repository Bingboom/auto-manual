#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = "config.yaml"
BUILD_ACTIONS = ("rst", "word", "html", "pdf", "all")
ALL_OUTPUT_FORMATS = "html,word,pdf"
REVIEW_TRACKED_ROOT = "docs/_review/JE-1000F"
REVIEW_REPORT_DIR = "reports/version_tracking/JE-1000F"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Cross-platform build entrypoint for Auto-Manual.",
    )
    ap.add_argument(
        "action",
        choices=("validate", *BUILD_ACTIONS, "review", "check", "publish", "clean", "diff-report"),
        help="Action to run",
    )
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="Config YAML path, relative to repo root by default")
    ap.add_argument("--model", default=None, help="Build a single model instead of build.targets")
    ap.add_argument("--region", default=None, help="Build a single region instead of build.targets")
    ap.add_argument(
        "--source",
        choices=("auto", "runtime", "review"),
        default="runtime",
        help="Content source for build actions: auto, runtime, or review",
    )
    ap.add_argument("--pdf-mode", choices=("latex", "word"), default=None, help="Override PDF backend")
    ap.add_argument("--open", action="store_true", help="Allow opening generated artifacts after build")
    ap.add_argument("--no-clean", action="store_true", help="Skip cleaning current target outputs before build")
    ap.add_argument(
        "--refresh-review",
        action="store_true",
        help="Refresh an existing review bundle from the runtime template/data output",
    )
    ap.add_argument("--tracked-root", default=REVIEW_TRACKED_ROOT, help="Tracked subtree for diff-report")
    ap.add_argument("--from-ref", default="HEAD~1", help="Git from ref for diff-report")
    ap.add_argument("--to-ref", default="HEAD", help="Git to ref for diff-report")
    ap.add_argument(
        "--ignore-initial-adds",
        action="store_true",
        help="Ignore initial all-Added rows when the tracked subtree is first introduced",
    )
    ap.add_argument(
        "--report-dir",
        default=REVIEW_REPORT_DIR,
        help="Output directory for diff-report CSV/HTML",
    )
    return ap.parse_args(argv)


def resolve_path_from_root(raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (ROOT / path)


def load_config(config_path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc

    if not config_path.exists():
        raise RuntimeError(f"Config not found: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception as exc:
        raise RuntimeError(f"Failed to load config: {config_path}") from exc

    if not isinstance(data, dict):
        raise RuntimeError(f"Config root must be a mapping: {config_path}")
    return data


def resolve_layout_params_csv(config_path: Path) -> Path:
    cfg = load_config(config_path)
    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        raw = paths_cfg.get("layout_params_csv")
        if isinstance(raw, str) and raw.strip():
            return resolve_path_from_root(raw.strip())
    return ROOT / "data" / "layout_params.csv"


def resolve_docs_dir(config_path: Path) -> Path:
    try:
        cfg = load_config(config_path)
    except RuntimeError:
        return ROOT / "docs"

    paths_cfg = cfg.get("paths", {})
    if isinstance(paths_cfg, dict):
        raw = paths_cfg.get("docs_dir")
        if isinstance(raw, str) and raw.strip():
            return resolve_path_from_root(raw.strip())
    return ROOT / "docs"


def clean_targets_for_config(config_path: Path) -> tuple[Path, Path]:
    docs_dir = resolve_docs_dir(config_path)
    return docs_dir / "_build", docs_dir / "renderers" / "latex" / "params.tex"


def review_root_for_config(config_path: Path) -> Path:
    docs_dir = resolve_docs_dir(config_path)
    return docs_dir / "_review"


def is_legacy_bundle_dir(path: Path) -> bool:
    return path.is_dir() and (path / "index.rst").exists() and (path / "page").is_dir()


def collect_legacy_docs_output_dirs(docs_dir: Path) -> list[Path]:
    if not docs_dir.exists():
        return []

    legacy_dirs: list[Path] = []
    generated_dir = docs_dir / "generated"
    if generated_dir.exists():
        legacy_dirs.append(generated_dir)

    reserved = {"_build", "_static", "renderers", "templates", "__pycache__"}
    for child in docs_dir.iterdir():
        if not child.is_dir() or child.name in reserved or child == generated_dir:
            continue
        if is_legacy_bundle_dir(child):
            legacy_dirs.append(child)
            continue
        subdirs = [item for item in child.iterdir() if item.is_dir()]
        if subdirs and all(is_legacy_bundle_dir(item) for item in subdirs):
            legacy_dirs.append(child)
    return legacy_dirs


def format_command(cmd: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in cmd])


def run_checked(cmd: list[str]) -> None:
    print(f"[build.py] {format_command(cmd)}")
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def _append_target_args(cmd: list[str], args: argparse.Namespace) -> list[str]:
    if args.model:
        cmd += ["--model", args.model]
    if args.region:
        cmd += ["--region", args.region]
    if not (args.model or args.region):
        cmd.append("--all-targets")
    return cmd


def build_docs_command(
    args: argparse.Namespace,
    *,
    action_override: str | None = None,
    source_override: str | None = None,
) -> list[str]:
    action = action_override or args.action
    if action not in BUILD_ACTIONS:
        raise RuntimeError(f"Action '{action}' is not a build action")

    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "build_docs.py"),
        "--config",
        str(config_path),
    ]
    _append_target_args(cmd, args)
    cmd += ["--source", source_override or args.source]

    if action == "rst":
        cmd.append("--prepare-only")
    elif action == "all":
        cmd += ["--formats", ALL_OUTPUT_FORMATS]
    else:
        cmd += ["--formats", action]

    if args.pdf_mode:
        cmd += ["--pdf-mode", args.pdf_mode]
    if not args.no_clean:
        cmd.append("--clean")
    if not args.open:
        cmd.append("--no-open")
    return cmd


def review_bundle_command(args: argparse.Namespace) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "review_bundle.py"),
        "--config",
        str(config_path),
    ]
    _append_target_args(cmd, args)
    if args.refresh_review:
        cmd.append("--refresh-existing")
    return cmd


def check_docs_command(args: argparse.Namespace) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "check_docs.py"),
        "--config",
        str(config_path),
    ]
    return _append_target_args(cmd, args)


def run_validate(config_path: Path) -> None:
    run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_config.py"),
            "--config",
            str(config_path),
        ]
    )
    run_checked(
        [
            sys.executable,
            str(ROOT / "tools" / "validate_layout_params.py"),
            "--csv",
            str(resolve_layout_params_csv(config_path)),
        ]
    )


def run_diff_report(args: argparse.Namespace) -> None:
    run_diff_report_with_paths(
        args,
        tracked_root=resolve_path_from_root(args.tracked_root),
        report_dir=resolve_path_from_root(args.report_dir),
    )


def run_diff_report_with_paths(
    args: argparse.Namespace,
    *,
    tracked_root: Path,
    report_dir: Path,
) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "diff_report.py"),
        "--tracked-root",
        str(tracked_root),
        "--config",
        str(resolve_path_from_root(args.config)),
        "--from-ref",
        args.from_ref,
        "--to-ref",
        args.to_ref,
        "--output-dir",
        str(report_dir),
    ]
    if args.ignore_initial_adds:
        cmd.append("--ignore-initial-adds")
    run_checked(cmd)


def run_check(args: argparse.Namespace, *, source_override: str = "runtime") -> None:
    config_path = resolve_path_from_root(args.config)
    run_validate(config_path)
    run_checked(build_docs_command(args, action_override="rst", source_override=source_override))
    run_checked(check_docs_command(args))


def _publish_target_components(args: argparse.Namespace) -> tuple[str, str]:
    model = (args.model or "").strip()
    region = (args.region or "").strip()
    if not model or not region:
        raise RuntimeError("publish requires --model and --region so the release target is explicit")
    return model, region


def _publish_tracked_root(args: argparse.Namespace) -> Path:
    model, region = _publish_target_components(args)
    if args.tracked_root == REVIEW_TRACKED_ROOT:
        return ROOT / "docs" / "_review" / model / region
    return resolve_path_from_root(args.tracked_root)


def _publish_report_dir(args: argparse.Namespace) -> Path:
    model, region = _publish_target_components(args)
    if args.report_dir == REVIEW_REPORT_DIR:
        return ROOT / "reports" / "version_tracking" / model / region
    return resolve_path_from_root(args.report_dir)


def run_publish(args: argparse.Namespace) -> None:
    tracked_root = _publish_tracked_root(args)
    report_dir = _publish_report_dir(args)
    run_check(args, source_override="review")
    run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)
    run_checked(build_docs_command(args, action_override="word", source_override="review"))


def clean_build_artifacts(config_path: Path, *, remove_params_tex: bool = True) -> None:
    build_dir, params_tex = clean_targets_for_config(config_path)
    review_dir = review_root_for_config(config_path)
    docs_dir = resolve_docs_dir(config_path)
    print(f"[build.py] remove {build_dir}")
    shutil.rmtree(build_dir, ignore_errors=True)
    print(f"[build.py] remove {review_dir}")
    shutil.rmtree(review_dir, ignore_errors=True)
    if remove_params_tex:
        print(f"[build.py] remove {params_tex}")
        params_tex.unlink(missing_ok=True)
    for legacy_dir in collect_legacy_docs_output_dirs(docs_dir):
        print(f"[build.py] remove {legacy_dir}")
        shutil.rmtree(legacy_dir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = resolve_path_from_root(args.config)

    try:
        if args.action == "validate":
            run_validate(config_path)
        elif args.action == "review":
            run_checked(build_docs_command(args, action_override="rst", source_override="runtime"))
            run_checked(review_bundle_command(args))
        elif args.action == "check":
            run_check(args)
        elif args.action == "publish":
            run_publish(args)
        elif args.action == "diff-report":
            run_diff_report(args)
        elif args.action == "clean":
            clean_build_artifacts(config_path)
        else:
            run_checked(build_docs_command(args))
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    except RuntimeError as exc:
        print(f"[build.py] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
