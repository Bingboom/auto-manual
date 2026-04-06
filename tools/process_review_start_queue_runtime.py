from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class ReviewStartRuntimeDeps:
    root: Path
    review_action_label: str
    cli_bin_fn: Callable[[dict[str, Any]], str]
    phase2_identity_fn: Callable[[], str]
    source_factory: Callable[..., Any]
    collect_preflight_errors_fn: Callable[..., list[str]]
    resolve_binding_fn: Callable[[dict[str, Any]], Any]
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
    base_ref_contains_target_review_root_fn: Callable[..., bool]
    build_duplicate_fields_fn: Callable[[], dict[str, Any]]
    build_success_fields_fn: Callable[..., dict[str, Any]]
    start_review_for_record_fn: Callable[..., tuple[str, str]]
    environ: dict[str, str]


def process_review_start_queue(
    *,
    cfg: dict[str, Any],
    config_path: Path,
    data_root: str | None,
    dry_run: bool,
    record_id: str | None,
    deps: ReviewStartRuntimeDeps,
) -> int:
    errors = deps.collect_preflight_errors_fn(cfg, require_github=not dry_run)
    if errors:
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
    deps.sync_snapshot_before_fn(config_path=config_path, data_root=snapshot_data_root)

    repository = str(deps.environ.get("GITHUB_REPOSITORY", "")).strip()
    token = str(deps.environ.get("GITHUB_TOKEN", "")).strip()
    base_ref = str(deps.environ.get("REVIEW_START_BASE_REF", "main")).strip() or "main"
    deps.run_git_fn(["fetch", "origin", "--prune"])

    failures: list[str] = []
    processed = 0
    blocked = 0
    for group in pending_groups:
        record = group[0]
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
            if deps.base_ref_contains_target_review_root_fn(
                config_path=build_config_path,
                model=model,
                region=region,
                base_ref=base_ref,
            ):
                duplicate_fields = deps.build_duplicate_fields_fn()
                for group_record in group:
                    source.upsert_record(
                        base_token=binding.base_token,
                        table_id=binding.table_id,
                        record_id=group_record.record_id,
                        record=duplicate_fields,
                    )
                blocked += 1
                print(
                    f"[review-start] {deps.review_action_label} BLOCKED "
                    f"{deps.record_key_fn(record)}: review root already exists in origin/{base_ref} "
                    f"for {model}/{region} family={group_build_family or 'legacy'}; updated {len(group)} row(s)"
                )
                continue
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
            print(
                f"[review-start] {deps.review_action_label} FAILURE {deps.record_key_fn(record)} "
                f"family={deps.group_build_family_fn(group) or 'legacy'}: {exc}",
                file=sys.stderr,
            )

    print(
        f"[review-start] {deps.review_action_label} summary: "
        f"processed={processed} blocked={blocked} failed={len(failures)}"
    )
    return 1 if failures else 0
