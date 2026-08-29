from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tools.build_paths import (
    resolve_idml_assembly_plan,
    resolve_idml_layout_param_overlays,
    resolve_layout_params_csv,
)


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
    release_rebuild_command: Callable[[argparse.Namespace], list[str]]
    clean_build_artifacts: Callable[[Path], None]
    maybe_sync_review_before_build: Callable[..., None]
    run_asset_command: Callable[[argparse.Namespace], None] | None = None
    run_new_line: Callable[[argparse.Namespace], None] | None = None


ActionHandler = Callable[[argparse.Namespace, DispatchContext], None]


def target_has_approved_reference_plan(
    *,
    model: str | None,
    region: str | None,
    config_path: Path,
    repo_root: Path,
) -> bool:
    """Return whether one resolved target is governed by an approved plan."""

    from tools.config_loader import load_config_mapping
    from tools.model_languages import resolve_target_languages
    from tools.utils.path_utils import PathSegments, Paths

    try:
        cfg = load_config_mapping(config_path)
        build = cfg.get("build", {})
        if not isinstance(build, dict):
            return False
        model = str(model or build.get("default_model") or "").strip()
        region = str(region or build.get("default_region") or "").strip()
        raw_languages = build.get("languages")
        if not isinstance(raw_languages, list):
            return False
        family_languages = [str(language).strip() for language in raw_languages]
        if not model or not region or any(
            not language for language in family_languages
        ):
            return False
        paths = Paths(root=repo_root)
        languages = list(
            resolve_target_languages(
                family_languages,
                model=model,
                region=region,
                data_dir=paths.data_dir,
            ).languages
        )
        registry_path = (
            paths.renderer_contracts_dir
            / PathSegments.REFERENCE_LAYOUT_REGISTRY_JSON
        )
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
        return False
    entries = registry.get("plans") if isinstance(registry, dict) else None
    if not isinstance(entries, list):
        return False
    target = {"model": model, "region": region, "languages": languages}
    return any(isinstance(entry, dict) and entry.get("target") == target for entry in entries)


def _target_has_approved_reference_plan(
    args: argparse.Namespace,
    *,
    config_path: Path,
    repo_root: Path,
) -> bool:
    """CLI adapter for :func:`target_has_approved_reference_plan`."""

    return target_has_approved_reference_plan(
        model=getattr(args, "model", None),
        region=getattr(args, "region", None),
        config_path=config_path,
        repo_root=repo_root,
    )


def _effective_idml_language(
    args: argparse.Namespace,
    *,
    config_path: Path,
) -> str | None:
    """Resolve the exporter language without changing multilingual defaults.

    An explicit ``--lang`` always wins.  For a single-language family, the
    config declaration is authoritative even when the CLI flag is omitted.
    Multilingual families retain the exporter's historical default unless the
    caller selects one language explicitly.
    """

    explicit = str(getattr(args, "lang", None) or "").strip()
    if explicit:
        return explicit

    from tools.config_loader import load_config_mapping
    from tools.utils.targets import resolve_build_languages

    try:
        languages = resolve_build_languages(load_config_mapping(config_path))
    except (OSError, RuntimeError, ValueError):
        return None
    return languages[0] if len(languages) == 1 else None


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


def _dispatch_asset_action(args: argparse.Namespace, context: DispatchContext) -> None:
    if context.run_asset_command is None:
        raise RuntimeError("asset commands are not wired into this build entrypoint")
    context.run_asset_command(args)


def _dispatch_new_line_action(args: argparse.Namespace, context: DispatchContext) -> None:
    if context.run_new_line is None:
        raise RuntimeError("new-line is not wired into this build entrypoint")
    context.run_new_line(args)


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


def _dispatch_release_rebuild_action(args: argparse.Namespace, context: DispatchContext) -> None:
    context.run_checked(context.release_rebuild_command(args))


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

    # An approved target already has a hash-bound physical page plan.  A target
    # with an explicitly configured candidate assembly likewise gets its page
    # order from contract data.  Neither needs a fresh LaTeX PDF; unregistered
    # targets retain that PDF for the historical measured fallback.
    mode = getattr(args, "idml_mode", "production")
    repo_root = Path(__file__).resolve().parents[1]
    assembly_plan = resolve_idml_assembly_plan(
        context.config_path,
        repo_root=repo_root,
        model=getattr(args, "model", None),
        region=getattr(args, "region", None),
    )
    layout_params_csv = resolve_layout_params_csv(
        context.config_path,
        repo_root=repo_root,
    )
    layout_param_overlays = resolve_idml_layout_param_overlays(
        context.config_path,
        repo_root=repo_root,
        model=getattr(args, "model", None),
        region=getattr(args, "region", None),
    )
    approved_target = _target_has_approved_reference_plan(
        args,
        config_path=context.config_path,
        repo_root=repo_root,
    )
    _src = getattr(args, "source", None)
    source_override = (
        _src
        if _src in {"review", "review-asis", "runtime"}
        else "review-asis" if approved_target else "runtime"
    )
    build_action = (
        "rst"
        if mode == "flow" or approved_target or assembly_plan is not None
        else "pdf"
    )
    build_args = argparse.Namespace(**vars(args))
    if build_action == "pdf":
        build_args.pdf_mode = "latex"
    context.run_checked(context.build_docs_command(
        build_args, action_override=build_action, source_override=source_override))
    cmd = [_sys.executable, str(repo_root / "tools" / "export_idml.py")]
    if getattr(args, "model", None):
        cmd += ["--model", args.model]
    if getattr(args, "region", None):
        cmd += ["--region", args.region]
    language = _effective_idml_language(args, config_path=context.config_path)
    if language:
        cmd += ["--lang", language]
    if getattr(args, "data_root", None):
        cmd += ["--data-root", args.data_root]
    if mode:
        cmd += ["--mode", mode]
    cmd += ["--layout-params-csv", str(layout_params_csv)]
    for overlay in layout_param_overlays:
        cmd += ["--layout-params-overlay", str(overlay)]
    if assembly_plan is not None:
        cmd += ["--assembly-plan", str(assembly_plan)]
    context.run_checked(cmd)


ACTION_HANDLERS: dict[str, ActionHandler] = {
    "validate": _dispatch_validate_action,
    "idml": _dispatch_idml_action,
    "doctor": _dispatch_doctor_action,
    "asset-check": _dispatch_asset_action,
    "asset-intake": _dispatch_asset_action,
    "new-line": _dispatch_new_line_action,
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
    "release-rebuild-verify": _dispatch_release_rebuild_action,
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
    release_rebuild_command: Callable[[argparse.Namespace], list[str]],
    clean_build_artifacts: Callable[[Path], None],
    maybe_sync_review_before_build: Callable[[argparse.Namespace], None],
    run_asset_command: Callable[[argparse.Namespace], None] | None = None,
    run_new_line: Callable[[argparse.Namespace], None] | None = None,
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
        release_rebuild_command=release_rebuild_command,
        clean_build_artifacts=clean_build_artifacts,
        maybe_sync_review_before_build=maybe_sync_review_before_build,
        run_asset_command=run_asset_command,
        run_new_line=run_new_line,
    )
    context.ensure_supported_staging_action(args)
    ACTION_HANDLERS.get(args.action, _dispatch_build_action)(args, context)
