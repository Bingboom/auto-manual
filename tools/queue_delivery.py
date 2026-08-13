from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


_SUCCESS_RESULT_PATTERN = re.compile(r"^\s*SUCCESS\b", re.IGNORECASE)


@dataclass(frozen=True)
class QueueDeliveryContract:
    delivery_kind: str
    delivery_field: str
    delivery_url: str
    delivery_ready: bool
    baseline_ready: bool


def queue_delivery_contract(
    *,
    normalized_workflow_action: str | None,
    result: str,
    result_is_fresh: bool | None,
    idml_file: str = "",
    feishu_cloud_doc: str = "",
    baseline_doc: str = "",
    html_link: str = "",
) -> QueueDeliveryContract:
    """Return the phase-aware delivery contract exposed to agents.

    ``Document link`` / ``document_link`` is retired. Draft delivery is the
    editable Feishu cloud doc, Publish delivery is the uploaded IDML package,
    and Web Publish delivery is the HTML URL. A frozen baseline is tracked
    separately because it is backport evidence, not the operator deliverable.
    """

    action = str(normalized_workflow_action or "").strip().lower()
    if action == "draft":
        delivery_kind, delivery_field, delivery_url = (
            "feishu_cloud_doc",
            "飞书云文档",
            str(feishu_cloud_doc or "").strip(),
        )
    elif action == "publish":
        delivery_kind, delivery_field, delivery_url = (
            "idml_file",
            "idml_file",
            str(idml_file or "").strip(),
        )
    elif action == "web_publish":
        delivery_kind, delivery_field, delivery_url = (
            "html",
            "HTML_link",
            str(html_link or "").strip(),
        )
    else:
        delivery_kind, delivery_field, delivery_url = "", "", ""

    result_succeeded = bool(_SUCCESS_RESULT_PATTERN.search(str(result or "")))
    result_is_current = result_is_fresh is not False
    return QueueDeliveryContract(
        delivery_kind=delivery_kind,
        delivery_field=delivery_field,
        delivery_url=delivery_url,
        delivery_ready=bool(delivery_url) and result_succeeded and result_is_current,
        baseline_ready=(
            action == "draft"
            and bool(str(baseline_doc or "").strip())
            and result_succeeded
            and result_is_current
        ),
    )


def queue_delivery_contract_for_row(row: Any) -> QueueDeliveryContract:
    return queue_delivery_contract(
        normalized_workflow_action=getattr(row, "normalized_workflow_action", None),
        result=str(getattr(row, "result", "") or ""),
        result_is_fresh=getattr(row, "result_is_fresh", None),
        idml_file=str(getattr(row, "document_link", "") or ""),
        feishu_cloud_doc=str(getattr(row, "feishu_cloud_doc", "") or ""),
        baseline_doc=str(getattr(row, "baseline_doc", "") or ""),
        html_link=str(getattr(row, "html_link", "") or ""),
    )


def serialize_queue_row(row: Any) -> dict[str, Any]:
    """Serialize a queue row without reviving the retired public field name."""

    payload = asdict(row)
    payload["idml_file"] = payload.pop("document_link", "")
    payload.update(asdict(queue_delivery_contract_for_row(row)))
    return payload


def render_queue_delivery_lines(row: Any) -> list[str]:
    delivery = queue_delivery_contract_for_row(row)
    lines: list[str] = []
    for label, value in (
        ("idml_file", getattr(row, "document_link", "")),
        ("feishu_cloud_doc", getattr(row, "feishu_cloud_doc", "")),
        ("baseline_doc", getattr(row, "baseline_doc", "")),
        ("html_link", getattr(row, "html_link", "")),
    ):
        if value:
            lines.append(f"{label}: {value}")
    if delivery.delivery_kind:
        lines.extend(
            (
                f"delivery_kind: {delivery.delivery_kind}",
                f"delivery_ready: {str(delivery.delivery_ready).lower()}",
            )
        )
        if delivery.delivery_url:
            lines.append(f"delivery_url: {delivery.delivery_url}")
    if getattr(row, "baseline_doc", ""):
        lines.append(f"baseline_ready: {str(delivery.baseline_ready).lower()}")
    return lines
