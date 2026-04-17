from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _document_target(record: Any | None, *, model: str, region: str) -> str:
    normalized_model = _text(model)
    normalized_region = _text(region)
    if normalized_model and normalized_region:
        return f"{normalized_model}_{normalized_region}"
    document_key = _text(getattr(record, "document_key", ""))
    if document_key and not document_key.startswith("{"):
        return document_key
    document_id = _text(getattr(record, "document_id", ""))
    if document_id:
        return document_id
    label = _text(getattr(record, "label", ""))
    if label:
        return label
    record_id = _text(getattr(record, "record_id", ""))
    return record_id or "当前任务"


def _detail_lines(exc: BaseException | str) -> list[str]:
    raw = _text(exc)
    return [line.strip() for line in raw.splitlines() if line.strip()]


def build_review_start_preflight_failure_summary(
    *,
    errors: list[str],
    review_action_label: str,
) -> dict[str, Any]:
    detail_lines = [str(item).strip() for item in errors if str(item).strip()]
    return {
        "code": "review_start_preflight_failed",
        "message": "Review 前置检查失败，当前无法进入 review。",
        "detail": "\n".join(detail_lines),
        "next_step": "请检查 GitHub 凭据、飞书绑定和 worker 环境配置。",
        "workflow_action": review_action_label,
        "retryable": False,
    }


def build_review_start_no_pending_summary(
    *,
    record_id: str,
    review_action_label: str,
) -> dict[str, Any]:
    normalized_record_id = _text(record_id)
    return {
        "code": "review_start_target_not_pending",
        "message": f"当前 Feishu 视图里没有找到 record_id={normalized_record_id} 对应的待进入 review 记录。",
        "detail": (
            f"record_id={normalized_record_id} was not returned as a pending review-start row. "
            "The row may be outside the bound view, not visible to the current Feishu identity, "
            "or no longer satisfies 是否进入Review=true with Workflow_action=Start Review."
        ),
        "next_step": "请检查 GitHub secrets 里的 table/view 绑定、bot 权限，以及该记录当前是否仍勾选 是否进入Review 且 Workflow_action=Start Review。",
        "workflow_action": review_action_label,
        "record_id": normalized_record_id,
        "retryable": True,
    }


def build_review_start_failure_summary(
    *,
    record: Any | None,
    exc: BaseException | str,
    review_action_label: str,
    model: str = "",
    region: str = "",
    build_family: str = "",
    lang: str = "",
    version: str = "",
) -> dict[str, Any]:
    detail_lines = _detail_lines(exc)
    detail = "\n".join(detail_lines)
    target = _document_target(record, model=model, region=region)
    code = "review_start_failed"
    message = f"{target} 进入 review 失败。"
    next_step = "请检查 worker 日志后重试。"
    retryable = False

    if any("Failed to resolve Product Name from Spec_Master.csv" in line for line in detail_lines):
        code = "missing_spec_data"
        message = f"缺少 {target} 的规格数据，无法进入 review。"
        next_step = f"请先补齐 {target} 在 Spec_Master 中的规格数据，再重试。"
    elif any(line.startswith("Unable to resolve review-start target.") for line in detail_lines):
        code = "unresolved_review_target"
        message = f"无法识别 {target} 对应的目标，无法进入 review。"
        next_step = "请检查 Document_ID、Document_Key、Build_family 和 Lang 配置。"
        retryable = True
    elif any("Workflow_action must map to Start Review" in line for line in detail_lines):
        code = "invalid_workflow_action"
        message = f"{target} 的 Workflow_action 不支持进入 review。"
        next_step = "请把 Workflow_action 改成 Start Review 后重试。"
        retryable = True
    elif any("Conflicting Build_family" in line or "Conflicting Version" in line or "Conflicting Git_ref" in line for line in detail_lines):
        code = "conflicting_review_group"
        message = f"{target} 的 review 配置冲突，无法进入 review。"
        next_step = "请检查同一 Document_Key 下的 Build_family、Version 和 Git_ref 是否一致。"
        retryable = True
    elif any("sync-data" in line.lower() or "snapshot" in line.lower() for line in detail_lines):
        code = "phase2_snapshot_sync_failed"
        message = "同步最新规格数据失败，当前无法进入 review。"
        next_step = "请先修复 phase2 数据同步问题，再重试。"

    return {
        "code": code,
        "message": message,
        "detail": detail,
        "next_step": next_step,
        "workflow_action": review_action_label,
        "record_id": _text(getattr(record, "record_id", "")),
        "document_id": _text(getattr(record, "document_id", "")),
        "document_key": _text(getattr(record, "document_key", "")),
        "target": target,
        "model": _text(model),
        "region": _text(region),
        "build_family": _text(build_family),
        "lang": _text(lang),
        "version": _text(version) or _text(getattr(record, "version", "")),
        "retryable": retryable,
    }


def build_review_start_failure_report(
    *,
    review_action_label: str,
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_failures = [item for item in failures if isinstance(item, dict)]
    first = normalized_failures[0] if normalized_failures else {}
    return {
        "workflow_action": review_action_label,
        "failure_count": len(normalized_failures),
        "summary_code": _text(first.get("code")),
        "summary_message": _text(first.get("message")),
        "summary_next_step": _text(first.get("next_step")),
        "failures": normalized_failures,
    }
