from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

FAILURE_SUMMARY_PATH_ENV = "AUTO_MANUAL_FAILURE_SUMMARY_PATH"


@dataclass(frozen=True)
class ReviewStartRuntimeDeps:
    root: Path
    review_action_label: str
    cli_bin_fn: Callable[[dict[str, Any]], str]
    phase2_identity_fn: Callable[[], str]
    source_factory: Callable[..., Any]
    collect_preflight_errors_fn: Callable[..., list[str]]
    resolve_binding_fn: Callable[[dict[str, Any]], Any]
    parse_records_fn: Callable[[list[dict[str, Any]]], list[Any]]
    select_pending_records_fn: Callable[..., list[Any]]
    group_records_fn: Callable[[list[Any]], list[list[Any]]]
    validate_group_fn: Callable[[list[Any]], None]
    resolve_target_fn: Callable[[Any], tuple[str, str]]
    group_lang_fn: Callable[[list[Any]], str]
    group_build_family_fn: Callable[[list[Any]], str]
    resolve_config_path_fn: Callable[..., Path]
    record_key_fn: Callable[[Any], str]
    generate_branch_name_fn: Callable[[Any], str]
    sync_snapshot_before_fn: Callable[..., None]
    run_git_fn: Callable[[list[str]], str]
    build_success_fields_fn: Callable[..., dict[str, Any]]
    start_review_for_record_fn: Callable[..., tuple[str, str]]
    build_preflight_failure_summary_fn: Callable[..., dict[str, Any]]
    build_no_pending_failure_summary_fn: Callable[..., dict[str, Any]]
    build_failure_summary_fn: Callable[..., dict[str, Any]]
    build_failure_report_fn: Callable[..., dict[str, Any]]
    environ: dict[str, str]


def _failure_summary_path(*, root: Path, environ: dict[str, str]) -> Path | None:
    raw = str(environ.get(FAILURE_SUMMARY_PATH_ENV, "")).strip()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _clear_failure_summary(*, root: Path, environ: dict[str, str]) -> None:
    path = _failure_summary_path(root=root, environ=environ)
    if path is None:
        return
    try:
        if path.exists():
            path.unlink()
    except OSError as exc:
        print(f"[review-start] Unable to clear failure summary {path}: {exc}", file=sys.stderr)


def _write_failure_summary(*, root: Path, environ: dict[str, str], payload: dict[str, Any]) -> None:
    path = _failure_summary_path(root=root, environ=environ)
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"[review-start] Unable to write failure summary {path}: {exc}", file=sys.stderr)


def _normalized_review_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def _is_completed_review_start_record(record: Any) -> bool:
    # Workflow_action is deliberately NOT checked here: once review-start succeeds,
    # the business plane advances the row's action to later stages (e.g. Build Draft
    # Package) while Git_ref + Review_status keep proving the review exists. A
    # duplicate targeted dispatch must key off that outcome, not the action label.
    status = _normalized_review_status(getattr(record, "review_status", ""))
    git_ref = str(getattr(record, "git_ref", "") or "").strip()
    return bool(git_ref) and status in {"inreview", "readyforpublish"}


def _find_record_by_id(records: list[Any], record_id: str) -> Any | None:
    for record in records:
        if str(getattr(record, "record_id", "") or "").strip() == record_id:
            return record
    return None


def process_review_start_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None,
    dry_run: bool,
    record_id: str | None,
    deps: ReviewStartRuntimeDeps,
) -> int:
    _clear_failure_summary(root=deps.root, environ=deps.environ)
    pending_groups: list[list[Any]] = []
    errors = deps.collect_preflight_errors_fn(cfg, require_github=not dry_run)
    if errors:
        _write_failure_summary(
            root=deps.root,
            environ=deps.environ,
            payload=deps.build_failure_report_fn(
                review_action_label=deps.review_action_label,
                failures=[
                    deps.build_preflight_failure_summary_fn(
                        errors=errors,
                        review_action_label=deps.review_action_label,
                    )
                ],
            ),
        )
        raise RuntimeError("process-review-start-queue preflight failed:\n- " + "\n- ".join(errors))

    binding = deps.resolve_binding_fn(cfg)
    source = deps.source_factory(cli_bin=deps.cli_bin_fn(cfg), identity=deps.phase2_identity_fn())
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
    )
    pending_records = deps.select_pending_records_fn(raw_records, record_id=record_id)
    if not pending_records:
        if record_id:
            existing_record = _find_record_by_id(deps.parse_records_fn(raw_records), record_id)
            if existing_record is not None and _is_completed_review_start_record(existing_record):
                print(
                    "[review-start] Targeted review-start row is already in review; "
                    f"record_id={record_id} git_ref={getattr(existing_record, 'git_ref', '')}. "
                    "Treating duplicate dispatch as success."
                )
                return 0
            _write_failure_summary(
                root=deps.root,
                environ=deps.environ,
                payload=deps.build_failure_report_fn(
                    review_action_label=deps.review_action_label,
                    failures=[
                        deps.build_no_pending_failure_summary_fn(
                            record_id=record_id,
                            review_action_label=deps.review_action_label,
                        )
                    ],
                ),
            )
            print(
                f"[review-start] No pending review-start task found for record_id={record_id}.",
                file=sys.stderr,
            )
            return 1
        print("[review-start] No pending review-start tasks found.")
        return 0
    pending_groups = deps.group_records_fn(pending_records)

    snapshot_data_root = data_root or str((deps.root / ".tmp" / "review-start" / "phase2").resolve())
    if dry_run:
        for group in pending_groups:
            record = group[0]
            deps.validate_group_fn(group)
            model, region = deps.resolve_target_fn(record)
            group_lang = deps.group_lang_fn(group)
            group_build_family = deps.group_build_family_fn(group)
            build_config_path = deps.resolve_config_path_fn(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            print(
                f"[review-start] {deps.review_action_label} DRY-RUN "
                + json.dumps(
                    {
                        "record_ids": [item.record_id for item in group],
                        "record_id": record.record_id,
                        "label": record.label,
                        "document_key": deps.record_key_fn(record),
                        "model": model,
                        "region": region,
                        "build_family": group_build_family,
                        "lang": group_lang,
                        "langs": [item.lang for item in group if item.lang.strip()],
                        "version": record.version,
                        "git_ref": deps.generate_branch_name_fn(record),
                        "workflow_action": deps.review_action_label,
                        "config": str(build_config_path),
                        "data_root": snapshot_data_root,
                    },
                    ensure_ascii=False,
                )
            )
        return 0

    print(f"[review-start] Syncing latest phase2 snapshot before {deps.review_action_label.lower()}.")
    try:
        deps.sync_snapshot_before_fn(config_path=config_path, data_root=snapshot_data_root)
    except Exception as exc:
        target_record = pending_groups[0][0] if len(pending_groups) == 1 and pending_groups[0] else None
        _write_failure_summary(
            root=deps.root,
            environ=deps.environ,
            payload=deps.build_failure_report_fn(
                review_action_label=deps.review_action_label,
                failures=[
                    deps.build_failure_summary_fn(
                        record=target_record,
                        exc=exc,
                        review_action_label=deps.review_action_label,
                    )
                ],
            ),
        )
        raise

    repository = str(deps.environ.get("GITHUB_REPOSITORY", "")).strip()
    token = str(deps.environ.get("GITHUB_TOKEN", "")).strip()
    base_ref = str(deps.environ.get("REVIEW_START_BASE_REF", "main")).strip() or "main"
    deps.run_git_fn(["fetch", "origin", "--prune"])

    failures: list[str] = []
    failure_summaries: list[dict[str, Any]] = []
    processed = 0
    blocked = 0
    for group in pending_groups:
        record = group[0]
        model = ""
        region = ""
        group_lang = ""
        group_build_family = ""
        try:
            deps.validate_group_fn(group)
            model, region = deps.resolve_target_fn(record)
            group_lang = deps.group_lang_fn(group)
            group_build_family = deps.group_build_family_fn(group)
            build_config_path = deps.resolve_config_path_fn(
                region=region,
                lang=group_lang,
                build_family=group_build_family,
            )
            branch_name, pr_url = deps.start_review_for_record_fn(
                record=record,
                build_config_path=build_config_path,
                snapshot_data_root=snapshot_data_root,
                base_ref=base_ref,
                repository=repository,
                token=token,
            )
            success_fields = deps.build_success_fields_fn(git_ref=branch_name, pr_url=pr_url)
            for group_record in group:
                source.upsert_record(
                    base_token=binding.base_token,
                    table_id=binding.table_id,
                    record_id=group_record.record_id,
                    record=success_fields,
                )
            processed += 1
            print(
                f"[review-start] {deps.review_action_label} updated {deps.record_key_fn(record)}: "
                f"family={group_build_family or 'legacy'} git_ref={branch_name} pr_url={pr_url} rows={len(group)}"
            )
        except Exception as exc:
            failures.append(f"{deps.record_key_fn(record)}: {exc}")
            failure_summaries.append(
                deps.build_failure_summary_fn(
                    record=record,
                    exc=exc,
                    review_action_label=deps.review_action_label,
                    model=model,
                    region=region,
                    build_family=group_build_family,
                    lang=group_lang,
                )
            )
            print(
                f"[review-start] {deps.review_action_label} FAILURE {deps.record_key_fn(record)} "
                f"family={deps.group_build_family_fn(group) or 'legacy'}: {exc}",
                file=sys.stderr,
            )

    if failure_summaries:
        _write_failure_summary(
            root=deps.root,
            environ=deps.environ,
            payload=deps.build_failure_report_fn(
                review_action_label=deps.review_action_label,
                failures=failure_summaries,
            ),
        )

    print(
        f"[review-start] {deps.review_action_label} summary: "
        f"processed={processed} blocked={blocked} failed={len(failures)}"
    )
    return 1 if failures else 0
