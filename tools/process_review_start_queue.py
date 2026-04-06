#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import re
import sys
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
    base_ref_contains_target_review_root as _base_ref_contains_target_review_root_impl,
    build_py_command as _build_py_command_impl,
    commit_review_bundle_if_changed as _commit_review_bundle_if_changed_impl,
    configure_git_identity as _configure_git_identity_impl,
    create_empty_review_start_commit as _create_empty_review_start_commit_impl,
    ensure_pull_request_for_branch as _ensure_pull_request_for_branch_impl,
    ensure_review_bundle_on_branch as _ensure_review_bundle_on_branch_impl,
    format_command as _format_command_impl,
    git_object_exists as _git_object_exists_impl,
    git_ref_exists as _git_ref_exists_impl,
    github_api_request as _github_api_request_impl,
    prepare_branch_worktree as _prepare_branch_worktree_impl,
    push_branch as _push_branch_impl,
    remote_branch_exists as _remote_branch_exists_impl,
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
from tools.queue_config_resolution import resolve_config_path_for_task  # noqa: E402

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
REVIEW_START_ACTION_LABEL = "Start Review/Seed Draft"

REVIEW_STATUS_NOT_STARTED = "NotStarted"
REVIEW_STATUS_IN_REVIEW = "InReview"
INITIAL_RESULT_DUPLICATE = "不允许重复创建"
DUPLICATE_REMARKS = "如需强制刷新内容，请在vs通过相关git命令操作，具体详见文档quick_start_guide.md."

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


def _resolve_review_start_config_path(*, region: str, lang: str | None, build_family: str | None) -> Path:
    try:
        return resolve_config_path_for_task(region=region, lang=lang, build_family=build_family)
    except TypeError as exc:
        if "build_family" not in str(exc):
            raise
        return resolve_config_path_for_task(region=region, lang=lang)


def resolve_target_for_review_start(record: ReviewStartRecord) -> tuple[str, str]:
    return _resolve_target_for_review_start_impl(record, parse_document_key=parse_document_key)


def review_start_record_key(record: ReviewStartRecord) -> str:
    return _review_start_record_key_impl(record)


def group_review_start_records(records: list[ReviewStartRecord]) -> list[list[ReviewStartRecord]]:
    return _group_review_start_records_impl(
        records,
        resolve_target_for_review_start=resolve_target_for_review_start,
        resolve_config_path_for_task=_resolve_review_start_config_path,
        load_config=load_config,
    )


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


def build_review_start_duplicate_fields() -> dict[str, Any]:
    return {
        REVIEW_TRIGGER_FIELD: False,
        INITIAL_RESULT_FIELD: INITIAL_RESULT_DUPLICATE,
        REMARKS_FIELD: DUPLICATE_REMARKS,
    }


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


def _git_ref_exists(ref_name: str) -> bool:
    return _git_ref_exists_impl(root=ROOT, ref_name=ref_name)


def _remote_branch_exists(branch_name: str) -> bool:
    return _remote_branch_exists_impl(root=ROOT, branch_name=branch_name)


def _git_object_exists(*, ref_name: str, repo_relative_path: str) -> bool:
    return _git_object_exists_impl(root=ROOT, ref_name=ref_name, repo_relative_path=repo_relative_path)


def base_ref_contains_target_review_root(*, config_path: Path, model: str, region: str, base_ref: str) -> bool:
    return _base_ref_contains_target_review_root_impl(
        root=ROOT,
        config_path=config_path,
        model=model,
        region=region,
        base_ref=base_ref,
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
    errors = collect_review_start_preflight_errors(cfg, require_github=not dry_run)
    if errors:
        raise RuntimeError("process-review-start-queue preflight failed:\n- " + "\n- ".join(errors))

    binding = resolve_review_init_binding(cfg)
    source = LarkCliSource(cli_bin=_cli_bin(cfg), identity=_phase2_identity())
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    pending_records = select_pending_review_start_records(raw_records, record_id=record_id)
    if not pending_records:
        print("[review-start] No pending review-start tasks found.")
        return 0
    pending_groups = group_review_start_records(pending_records)

    snapshot_data_root = data_root or str((ROOT / ".tmp" / "review-start" / "phase2").resolve())
    if dry_run:
        for group in pending_groups:
            record = group[0]
            validate_review_start_group(group)
            model, region = resolve_target_for_review_start(record)
            group_lang = review_start_group_lang(group)
            group_build_family = review_start_group_build_family(group)
            build_config_path = _resolve_review_start_config_path(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            print(
                f"[review-start] {REVIEW_START_ACTION_LABEL} DRY-RUN "
                + json.dumps(
                    {
                        "record_ids": [item.record_id for item in group],
                        "record_id": record.record_id,
                        "label": record.label,
                        "document_key": review_start_record_key(record),
                        "model": model,
                        "region": region,
                        "build_family": group_build_family,
                        "lang": group_lang,
                        "langs": [item.lang for item in group if item.lang.strip()],
                        "version": record.version,
                        "git_ref": generate_review_branch_name(record),
                        "workflow_action": REVIEW_START_ACTION_LABEL,
                        "config": str(build_config_path),
                        "data_root": snapshot_data_root,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    print(f"[review-start] Syncing latest phase2 snapshot before {REVIEW_START_ACTION_LABEL.lower()}.")
    sync_phase2_snapshot_before_review_start(config_path=config_path, data_root=snapshot_data_root)

    repository = str(os.environ.get("GITHUB_REPOSITORY", "")).strip()
    token = str(os.environ.get("GITHUB_TOKEN", "")).strip()
    base_ref = str(os.environ.get("REVIEW_START_BASE_REF", "main")).strip() or "main"
    _run_git(["fetch", "origin", "--prune"])

    failures: list[str] = []
    processed = 0
    blocked = 0
    for group in pending_groups:
        record = group[0]
        try:
            validate_review_start_group(group)
            model, region = resolve_target_for_review_start(record)
            group_lang = review_start_group_lang(group)
            group_build_family = review_start_group_build_family(group)
            build_config_path = _resolve_review_start_config_path(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            if base_ref_contains_target_review_root(
                config_path=build_config_path,
                model=model,
                region=region,
                base_ref=base_ref,
            ):
                duplicate_fields = build_review_start_duplicate_fields()
                for group_record in group:
                    source.upsert_record(
                        base_token=binding.base_token,
                        table_id=binding.table_id,
                        record_id=group_record.record_id,
                        record=duplicate_fields,
                    )
                blocked += 1
                print(
                    f"[review-start] {REVIEW_START_ACTION_LABEL} BLOCKED "
                    f"{review_start_record_key(record)}: review root already exists in origin/{base_ref} "
                    f"for {model}/{region} family={group_build_family or 'legacy'}; updated {len(group)} row(s)"
                )
                continue
            branch_name, pr_url = start_review_for_record(
                record=record,
                build_config_path=build_config_path,
                snapshot_data_root=snapshot_data_root,
                base_ref=base_ref,
                repository=repository,
                token=token,
            )
            success_fields = build_review_start_success_fields(git_ref=branch_name, pr_url=pr_url)
            for group_record in group:
                source.upsert_record(
                    base_token=binding.base_token,
                    table_id=binding.table_id,
                    record_id=group_record.record_id,
                    record=success_fields,
                )
            processed += 1
            print(
                f"[review-start] {REVIEW_START_ACTION_LABEL} updated {review_start_record_key(record)}: "
                f"family={group_build_family or 'legacy'} git_ref={branch_name} pr_url={pr_url} rows={len(group)}"
            )
        except Exception as exc:
            failures.append(f"{review_start_record_key(record)}: {exc}")
            print(
                f"[review-start] {REVIEW_START_ACTION_LABEL} FAILURE {review_start_record_key(record)} "
                f"family={review_start_group_build_family(group) or 'legacy'}: {exc}",
                file=sys.stderr,
            )

    print(
        f"[review-start] {REVIEW_START_ACTION_LABEL} summary: "
        f"processed={processed} blocked={blocked} failed={len(failures)}"
    )
    return 1 if failures else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Consume Review-init rows and start review / seed draft branches and PRs.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--data-root", default=None, help="Override phase2 snapshot root for review seeding")
    ap.add_argument("--dry-run", action="store_true", help="List pending rows without creating branches or PRs")
    ap.add_argument("--record-id", default=None, help="Only consume one Review-init record_id")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    cfg = load_config(config_path)
    resolved_data_root = str(
        resolve_phase2_export_root(
            cfg,
            repo_root=ROOT,
            data_root=args.data_root,
        )
    )
    return process_review_start_queue(
        cfg=cfg,
        config_path=config_path,
        data_root=resolved_data_root,
        dry_run=args.dry_run,
        record_id=args.record_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
