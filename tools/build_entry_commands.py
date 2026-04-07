from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Callable


def normalize_cli_build_queue_action(workflow_action: str | None = None, doc_phase: str | None = None) -> str | None:
    explicit = (workflow_action or "").strip().lower()
    legacy = (doc_phase or "").strip().lower()
    normalized_explicit = None
    if explicit:
        normalized_explicit = "draft" if explicit == "build-draft-package" else "publish"
    if normalized_explicit:
        return normalized_explicit
    if legacy:
        raise RuntimeError("--doc-phase is no longer supported; use --workflow-action")
    return None


def effective_source(args: argparse.Namespace, *, source_override: str = "auto") -> str:
    return args.source if source_override == "auto" else source_override


def append_target_args(cmd: list[str], args: argparse.Namespace) -> list[str]:
    if args.model:
        cmd += ["--model", args.model]
    if args.region:
        cmd += ["--region", args.region]
    if not (args.model or args.region):
        cmd.append("--all-targets")
    return cmd


def append_data_root_arg(cmd: list[str], args: argparse.Namespace) -> list[str]:
    if isinstance(args.data_root, str) and args.data_root.strip():
        cmd += ["--data-root", args.data_root.strip()]
    return cmd


def build_docs_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    build_actions: tuple[str, ...],
    all_output_formats: str,
    resolve_path_from_root: Callable[[str], Path],
    staging_docs_build_dir: Callable[[argparse.Namespace], Path | None],
    preview_output_root: Callable[..., Path],
    require_explicit_target: Callable[[argparse.Namespace, str], tuple[str, str]],
    action_override: str | None = None,
    source_override: str | None = None,
) -> list[str]:
    action = action_override or args.action
    if action not in (*build_actions, "preview", "fast"):
        raise RuntimeError(f"Action '{action}' is not a build action")

    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "build_docs.py"),
        "--config",
        str(config_path),
    ]
    append_target_args(cmd, args)
    append_data_root_arg(cmd, args)
    current_effective_source = source_override or args.source
    staged_docs_build_dir = staging_docs_build_dir(args)
    if action == "fast":
        current_effective_source = "runtime"
    cmd += ["--source", current_effective_source]

    if action in {"rst", "preview", "fast"}:
        cmd.append("--prepare-only")
    elif action == "all":
        cmd += ["--formats", all_output_formats]
    else:
        cmd += ["--formats", action]

    if action == "preview":
        model, region = require_explicit_target(args, "preview")
        page = (args.page or "").strip()
        if not page:
            raise RuntimeError("preview requires --page so the bundle scope is explicit")
        cmd += ["--page-selector", page]
        cmd += [
            "--output-root",
            str(
                preview_output_root(
                    config_path,
                    model=model,
                    region=region,
                    page=page,
                    docs_build_dir=staged_docs_build_dir,
                )
            ),
        ]
        cmd.append("--skip-root-index")
    elif staged_docs_build_dir is not None:
        cmd += ["--output-base-root", str(staged_docs_build_dir), "--skip-root-index"]
    elif args.skip_root_index:
        cmd.append("--skip-root-index")

    if args.pdf_mode:
        cmd += ["--pdf-mode", args.pdf_mode]
    if action != "fast" and not args.no_clean:
        cmd.append("--clean")
    if not args.open:
        cmd.append("--no-open")
    return cmd


def review_bundle_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
    staging_docs_build_dir: Callable[[argparse.Namespace], Path | None],
) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "review_bundle.py"),
        "--config",
        str(config_path),
    ]
    append_target_args(cmd, args)
    staged = staging_docs_build_dir(args)
    if staged is not None:
        cmd += ["--docs-build-dir", str(staged)]
    if args.refresh_review:
        cmd.append("--refresh-existing")
    return cmd


def check_docs_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
    staging_docs_build_dir: Callable[[argparse.Namespace], Path | None],
) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "check_docs.py"),
        "--config",
        str(config_path),
    ]
    append_target_args(cmd, args)
    append_data_root_arg(cmd, args)
    staged = staging_docs_build_dir(args)
    if staged is not None:
        cmd += ["--docs-build-dir", str(staged)]
    return cmd


def sync_review_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
    staging_docs_build_dir: Callable[[argparse.Namespace], Path | None],
) -> list[str]:
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "sync_review.py"),
        "--config",
        str(config_path),
        "--sync-scope",
        args.sync_scope,
    ]
    append_target_args(cmd, args)
    staged = staging_docs_build_dir(args)
    if staged is not None:
        cmd += ["--docs-build-dir", str(staged)]
    for page_file in args.page_file:
        cmd += ["--page-file", page_file]
    return cmd


def sync_data_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
) -> list[str]:
    if (args.model or "").strip() or (args.region or "").strip():
        raise RuntimeError("sync-data does not accept --model or --region; it always exports full snapshot tables")
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "sync_data.py"),
        "--config",
        str(config_path),
    ]
    append_data_root_arg(cmd, args)
    for table in args.table:
        cmd += ["--table", table]
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def release_manifest_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    require_explicit_target: Callable[[argparse.Namespace, str], tuple[str, str]],
    resolve_path_from_root: Callable[[str], Path],
    staging_docs_build_dir: Callable[[argparse.Namespace], Path | None],
    staging_releases_root: Callable[[argparse.Namespace], Path | None],
) -> list[str]:
    model, region = require_explicit_target(args, "release-manifest")
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "release_manifest.py"),
        "--config",
        str(config_path),
        "--model",
        model,
        "--region",
        region,
    ]
    append_data_root_arg(cmd, args)
    staged_docs = staging_docs_build_dir(args)
    staged_releases = staging_releases_root(args)
    if staged_docs is not None:
        cmd += ["--docs-build-dir", str(staged_docs)]
    if staged_releases is not None:
        cmd += ["--releases-root", str(staged_releases)]
    return cmd


def process_build_queue_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
    normalize_cli_build_queue_action: Callable[[str | None, str | None], str | None],
) -> list[str]:
    if (args.model or "").strip() or (args.region or "").strip():
        raise RuntimeError(
            "process-build-queue does not accept --model or --region; Build Draft Package / Publish targets come from Document_link rows"
        )
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "process_build_queue.py"),
        "--config",
        str(config_path),
    ]
    append_data_root_arg(cmd, args)
    normalized_action = normalize_cli_build_queue_action(args.workflow_action, args.doc_phase)
    if normalized_action == "draft":
        cmd += ["--workflow-action", "build-draft-package"]
    elif normalized_action == "publish":
        cmd += ["--workflow-action", "publish"]
    if isinstance(args.record_id, str) and args.record_id.strip():
        cmd += ["--record-id", args.record_id.strip()]
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def process_review_start_queue_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
) -> list[str]:
    if (args.model or "").strip() or (args.region or "").strip():
        raise RuntimeError(
            "process-review-start-queue does not accept --model or --region; Start Review targets come from Review-init rows"
        )
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "process_review_start_queue.py"),
        "--config",
        str(config_path),
    ]
    append_data_root_arg(cmd, args)
    if isinstance(args.record_id, str) and args.record_id.strip():
        cmd += ["--record-id", args.record_id.strip()]
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def listen_build_queue_command(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
) -> list[str]:
    if (args.model or "").strip() or (args.region or "").strip():
        raise RuntimeError(
            "listen-build-queue does not accept --model or --region; targets come from Document_link events"
        )
    config_path = resolve_path_from_root(args.config)
    cmd = [
        sys.executable,
        str(repo_root / "tools" / "listen_build_queue.py"),
        "--config",
        str(config_path),
    ]
    append_data_root_arg(cmd, args)
    return cmd
