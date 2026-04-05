from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable


def dispatch_action(
    args: argparse.Namespace,
    *,
    config_path: Path,
    ensure_supported_staging_action: Callable[[argparse.Namespace], None],
    run_validate: Callable[[Path], None],
    run_doctor: Callable[[argparse.Namespace], None],
    run_checked: Callable[[list[str]], None],
    build_docs_command: Callable[..., list[str]],
    review_bundle_command: Callable[[argparse.Namespace], list[str]],
    run_check: Callable[[argparse.Namespace], None],
    sync_review_command: Callable[[argparse.Namespace], list[str]],
    sync_data_command: Callable[[argparse.Namespace], list[str]],
    process_review_start_queue_command: Callable[[argparse.Namespace], list[str]],
    process_build_queue_command: Callable[[argparse.Namespace], list[str]],
    listen_build_queue_command: Callable[[argparse.Namespace], list[str]],
    run_publish: Callable[[argparse.Namespace], None],
    run_diff_report: Callable[[argparse.Namespace], None],
    release_manifest_command: Callable[[argparse.Namespace], list[str]],
    clean_build_artifacts: Callable[[Path], None],
    maybe_sync_review_before_build: Callable[[argparse.Namespace], None],
) -> None:
    ensure_supported_staging_action(args)
    if args.action == "validate":
        run_validate(config_path, data_root=args.data_root)
    elif args.action == "doctor":
        run_doctor(args)
    elif args.action == "review":
        run_checked(build_docs_command(args, action_override="rst", source_override="runtime"))
        run_checked(review_bundle_command(args))
    elif args.action == "check":
        run_check(args)
    elif args.action == "sync-review":
        run_checked(build_docs_command(args, action_override="rst", source_override="runtime"))
        run_checked(sync_review_command(args))
    elif args.action == "sync-data":
        run_checked(sync_data_command(args))
    elif args.action == "process-review-start-queue":
        run_checked(process_review_start_queue_command(args))
    elif args.action == "process-build-queue":
        run_checked(process_build_queue_command(args))
    elif args.action == "listen-build-queue":
        run_checked(listen_build_queue_command(args))
    elif args.action == "publish":
        run_publish(args)
    elif args.action == "diff-report":
        run_diff_report(args)
    elif args.action == "release-manifest":
        run_checked(release_manifest_command(args))
    elif args.action == "clean":
        clean_build_artifacts(config_path)
    else:
        maybe_sync_review_before_build(args)
        run_checked(build_docs_command(args))
