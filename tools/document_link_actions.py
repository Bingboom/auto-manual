from __future__ import annotations

import json
import re
import sys
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
    return not _scalar_text(workflow_action) and bool(_scalar_text(doc_phase))


def workflow_action_source(*, workflow_action: Any, doc_phase: Any) -> str:
    if _scalar_text(workflow_action):
        return "Workflow_action"
    if workflow_action_uses_legacy_doc_phase(workflow_action=workflow_action, doc_phase=doc_phase):
        return "Doc_phase (legacy)"
    return "Unspecified"


def legacy_doc_phase_value(*, workflow_action: Any, doc_phase: Any) -> str | None:
    if not workflow_action_uses_legacy_doc_phase(workflow_action=workflow_action, doc_phase=doc_phase):
        return None
    text = _scalar_text(doc_phase)
    return text or None


def resolve_workflow_action(
    *,
    workflow_action: Any,
    doc_phase: Any,
    record_id: str | None = None,
) -> str | None:
    normalized_workflow_action = normalize_workflow_action(workflow_action)
    normalized_doc_phase = normalize_doc_phase(doc_phase)
    if normalized_workflow_action and normalized_doc_phase and normalized_workflow_action != normalized_doc_phase:
        detail = f" for queue record {record_id}" if (record_id or "").strip() else ""
        raise RuntimeError(
            "Workflow_action conflicts with Doc_phase"
            f"{detail}: {workflow_action!r} vs {doc_phase!r}"
        )
    return normalized_workflow_action or normalized_doc_phase


def workflow_action_label(value: Any) -> str | None:
    normalized_doc_phase = normalize_workflow_action(value)
    if normalized_doc_phase == "draft":
        return DRAFT_PACKAGE_ACTION_LABEL
    if normalized_doc_phase == "publish":
        return PUBLISH_ACTION_LABEL
    return None


def normalize_cli_queue_action(*, workflow_action: str | None = None, doc_phase: str | None = None) -> str | None:
    normalized_workflow_action = normalize_workflow_action(workflow_action)
    normalized_doc_phase = normalize_doc_phase(doc_phase)
    if normalized_workflow_action and normalized_doc_phase and normalized_workflow_action != normalized_doc_phase:
        raise RuntimeError(
            "--workflow-action conflicts with --doc-phase: "
            f"{workflow_action!r} vs {doc_phase!r}"
        )
    return normalized_workflow_action or normalized_doc_phase


def warn_legacy_cli_doc_phase(doc_phase: str | None, workflow_action: str | None) -> None:
    if (doc_phase or "").strip() and not (workflow_action or "").strip():
        print(
            "[build-queue] WARNING --doc-phase is deprecated; use --workflow-action instead.",
            file=sys.stderr,
        )


def warn_legacy_record_doc_phase(
    *,
    record_id: str,
    workflow_action: Any,
    doc_phase: Any,
) -> None:
    legacy_doc_phase = legacy_doc_phase_value(workflow_action=workflow_action, doc_phase=doc_phase)
    if not legacy_doc_phase:
        return
    print(
        "[build-queue] WARNING "
        f"record {record_id} is still using legacy Doc_phase={legacy_doc_phase!r}; "
        "set Workflow_action instead.",
        file=sys.stderr,
    )


def best_effort_queue_workflow_action(
    *,
    workflow_action: Any,
    doc_phase: Any,
    record_id: str | None = None,
) -> str | None:
    try:
        return resolve_workflow_action(
            workflow_action=workflow_action,
            doc_phase=doc_phase,
            record_id=record_id,
        )
    except RuntimeError:
        try:
            normalized_workflow_action = normalize_workflow_action(workflow_action)
        except RuntimeError:
            normalized_workflow_action = None
        if normalized_workflow_action:
            return normalized_workflow_action
        try:
            return normalize_doc_phase(doc_phase)
        except RuntimeError:
            return None
