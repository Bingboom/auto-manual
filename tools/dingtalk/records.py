from __future__ import annotations

from typing import Any

from .contracts import DingTalkRecordReference


def list_records(*, app_name: str, table_id: str, view_id: str | None = None) -> list[dict[str, Any]]:
    raise NotImplementedError(
        "Phase 0 placeholder: implement record listing after the exact DingTalk structured-data product is chosen."
    )


def get_record(ref: DingTalkRecordReference) -> dict[str, Any]:
    raise NotImplementedError(
        "Phase 0 placeholder: implement single-record lookup once the row identifier contract is confirmed."
    )


def update_record(ref: DingTalkRecordReference, *, fields: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError(
        "Phase 0 placeholder: implement row writeback after partial-update semantics are verified."
    )
