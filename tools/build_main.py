from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable


def run_main(
    argv: list[str] | None = None,
    *,
    parse_args: Callable[[list[str] | None], argparse.Namespace],
    resolve_path_from_root: Callable[[str], Path],
    dispatch_action: Callable[..., None],
    ensure_supported_staging_action: Callable[[argparse.Namespace], None],
    run_validate: Callable[..., None],
    run_doctor: Callable[[argparse.Namespace], None],
    run_checked: Callable[[list[str]], None],
    build_docs_command: Callable[..., list[str]],
    review_bundle_command: Callable[[argparse.Namespace], list[str]],
    run_check: Callable[..., None],
    sync_review_command: Callable[[argparse.Namespace], list[str]],
    sync_data_command: Callable[[argparse.Namespace], list[str]],
    run_message_control_dry_run: Callable[[argparse.Namespace], None],
    run_queue_query: Callable[[argparse.Namespace], None],
    run_queue_resolve_action: Callable[[argparse.Namespace], None],
    run_queue_execute: Callable[[argparse.Namespace], None],
    process_review_start_queue_command: Callable[[argparse.Namespace], list[str]],
    process_build_queue_command: Callable[[argparse.Namespace], list[str]],
    listen_build_queue_command: Callable[[argparse.Namespace], list[str]],
    run_publish: Callable[[argparse.Namespace], None],
    run_diff_report: Callable[[argparse.Namespace], None],
    release_manifest_command: Callable[[argparse.Namespace], list[str]],
    clean_build_artifacts: Callable[[Path], None],
    maybe_sync_review_before_build: Callable[[argparse.Namespace], None],
) -> int:
    args = parse_args(argv)
    config_path = resolve_path_from_root(args.config)

    try:
        dispatch_action(
            args,
            config_path=config_path,
            ensure_supported_staging_action=ensure_supported_staging_action,
            run_validate=run_validate,
            run_doctor=run_doctor,
            run_checked=run_checked,
            build_docs_command=build_docs_command,
            review_bundle_command=review_bundle_command,
            run_check=run_check,
            sync_review_command=sync_review_command,
            sync_data_command=sync_data_command,
            run_message_control_dry_run=run_message_control_dry_run,
            run_queue_query=run_queue_query,
            run_queue_resolve_action=run_queue_resolve_action,
            run_queue_execute=run_queue_execute,
            process_review_start_queue_command=process_review_start_queue_command,
            process_build_queue_command=process_build_queue_command,
            listen_build_queue_command=listen_build_queue_command,
            run_publish=run_publish,
            run_diff_report=run_diff_report,
            release_manifest_command=release_manifest_command,
            clean_build_artifacts=clean_build_artifacts,
            maybe_sync_review_before_build=maybe_sync_review_before_build,
        )
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    except RuntimeError as exc:
        print(f"[build.py] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0
