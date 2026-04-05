from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable


def require_explicit_target(*, model: str | None, region: str | None, action_name: str) -> tuple[str, str]:
    normalized_model = (model or "").strip()
    normalized_region = (region or "").strip()
    if not normalized_model or not normalized_region:
        raise RuntimeError(f"{action_name} requires --model and --region so the release target is explicit")
    return normalized_model, normalized_region


def publish_target_components(
    *,
    config_path: Path,
    model: str | None,
    region: str | None,
    action_name: str,
    config_loader: Callable[[Path], dict[str, Any]],
    resolve_output_lang: Callable[[dict[str, Any]], str | None],
) -> tuple[str, str, str | None]:
    resolved_model, resolved_region = require_explicit_target(
        model=model,
        region=region,
        action_name=action_name,
    )
    cfg = config_loader(config_path)
    return resolved_model, resolved_region, resolve_output_lang(cfg)


def tracked_root_for_target(
    *,
    config_path: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
    review_root_for_config: Callable[[Path], Path],
) -> Path:
    base = review_root_for_config(config_path) / (model or "_shared") / (region or "_default")
    if (lang or "").strip():
        return base / str(lang).strip()
    return base


def report_dir_for_target(
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
    version_tracking_root: Callable[..., Path],
    base_root: Path | None = None,
) -> Path:
    base = version_tracking_root(base_root=base_root) / (model or "_shared") / (region or "_default")
    if (lang or "").strip():
        return base / str(lang).strip()
    return base


def default_report_dir_for_tracked_root(
    *,
    config_path: Path,
    tracked_root: Path,
    review_root_for_config: Callable[[Path], Path],
    version_tracking_root: Callable[..., Path],
    base_root: Path | None = None,
) -> Path:
    review_root = review_root_for_config(config_path)
    try:
        rel = tracked_root.resolve(strict=False).relative_to(review_root.resolve(strict=False))
    except ValueError:
        return version_tracking_root(base_root=base_root) / tracked_root.name
    return version_tracking_root(base_root=base_root) / rel


def resolve_diff_report_targets(
    *,
    config_path: Path,
    config_loader: Callable[[Path], dict[str, Any]],
    resolve_build_targets: Callable[..., list[Any]],
    model: str | None,
    region: str | None,
) -> list[tuple[str | None, str | None, str | None]]:
    cfg = config_loader(config_path)
    targets = resolve_build_targets(
        cfg,
        arg_model=model,
        arg_region=region,
        all_targets=not (model or region),
    )
    return [(target.model, target.region, target.lang) for target in targets]


def diff_report_command(
    *,
    repo_root: Path,
    config_path: Path,
    tracked_root: Path,
    report_dir: Path,
    from_ref: str,
    to_ref: str,
    data_root: str | None,
    ignore_initial_adds: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "diff_report.py"),
        "--tracked-root",
        str(tracked_root),
        "--config",
        str(config_path),
        "--from-ref",
        from_ref,
        "--to-ref",
        to_ref,
        "--output-dir",
        str(report_dir),
        *(
            ["--data-root", data_root.strip()]
            if isinstance(data_root, str) and data_root.strip()
            else []
        ),
    ]
    if not ignore_initial_adds:
        cmd.append("--include-initial-adds")
    return cmd
