"""Batch request artifact, emitted only after verified source writeback."""
from __future__ import annotations

import os
from pathlib import Path

from tools.workspace_snapshot import atomic_json, digest

REQUEST_ENV = "AUTO_MANUAL_WORKSPACE_REFRESH_REQUEST"


def delivery_readback(source, binding, group, expected: dict) -> list[str]:
    """Opt-in production hook; source write acknowledgement alone is insufficient."""
    if not os.environ.get(REQUEST_ENV):
        return []
    from tools.rtd.deliverables import FEISHU_FORMATS, feishu_url

    links = {field: feishu_url(expected.get(field)) for field in FEISHU_FORMATS.values()
             if feishu_url(expected.get(field))}
    if not links:
        return []
    rows = source.fetch_records_with_ids(base_token=binding.base_token, table_id=binding.table_id, view_id=None)
    found = {row["record_id"]: row.get("fields", {}) for row in rows if isinstance(row, dict)}
    identities = []
    for record in group:
        fields = found.get(record.record_id, {})
        if any(feishu_url(fields.get(key)) != value for key, value in links.items()):
            raise RuntimeError("workspace delivery readback mismatch")
        identities.append(record.record_id)
    return identities


def request_refresh(kind: str, identities: list[str]) -> None:
    """One atomic request per completed batch; deterministic identity on retries."""
    configured = os.environ.get(REQUEST_ENV)
    if not configured or not identities:
        return
    identities = sorted(set(identities))
    atomic_json(Path(configured), {"schema": "workspace-refresh-request/v1", "kind": kind,
                                  "source_completed": True, "identities": identities,
                                  "batch_sha256": digest([kind, identities])})


def request_tm_refresh(write, transport, applied):
    if write and transport is not None and applied and all(row.get("verified") for row in applied):
        request_refresh("corpus", [str(row["record_id"]) for row in applied if row.get("record_id")])
