from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def print_dry_run_groups(
    *,
    groups: list[list[Any]],
    data_root: str | None,
    warn_legacy_record_doc_phase: Callable[[Any], None],
    resolve_target_for_record: Callable[[Any], tuple[str, str]],
    queue_group_lang: Callable[[list[Any]], str],
    queue_group_build_family: Callable[[list[Any]], str],
    validate_queue_record_group: Callable[[list[Any]], None],
    resolve_config_path_for_task: Callable[..., Path],
    queue_record_key: Callable[[Any], str],
    workflow_action_label: Callable[[str | None], str | None],
    queue_record_action_source: Callable[[Any], str],
    queue_record_legacy_doc_phase: Callable[[Any], str | None],
    resolve_queue_workflow_action: Callable[[Any], str | None],
) -> None:
    for group in groups:
        record = group[0]
        warn_legacy_record_doc_phase(record)
        model, region = resolve_target_for_record(record)
        group_lang = queue_group_lang(group)
        group_build_family = queue_group_build_family(group)
        validate_queue_record_group(group)
        effective_doc_phase = resolve_queue_workflow_action(record)
        resolved_config_path = resolve_config_path_for_task(
            region=region,
            lang=group_lang,
            build_family=group_build_family,
            workflow_action=effective_doc_phase,
        )
        print(
            "[build-queue] DRY-RUN "
            + json.dumps(
                {
                    "record_ids": [item.record_id for item in group],
                    "record_id": record.record_id,
                    "label": record.label,
                    "document_key": queue_record_key(record),
                    "model": model,
                    "region": region,
                    "lang": group_lang,
                    "build_family": group_build_family,
                    "langs": [item.lang for item in group if item.lang.strip()],
                    "version": record.version,
                    "workflow_action": workflow_action_label(record.workflow_action or record.doc_phase) or "Legacy/Unspecified",
                    "workflow_action_source": queue_record_action_source(record),
                    "legacy_doc_phase": queue_record_legacy_doc_phase(record),
                    "git_ref": record.git_ref,
                    "config": str(resolved_config_path),
                    "data_root": data_root,
                },
                ensure_ascii=False,
            )
        )
