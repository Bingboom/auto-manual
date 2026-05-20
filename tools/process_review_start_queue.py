#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.data_snapshot import resolve_phase2_export_root  # noqa: E402
from tools.document_link_queue import parse_document_key  # noqa: E402
from tools.phase2_support import (  # noqa: E402
    LarkCliSource,
    cli_bin as _cli_bin,
    cli_command_exists as _cli_command_exists,
    cli_command_parts as _cli_command_parts,
    env_value as _env_value,
    load_config,
    phase2_identity as _phase2_identity,
    provider_name as _provider_name,
    sync_phase2_cfg as _sync_phase2_cfg,
)
from tools.process_review_start_queue_binding import (  # noqa: E402
    ReviewInitBinding,
    collect_review_start_preflight_errors as _collect_review_start_preflight_errors_impl,
    resolve_review_init_binding as _resolve_review_init_binding_impl,
    review_init_env_names as _review_init_env_names_impl,
)
from tools.process_review_start_queue_records import (  # noqa: E402
    ReviewStartRecord,
    generate_review_branch_name as _generate_review_branch_name_impl,
    group_review_start_records as _group_review_start_records_impl,
    normalize_review_start_action as _normalize_review_start_action_impl,
    normalize_review_status as _normalize_review_status_impl,
    parse_review_start_records as _parse_review_start_records_impl,
    review_start_group_build_family as _review_start_group_build_family_impl,
    review_start_group_lang as _review_start_group_lang_impl,
    review_start_record_key as _review_start_record_key_impl,
    resolve_target_for_review_start as _resolve_target_for_review_start_impl,
    select_pending_review_start_records as _select_pending_review_start_records_impl,
    validate_review_start_group as _validate_review_start_group_impl,
)
from tools.process_review_start_queue_git import (  # noqa: E402
    build_py_command as _build_py_command_impl,
    commit_review_bundle_if_changed as _commit_review_bundle_if_changed_impl,
    configure_git_identity as _configure_git_identity_impl,
    create_empty_review_start_commit as _create_empty_review_start_commit_impl,
    ensure_pull_request_for_branch as _ensure_pull_request_for_branch_impl,
    ensure_review_bundle_on_branch as _ensure_review_bundle_on_branch_impl,
    format_command as _format_command_impl,
    github_api_request as _github_api_request_impl,
    prepare_branch_worktree as _prepare_branch_worktree_impl,
    push_branch as _push_branch_impl,
    remove_worktree as _remove_worktree_impl,
    resolve_docs_dir_for_config as _resolve_docs_dir_for_config_impl,
    review_dir_for_target_config as _review_dir_for_target_impl,
    review_root_for_target_config as _review_root_for_target_impl,
    run_command as _run_command_impl,
    run_git as _run_git_impl,
    start_review_for_record as _start_review_for_record_impl,
    sync_phase2_snapshot_before_review_start as _sync_phase2_snapshot_before_review_start_impl,
    worktree_dir_for_branch as _worktree_dir_for_branch_impl,
)
from tools.process_review_start_queue_entry import parse_args as _parse_args_impl, run_main as _run_main_impl  # noqa: E402
from tools.process_review_start_queue_runtime import (  # noqa: E402
    ReviewStartRuntimeDeps,
    process_review_start_queue as _process_review_start_queue_impl,
)
from tools.queue_config_resolution import resolve_config_path_for_task  # noqa: E402
from tools.region_aliases import canonical_document_key_region  # noqa: E402
from tools.review_start_failure_summary import (  # noqa: E402
    build_review_start_failure_report as _build_review_start_failure_report_impl,
    build_review_start_failure_summary as _build_review_start_failure_summary_impl,
    build_review_start_no_pending_summary as _build_review_start_no_pending_summary_impl,
    build_review_start_preflight_failure_summary as _build_review_start_preflight_failure_summary_impl,
)

REVIEW_TRIGGER_FIELD = "\u662f\u5426\u8fdb\u5165Review"
REVIEW_STATUS_FIELD = "Review_status"
GIT_REF_FIELD = "Git_ref"
PR_URL_FIELD = "PR_url"
DOCUMENT_ID_FIELD = "Document_ID"
DOCUMENT_KEY_FIELD = "Document_Key"
BUILD_FAMILY_FIELD = "Build_family"
VERSION_FIELD = "Version"
LANG_FIELD = "Lang"
WORKFLOW_ACTION_FIELD = "Workflow_action"
INITIAL_RESULT_FIELD = "Initial_result"
REMARKS_FIELD = "Remarks"
REVIEW_START_ACTION_LABEL = "Start Review"

REVIEW_STATUS_NOT_STARTED = "NotStarted"
REVIEW_STATUS_IN_REVIEW = "InReview"
def _review_init_env_names(cfg: dict[str, Any]) -> tuple[str, str, str | None]:
    return _review_init_env_names_impl(cfg, sync_phase2_cfg=_sync_phase2_cfg)


def collect_review_start_preflight_errors(cfg: dict[str, Any], *, require_github: bool = True) -> list[str]:
    return _collect_review_start_preflight_errors_impl(
        cfg,
        require_github=require_github,
        provider_name=_provider_name,
        cli_bin=_cli_bin,
        cli_command_parts=_cli_command_parts,
        cli_command_exists=_cli_command_exists,
        review_init_env_names=_review_init_env_names,
        environ=os.environ,
    )


def resolve_review_init_binding(cfg: dict[str, Any]) -> ReviewInitBinding:
    return _resolve_review_init_binding_impl(
        cfg,
        review_init_env_names=_review_init_env_names,
        env_value=_env_value,
    )


def normalize_review_status(value: Any) -> str | None:
    return _normalize_review_status_impl(value)


def normalize_review_start_action(value: Any) -> str | None:
    return _normalize_review_start_action_impl(value)


def parse_review_start_records(raw_records: list[dict[str, Any]]) -> list[ReviewStartRecord]:
    return _parse_review_start_records_impl(raw_records)


def select_pending_review_start_records(
    raw_records: list[dict[str, Any]],
    *,
    record_id: str | None = None,
) -> list[ReviewStartRecord]:
    return _select_pending_review_start_records_impl(raw_records, record_id=record_id)


def _slug_branch_token(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return text or "review"


def generate_review_branch_name(record: ReviewStartRecord) -> str:
    return _generate_review_branch_name_impl(record)


def _resolve_review_start_region_config_path(*, region: str) -> Path | None:
    normalized_region = canonical_document_key_region(str(region or "").strip())
    if not normalized_region:
        return None

    candidates: list[tuple[int, Path]] = []
    for config_path in sorted(ROOT.glob("config*.yaml")):
        try:
            cfg = load_config(config_path)
        except RuntimeError:
            continue
        build_cfg_raw = cfg.get("build", {})
        build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
        default_region = canonical_document_key_region(str(build_cfg.get("default_region") or "").strip())
        if default_region != normalized_region:
            continue
        languages_raw = build_cfg.get("languages", [])
        if isinstance(languages_raw, (list, tuple)):
            languages = [str(item).strip().lower() for item in languages_raw if str(item).strip()]
        else:
            languages = [str(languages_raw).strip().lower()] if str(languages_raw).strip() else []
        score = 0
        if bool(build_cfg.get("queue_by_document_key")):
            score += 100
        if len(languages) == 1:
            score += 10
        if not bool(build_cfg.get("include_lang_in_output_path")):
            score += 5
        if normalized_region.lower() in config_path.name.lower():
            score += 1
        candidates.append((score, config_path))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1].name))
    best_score = candidates[0][0]
    best_paths = [path for score, path in candidates if score == best_score]
    if len(best_paths) > 1:
        names = ", ".join(path.name for path in best_paths)
        raise RuntimeError(
            f"Review-start config resolution is ambiguous for region={normalized_region!r}: {names}"
        )
    return candidates[0][1]


def _fallback_review_start_config_path(
    *,
    region: str,
    lang: str | None,
    build_family: str | None,
    exc: RuntimeError,
) -> Path:
    if str(lang or "").strip() or str(build_family or "").strip():
        raise exc
    fallback = _resolve_review_start_region_config_path(region=region)
    if fallback is None:
        raise exc
    return fallback


def _resolve_review_start_config_path(*, region: str, lang: str | None, build_family: str | None) -> Path:
    try:
        return resolve_config_path_for_task(
            repo_root=ROOT,
            region=region,
            lang=lang,
            build_family=build_family,
            config_loader=load_config,
        )
    except RuntimeError as exc:
        return _fallback_review_start_config_path(
            region=region,
            lang=lang,
            build_family=build_family,
            exc=exc,
        )
    except TypeError as exc:
        message = str(exc)
        if not any(name in message for name in ("repo_root", "config_loader", "build_family")):
            raise
    try:
        return resolve_config_path_for_task(region=region, lang=lang, build_family=build_family)
    except RuntimeError as exc:
        return _fallback_review_start_config_path(
            region=region,
            lang=lang,
            build_family=build_family,
            exc=exc,
        )
    except TypeError as exc:
        if "build_family" not in str(exc):
            raise
        try:
            return resolve_config_path_for_task(region=region, lang=lang)
        except RuntimeError as runtime_exc:
            return _fallback_review_start_config_path(
                region=region,
                lang=lang,
                build_family=build_family,
                exc=runtime_exc,
            )


def resolve_target_for_review_start(record: ReviewStartRecord) -> tuple[str, str]:
    return _resolve_target_for_review_start_impl(record, parse_document_key=parse_document_key)


def review_start_record_key(record: ReviewStartRecord) -> str:
    return _review_start_record_key_impl(record)


def group_review_start_records(records: list[ReviewStartRecord]) -> list[list[ReviewStartRecord]]:
    return _group_review_start_records_impl(records)


def review_start_group_build_family(records: list[ReviewStartRecord]) -> str:
    return _review_start_group_build_family_impl(records)


def review_start_group_lang(records: list[ReviewStartRecord]) -> str:
    return _review_start_group_lang_impl(records)


def validate_review_start_group(records: list[ReviewStartRecord]) -> None:
    _validate_review_start_group_impl(records)


def build_review_start_success_fields(*, git_ref: str, pr_url: str) -> dict[str, Any]:
    return {
        REVIEW_STATUS_FIELD: [REVIEW_STATUS_IN_REVIEW],
        REVIEW_TRIGGER_FIELD: False,
        GIT_REF_FIELD: git_ref,
        PR_URL_FIELD: pr_url,
    }


def build_review_start_preflight_failure_summary(*, errors: list[str], review_action_label: str) -> dict[str, Any]:
    return _build_review_start_preflight_failure_summary_impl(
        errors=errors,
        review_action_label=review_action_label,
    )


def build_review_start_no_pending_failure_summary(*, record_id: str, review_action_label: str) -> dict[str, Any]:
    return _build_review_start_no_pending_summary_impl(
        record_id=record_id,
        review_action_label=review_action_label,
    )


def build_review_start_failure_summary(
    *,
    record: ReviewStartRecord | None,
    exc: BaseException | str,
    review_action_label: str,
    model: str = "",
    region: str = "",
    build_family: str = "",
    lang: str = "",
) -> dict[str, Any]:
    return _build_review_start_failure_summary_impl(
        record=record,
        exc=exc,
        review_action_label=review_action_label,
        model=model,
        region=region,
        build_family=build_family,
        lang=lang,
        version=getattr(record, "version", "") if record is not None else "",
    )


def build_review_start_failure_report(*, review_action_label: str, failures: list[dict[str, Any]]) -> dict[str, Any]:
    return _build_review_start_failure_report_impl(
        review_action_label=review_action_label,
        failures=failures,
    )


def _format_command(cmd: list[str]) -> str:
    return _format_command_impl(cmd)


def _run_command(cmd: list[str], *, cwd: Path = ROOT) -> str:
    return _run_command_impl(cmd, root=ROOT, cwd=cwd)


def _run_git(args: list[str], *, cwd: Path = ROOT) -> str:
    return _run_git_impl(args, root=ROOT, cwd=cwd)


def _build_py_command(
    worktree: Path,
    *,
    action: str,
    config_path: Path,
    model: str | None = None,
    region: str | None = None,
    data_root: str | None = None,
    source: str | None = None,
) -> list[str]:
    return _build_py_command_impl(
        worktree,
        action=action,
        config_path=config_path,
        model=model,
        region=region,
        data_root=data_root,
        source=source,
    )


def sync_phase2_snapshot_before_review_start(*, config_path: Path, data_root: str | None) -> None:
    _sync_phase2_snapshot_before_review_start_impl(root=ROOT, config_path=config_path, data_root=data_root)


def _resolve_docs_dir_for_config(config_path: Path, cfg: dict[str, Any] | None = None) -> Path:
    return _resolve_docs_dir_for_config_impl(
        root=ROOT,
        config_path=config_path,
        cfg=cfg,
        load_config_fn=load_config,
    )


def _review_dir_for_target(config_path: Path, *, model: str, region: str) -> Path:
    return _review_dir_for_target_impl(
        root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        load_config_fn=load_config,
    )


def _review_root_for_target(config_path: Path, *, model: str, region: str) -> Path:
    return _review_root_for_target_impl(
        root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        load_config_fn=load_config,
    )


def _worktree_dir_for_branch(branch_name: str) -> Path:
    return _worktree_dir_for_branch_impl(root=ROOT, branch_name=branch_name, slug_branch_token_fn=_slug_branch_token)


def _remove_worktree(path: Path) -> None:
    _remove_worktree_impl(root=ROOT, path=path)


def _prepare_branch_worktree(*, branch_name: str, base_ref: str) -> Path:
    return _prepare_branch_worktree_impl(
        root=ROOT,
        branch_name=branch_name,
        base_ref=base_ref,
        slug_branch_token_fn=_slug_branch_token,
    )


def _configure_git_identity(worktree: Path) -> None:
    _configure_git_identity_impl(worktree=worktree, root=ROOT)


def ensure_review_bundle_on_branch(
    *,
    worktree: Path,
    build_config_path: Path,
    model: str,
    region: str,
    data_root: str | None,
) -> Path:
    return _ensure_review_bundle_on_branch_impl(
        root=ROOT,
        worktree=worktree,
        build_config_path=build_config_path,
        model=model,
        region=region,
        data_root=data_root,
        load_config_fn=load_config,
    )


def _commit_review_bundle_if_changed(*, worktree: Path, review_dir: Path, record: ReviewStartRecord) -> bool:
    return _commit_review_bundle_if_changed_impl(root=ROOT, worktree=worktree, review_dir=review_dir, record=record)


def _push_branch(*, worktree: Path, branch_name: str) -> None:
    _push_branch_impl(root=ROOT, worktree=worktree, branch_name=branch_name)


def _create_empty_review_start_commit(*, worktree: Path, record: ReviewStartRecord) -> None:
    _create_empty_review_start_commit_impl(root=ROOT, worktree=worktree, record=record)


def _github_api_request(*, method: str, path: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _github_api_request_impl(method=method, path=path, token=token, payload=payload)


def ensure_pull_request_for_branch(
    *,
    repository: str,
    branch_name: str,
    base_ref: str,
    token: str,
    record: ReviewStartRecord,
    worktree: Path | None = None,
) -> str:
    return _ensure_pull_request_for_branch_impl(
        root=ROOT,
        repository=repository,
        branch_name=branch_name,
        base_ref=base_ref,
        token=token,
        record=record,
        worktree=worktree,
    )


def start_review_for_record(
    *,
    record: ReviewStartRecord,
    build_config_path: Path,
    snapshot_data_root: str | None,
    base_ref: str,
    repository: str,
    token: str,
) -> tuple[str, str]:
    return _start_review_for_record_impl(
        root=ROOT,
        record=record,
        build_config_path=build_config_path,
        snapshot_data_root=snapshot_data_root,
        base_ref=base_ref,
        repository=repository,
        token=token,
        slug_branch_token_fn=_slug_branch_token,
        resolve_target_for_review_start_fn=resolve_target_for_review_start,
        generate_review_branch_name_fn=generate_review_branch_name,
        load_config_fn=load_config,
    )


def process_review_start_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None,
    dry_run: bool,
    record_id: str | None = None,
) -> int:
    return _process_review_start_queue_impl(
        cfg=cfg,
        config_path=config_path,
        data_root=data_root,
        dry_run=dry_run,
        record_id=record_id,
        deps=ReviewStartRuntimeDeps(
            root=ROOT,
            review_action_label=REVIEW_START_ACTION_LABEL,
            cli_bin_fn=_cli_bin,
            phase2_identity_fn=_phase2_identity,
            source_factory=lambda *, cli_bin, identity: LarkCliSource(cli_bin=cli_bin, identity=identity),
            collect_preflight_errors_fn=collect_review_start_preflight_errors,
            resolve_binding_fn=resolve_review_init_binding,
            parse_records_fn=parse_review_start_records,
            select_pending_records_fn=select_pending_review_start_records,
            group_records_fn=group_review_start_records,
            validate_group_fn=validate_review_start_group,
            resolve_target_fn=resolve_target_for_review_start,
            group_lang_fn=review_start_group_lang,
            group_build_family_fn=review_start_group_build_family,
            resolve_config_path_fn=_resolve_review_start_config_path,
            record_key_fn=review_start_record_key,
            generate_branch_name_fn=generate_review_branch_name,
            sync_snapshot_before_fn=sync_phase2_snapshot_before_review_start,
            run_git_fn=_run_git,
            build_success_fields_fn=build_review_start_success_fields,
            start_review_for_record_fn=start_review_for_record,
            build_preflight_failure_summary_fn=build_review_start_preflight_failure_summary,
            build_no_pending_failure_summary_fn=build_review_start_no_pending_failure_summary,
            build_failure_summary_fn=build_review_start_failure_summary,
            build_failure_report_fn=build_review_start_failure_report,
            environ=os.environ,
        ),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return _parse_args_impl(argv)


def main(argv: list[str] | None = None) -> int:
    return _run_main_impl(
        argv,
        root=ROOT,
        load_config_fn=load_config,
        resolve_phase2_export_root_fn=resolve_phase2_export_root,
        process_review_start_queue_fn=process_review_start_queue,
    )


if __name__ == "__main__":
    raise SystemExit(main())
