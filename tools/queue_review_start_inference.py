from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from tools.document_link_queue import parse_document_key
from tools.phase2_support import load_config as default_load_config
from tools.process_review_start_queue_records import (
    document_key_from_document_id as review_start_document_key_from_document_id,
    document_key_from_task_id as review_start_document_key_from_task_id,
)
from tools.queue_config_resolution import (
    config_family_id,
    resolve_review_start_config_path_for_target,
)

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[1]


def review_start_target_candidates(parsed: Any) -> list[str]:
    candidates: list[str] = []
    for candidate in (
        parsed.document_key,
        review_start_document_key_from_document_id(
            document_id=parsed.document_id,
            lang=parsed.lang,
            version=parsed.version,
        ),
        review_start_document_key_from_task_id(parsed.task_id),
    ):
        text = str(candidate or "").strip()
        if text and text not in candidates:
            candidates.append(text)
    return candidates


def infer_review_start_build_family(
    parsed: Any,
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    config_loader: Callable[[Path], dict[str, Any]] = default_load_config,
) -> str:
    if parsed.build_family:
        return parsed.build_family
    for candidate in review_start_target_candidates(parsed):
        try:
            _model, region = parse_document_key(candidate)
            config_path = resolve_review_start_config_path_for_target(
                repo_root=repo_root,
                region=region,
                lang=parsed.lang,
                build_family="",
                config_loader=config_loader,
            )
            return config_family_id(config_loader(config_path))
        except RuntimeError:
            continue
    return ""
