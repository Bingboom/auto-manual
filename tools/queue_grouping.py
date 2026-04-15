from __future__ import annotations

from typing import Any, Callable


def group_pending_queue_records(
    records: list[Any],
    *,
    resolve_target_for_record: Callable[[Any], tuple[str, str]],
    resolve_config_path_for_task: Callable[..., Any],
    config_loader: Callable[[Any], dict[str, Any]],
    queue_by_document_key: Callable[[dict[str, Any]], bool],
    queue_record_group_key: Callable[[Any], str],
    resolve_queue_workflow_action: Callable[[Any], str | None],
) -> list[list[Any]]:
    grouped: list[list[Any]] = []
    index_by_key: dict[str, int] = {}
    for record in records:
        model, region = resolve_target_for_record(record)
        config_path = resolve_config_path_for_task(
            region=region,
            lang=record.lang,
            build_family=record.build_family,
            workflow_action=resolve_queue_workflow_action(record),
        )
        cfg = config_loader(config_path)
        if queue_by_document_key(cfg):
            key = queue_record_group_key(record)
        else:
            key = record.record_id
        existing_index = index_by_key.get(key)
        if existing_index is None:
            index_by_key[key] = len(grouped)
            grouped.append([record])
            continue
        grouped[existing_index].append(record)
    return grouped
