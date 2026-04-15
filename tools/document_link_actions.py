from __future__ import annotations

import json
import re
from typing import Any

DRAFT_PACKAGE_ACTION_LABEL = "Build Draft Package"
PUBLISH_ACTION_LABEL = "Publish"


def _scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        for item in value:
            text = _scalar_text(item)
            if text:
                return text
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, "g")
    if isinstance(value, dict):
        for key in ("text", "name", "label", "title", "value"):
            text = _scalar_text(value.get(key))
            if text:
                return text
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value).strip()


def normalize_workflow_action(value: Any) -> str | None:
    text = re.sub(r"[^a-z0-9]+", " ", _scalar_text(value).strip().lower()).strip()
    if not text:
        return None
    if text in {
        "build draft package",
        "build draft",
        "build_draft_package",
        "draft",
        "review",
        "preview",
        "draft package",
    }:
        return "draft"
    if text in {"publish", "published"}:
        return "publish"
    raise RuntimeError("Workflow_action must map to Build Draft Package or Publish")


def normalize_doc_phase(value: Any) -> str | None:
    try:
        return normalize_workflow_action(value)
    except RuntimeError as exc:
        raise RuntimeError("Doc_phase must map to Build Draft Package or Publish") from exc


def workflow_action_uses_legacy_doc_phase(*, workflow_action: Any, doc_phase: Any) -> bool:
    return False


def workflow_action_source(*, workflow_action: Any, doc_phase: Any) -> str:
    if _scalar_text(workflow_action):
        return "Workflow_action"
    if _scalar_text(doc_phase):
        return "Doc_phase (ignored)"
    return "Unspecified"


def legacy_doc_phase_value(*, workflow_action: Any, doc_phase: Any) -> str | None:
    return None


def resolve_workflow_action(
    *,
    workflow_action: Any,
    doc_phase: Any,
    record_id: str | None = None,
) -> str | None:
    normalized_workflow_action = normalize_workflow_action(workflow_action)
    if normalized_workflow_action:
        return normalized_workflow_action
    if _scalar_text(doc_phase):
        detail = f" for queue record {record_id}" if (record_id or "").strip() else ""
        raise RuntimeError(
            "Workflow_action is required"
            f"{detail}; Doc_phase is ignored"
        )
    return None


def workflow_action_label(value: Any) -> str | None:
    normalized_doc_phase = normalize_workflow_action(value)
    if normalized_doc_phase == "draft":
        return DRAFT_PACKAGE_ACTION_LABEL
    if normalized_doc_phase == "publish":
        return PUBLISH_ACTION_LABEL
    return None


def normalize_cli_queue_action(*, workflow_action: str | None = None, doc_phase: str | None = None) -> str | None:
    normalized_workflow_action = normalize_workflow_action(workflow_action)
    if normalized_workflow_action:
        return normalized_workflow_action
    if (doc_phase or "").strip():
        raise RuntimeError("--doc-phase is no longer supported; use --workflow-action")
    return None


def warn_legacy_cli_doc_phase(doc_phase: str | None, workflow_action: str | None) -> None:
    return None


def warn_legacy_record_doc_phase(
    *,
    record_id: str,
    workflow_action: Any,
    doc_phase: Any,
) -> None:
    return None


def best_effort_queue_workflow_action(
    *,
    workflow_action: Any,
    doc_phase: Any,
    record_id: str | None = None,
) -> str | None:
    try:
        return normalize_workflow_action(workflow_action)
    except RuntimeError:
        return None
