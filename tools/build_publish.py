from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable


def run_diff_report(
    args: argparse.Namespace,
    *,
    resolve_path_from_root: Callable[[str], Path],
    resolve_staging_root: Callable[[argparse.Namespace], Path | None],
    default_report_dir_for_tracked_root: Callable[[Path, Path], Path],
    run_diff_report_with_paths: Callable[..., None],
    resolve_diff_report_targets: Callable[[argparse.Namespace], list[tuple[str | None, str | None, str | None]]],
    tracked_root_for_target: Callable[[Path, str | None, str | None, str | None], Path],
    report_dir_for_target: Callable[[str | None, str | None, str | None, Path | None], Path],
) -> None:
    config_path = resolve_path_from_root(args.config)
    tracked_root_explicit = args.tracked_root is not None
    report_dir_explicit = args.report_dir is not None
    staging_root = resolve_staging_root(args)

    if tracked_root_explicit:
        tracked_root = resolve_path_from_root(args.tracked_root)
        if report_dir_explicit:
            report_dir = resolve_path_from_root(args.report_dir)
        else:
            report_dir = default_report_dir_for_tracked_root(config_path, tracked_root)
        run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)
        return

    targets = resolve_diff_report_targets(args)
    if report_dir_explicit and len(targets) != 1:
        raise RuntimeError("diff-report with explicit --report-dir requires a single resolved target or explicit --tracked-root")

    for target in targets:
        if len(target) == 2:
            model, region = target
            lang = None
        else:
            model, region, lang = target
        tracked_root = tracked_root_for_target(config_path, model, region, lang)
        report_dir = (
            resolve_path_from_root(args.report_dir)
            if report_dir_explicit
            else report_dir_for_target(model, region, lang, staging_root)
        )
        run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)


def run_diff_report_with_paths(
    args: argparse.Namespace,
    *,
    run_checked: Callable[[list[str]], None],
    diff_report_command: Callable[[argparse.Namespace, Path, Path], list[str]],
    tracked_root: Path,
    report_dir: Path,
) -> None:
    run_checked(diff_report_command(args, tracked_root, report_dir))


def run_publish(
    args: argparse.Namespace,
    *,
    publish_tracked_root: Callable[[argparse.Namespace], Path],
    publish_report_dir: Callable[[argparse.Namespace], Path],
    run_check: Callable[..., None],
    run_diff_report_with_paths: Callable[..., None],
    run_checked: Callable[[list[str]], None],
    build_docs_command: Callable[..., list[str]],
    release_manifest_command: Callable[[argparse.Namespace], list[str]],
) -> None:
    tracked_root = publish_tracked_root(args)
    report_dir = publish_report_dir(args)
    run_check(args, source_override="review")
    run_diff_report_with_paths(args, tracked_root=tracked_root, report_dir=report_dir)
    run_checked(build_docs_command(args, action_override="word", source_override="review"))
    # Keep the freshly generated DOCX in place so publish can stage both DOCX and PDF.
    run_checked(build_docs_command(args, action_override="pdf", source_override="review", no_clean_override=True))
    run_checked(build_docs_command(args, action_override="md", source_override="review", no_clean_override=True))
    run_checked(release_manifest_command(args))
