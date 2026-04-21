from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable


def dispatch_action(
    args: argparse.Namespace,
    *,
    config_path: Path,
    ensure_supported_staging_action: Callable[[argparse.Namespace], None],
    run_validate: Callable[..., None],
    run_doctor: Callable[[argparse.Namespace], None],
    run_checked: Callable[[list[str]], None],
    build_docs_command: Callable[..., list[str]],
    review_bundle_command: Callable[[argparse.Namespace], list[str]],
    run_check: Callable[[argparse.Namespace], None],
    sync_review_command: Callable[[argparse.Namespace], list[str]],
    sync_data_command: Callable[[argparse.Namespace], list[str]],
    run_translation_memory: Callable[[argparse.Namespace], None],
    run_message_control_dry_run: Callable[[argparse.Namespace], None],
    run_queue_query: Callable[[argparse.Namespace], None],
    run_queue_resolve_action: Callable[[argparse.Namespace], None],
    run_queue_execute: Callable[[argparse.Namespace], None],
    process_review_start_queue_command: Callable[[argparse.Namespace], list[str]],
    process_build_queue_command: Callable[[argparse.Namespace], list[str]],
    listen_build_queue_command: Callable[[argparse.Namespace], list[str]],
    listen_message_control_command: Callable[[argparse.Namespace], list[str]],
    run_publish: Callable[[argparse.Namespace], None],
    run_diff_report: Callable[[argparse.Namespace], None],
    release_manifest_command: Callable[[argparse.Namespace], list[str]],
    clean_build_artifacts: Callable[[Path], None],
    maybe_sync_review_before_build: Callable[[argparse.Namespace], None],
) -> None:
    ensure_supported_staging_action(args)
    if args.action == "validate":
        run_validate(
            config_path,
            data_root=args.data_root,
            model=args.model,
            region=args.region,
        )
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
    elif args.action == "translation-memory":
        run_translation_memory(args)
    elif args.action == "message-control-dry-run":
        run_message_control_dry_run(args)
    elif args.action == "queue-query":
        run_queue_query(args)
    elif args.action == "queue-resolve-action":
        run_queue_resolve_action(args)
    elif args.action == "queue-execute":
        run_queue_execute(args)
    elif args.action == "process-review-start-queue":
        run_checked(process_review_start_queue_command(args))
    elif args.action == "process-build-queue":
        run_checked(process_build_queue_command(args))
    elif args.action == "listen-build-queue":
        run_checked(listen_build_queue_command(args))
    elif args.action == "listen-message-control":
        run_checked(listen_message_control_command(args))
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
