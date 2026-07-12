from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class DispatchContext:
    config_path: Path
    ensure_supported_staging_action: Callable[[argparse.Namespace], None]
    run_validate: Callable[..., None]
    run_doctor: Callable[[argparse.Namespace], None]
    run_checked: Callable[[list[str]], None]
    build_docs_command: Callable[..., list[str]]
    review_bundle_command: Callable[[argparse.Namespace], list[str]]
    run_check: Callable[[argparse.Namespace], None]
    sync_review_command: Callable[[argparse.Namespace], list[str]]
    sync_data_command: Callable[[argparse.Namespace], list[str]]
    spec_master_rebuild_command: Callable[[argparse.Namespace], list[str]]
    run_translation_memory: Callable[[argparse.Namespace], None]
    run_message_control_dry_run: Callable[[argparse.Namespace], None]
    run_manual_index_query: Callable[[argparse.Namespace], None]
    run_queue_query: Callable[[argparse.Namespace], None]
    run_queue_resolve_action: Callable[[argparse.Namespace], None]
    run_queue_execute: Callable[[argparse.Namespace], None]
    process_review_start_queue_command: Callable[[argparse.Namespace], list[str]]
    process_build_queue_command: Callable[[argparse.Namespace], list[str]]
    listen_build_queue_command: Callable[[argparse.Namespace], list[str]]
    listen_message_control_command: Callable[[argparse.Namespace], list[str]]
    run_publish: Callable[[argparse.Namespace], None]
    run_diff_report: Callable[[argparse.Namespace], None]
    release_manifest_command: Callable[[argparse.Namespace], list[str]]
    clean_build_artifacts: Callable[[Path], None]
    maybe_sync_review_before_build: Callable[..., None]


ActionHandler = Callable[[argparse.Namespace, DispatchContext], None]


def _dispatch_validate_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_validate(
        context.config_path,
        data_root=args.data_root,
        model=args.model,
        region=args.region,
    )


def _dispatch_doctor_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_doctor(args)


def _dispatch_review_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.build_docs_command(args, action_override="rst", source_override="runtime"))
    context.run_checked(context.review_bundle_command(args))


def _dispatch_check_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_check(args)


def _dispatch_sync_review_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.build_docs_command(args, action_override="rst", source_override="runtime"))
    context.run_checked(context.sync_review_command(args))


def _dispatch_sync_data_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.sync_data_command(args))


def _dispatch_spec_master_rebuild_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.spec_master_rebuild_command(args))


def _dispatch_translation_memory_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_translation_memory(args)


def _dispatch_message_control_dry_run_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_message_control_dry_run(args)


def _dispatch_manual_index_query_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_manual_index_query(args)


def _dispatch_queue_query_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_queue_query(args)


def _dispatch_queue_resolve_action_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_queue_resolve_action(args)


def _dispatch_queue_execute_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_queue_execute(args)


def _dispatch_process_review_start_queue_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.process_review_start_queue_command(args))


def _dispatch_process_build_queue_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.process_build_queue_command(args))


def _dispatch_listen_build_queue_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.listen_build_queue_command(args))


def _dispatch_listen_message_control_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.listen_message_control_command(args))


def _dispatch_publish_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_publish(args)


def _dispatch_diff_report_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_diff_report(args)


def _dispatch_release_manifest_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.release_manifest_command(args))


def _dispatch_clean_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.clean_build_artifacts(context.config_path)


def _dispatch_build_action(args: argparse.Namespace, context: DispatchContext) -> None:
    # `fast` forces a runtime-source, no-clean build (build_docs_command), so its
    # effective source is runtime. Tell the review pre-sync that too, or it gates
    # on the raw --source (default auto) and runs a --clean RST rebuild + a
    # docs/_review params rewrite as an unexpected side effect of a "quick" build.
    if args.action == "fast":
        context.maybe_sync_review_before_build(args, source_override="runtime")
    else:
        context.maybe_sync_review_before_build(args)
    context.run_checked(context.build_docs_command(args))


def _dispatch_idml_action(args: argparse.Namespace, context: "DispatchContext") -> None:
    """Export the editable InDesign handoff package (tools/export_idml.py)."""
    import sys as _sys

    # Production IDML needs both the prepared bundle and the LaTeX reference PDF
    # used by its page plan. Flow-only mode still needs just the RST bundle.
    _src = getattr(args, "source", None)
    source_override = _src if _src in {"review", "review-asis", "runtime"} else "runtime"
    mode = getattr(args, "idml_mode", "production")
    build_action = "rst" if mode == "flow" else "pdf"
    build_args = argparse.Namespace(**vars(args))
    if build_action == "pdf":
        build_args.pdf_mode = "latex"
    context.run_checked(context.build_docs_command(
        build_args, action_override=build_action, source_override=source_override))
    cmd = [_sys.executable, str(Path(__file__).resolve().parents[1] / "tools" / "export_idml.py")]
    if getattr(args, "model", None):
        cmd += ["--model", args.model]
    if getattr(args, "region", None):
        cmd += ["--region", args.region]
    if getattr(args, "lang", None):
        cmd += ["--lang", args.lang]
    if getattr(args, "data_root", None):
        cmd += ["--data-root", args.data_root]
    if mode:
        cmd += ["--mode", mode]
    context.run_checked(cmd)


ACTION_HANDLERS: dict[str, ActionHandler] = {
    "validate": _dispatch_validate_action,
    "idml": _dispatch_idml_action,
    "doctor": _dispatch_doctor_action,
    "review": _dispatch_review_action,
    "check": _dispatch_check_action,
    "sync-review": _dispatch_sync_review_action,
    "sync-data": _dispatch_sync_data_action,
    "spec-master-rebuild": _dispatch_spec_master_rebuild_action,
    "translation-memory": _dispatch_translation_memory_action,
    "message-control-dry-run": _dispatch_message_control_dry_run_action,
    "manual-index-query": _dispatch_manual_index_query_action,
    "queue-query": _dispatch_queue_query_action,
    "queue-resolve-action": _dispatch_queue_resolve_action_action,
    "queue-execute": _dispatch_queue_execute_action,
    "process-review-start-queue": _dispatch_process_review_start_queue_action,
    "process-build-queue": _dispatch_process_build_queue_action,
    "listen-build-queue": _dispatch_listen_build_queue_action,
    "listen-message-control": _dispatch_listen_message_control_action,
    "publish": _dispatch_publish_action,
    "diff-report": _dispatch_diff_report_action,
    "release-manifest": _dispatch_release_manifest_action,
    "clean": _dispatch_clean_action,
}


def registered_actions() -> tuple[str, ...]:
    return tuple(ACTION_HANDLERS)


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
    spec_master_rebuild_command: Callable[[argparse.Namespace], list[str]],
    run_translation_memory: Callable[[argparse.Namespace], None],
    run_message_control_dry_run: Callable[[argparse.Namespace], None],
    run_manual_index_query: Callable[[argparse.Namespace], None],
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
    context = DispatchContext(
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
        spec_master_rebuild_command=spec_master_rebuild_command,
        run_translation_memory=run_translation_memory,
        run_message_control_dry_run=run_message_control_dry_run,
        run_manual_index_query=run_manual_index_query,
        run_queue_query=run_queue_query,
        run_queue_resolve_action=run_queue_resolve_action,
        run_queue_execute=run_queue_execute,
        process_review_start_queue_command=process_review_start_queue_command,
        process_build_queue_command=process_build_queue_command,
        listen_build_queue_command=listen_build_queue_command,
        listen_message_control_command=listen_message_control_command,
        run_publish=run_publish,
        run_diff_report=run_diff_report,
        release_manifest_command=release_manifest_command,
        clean_build_artifacts=clean_build_artifacts,
        maybe_sync_review_before_build=maybe_sync_review_before_build,
    )
    context.ensure_supported_staging_action(args)
    ACTION_HANDLERS.get(args.action, _dispatch_build_action)(args, context)
