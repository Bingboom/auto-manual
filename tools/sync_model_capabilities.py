"""Mirror the build table's capability checkboxes into the tracked CSV.

``data/model_capabilities.csv`` feeds the capability -> chapter check
(tools/check_docs_capability.py). Like ``page_registry.csv`` it is a
repo-tracked file that ``sync-data`` refreshes from Feishu — a diff in
git is the review surface for capability changes.

The source is the 文档构建表 (the document-link table the queue already
binds via FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID); no new coordinates.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from tools.check_docs_capability import load_rules


_REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_CSV = "capability_page_rules.csv"


def load_capability_fields(data_dir: Path) -> tuple[str, ...]:
    """Return capability columns in the reviewed rules-file order."""

    fields = tuple(dict.fromkeys(rule["capability"] for rule in load_rules(data_dir)))
    if not fields:
        raise RuntimeError(
            f"No capability fields found in {data_dir / RULES_CSV}; "
            "the rules CSV is the source of truth for capability columns"
        )
    return fields


CAPABILITY_FIELDS = load_capability_fields(_REPO_ROOT / "data")
FIELDNAMES: tuple[str, ...] = ("Document_key", "Project", *CAPABILITY_FIELDS)


def _text(value: Any) -> str:
    """Flatten a Feishu text/formula field (list of segments) to a string."""
    if isinstance(value, list):
        return "".join(
            str(seg.get("text") or "") for seg in value if isinstance(seg, dict)
        ).strip()
    if value is None:
        return ""
    return str(value).strip()


def capabilities_csv_text(
    records: list[dict[str, Any]],
    *,
    capability_fields: tuple[str, ...] = CAPABILITY_FIELDS,
) -> str:
    """Raw build-table records -> deterministic capability mirror CSV.

    Rows without a resolved Document_key (e.g. a target whose model link
    is still pending, so the key formula yields "_<region>") and rows
    with no capability data at all (not yet inventoried) are skipped —
    the check treats absent rows as "no data", not "no capability".
    """
    rows: list[dict[str, str]] = []
    for record in records:
        fields = record.get("fields", record)
        key = _text(fields.get("Document_key"))
        if not key or key.startswith("_"):
            continue
        if all(fields.get(name) is None for name in capability_fields):
            continue
        row = {"Document_key": key, "Project": _text(fields.get("项目代码"))}
        for name in capability_fields:
            row[name] = "TRUE" if fields.get(name) is True else "FALSE"
        rows.append(row)
    rows.sort(key=lambda r: (r["Document_key"], r["Project"]))
    # the build table has carried duplicate rows before (JE-2000F_CN);
    # one mirror row per Document_key keeps the config surface clean
    seen: set[str] = set()
    rows = [r for r in rows
            if r["Document_key"] not in seen and not seen.add(r["Document_key"])]
    buf = io.StringIO()
    fieldnames = ("Document_key", "Project", *capability_fields)
    writer = csv.DictWriter(buf, fieldnames=list(fieldnames), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def sync_capability_mirror(
    cfg: dict[str, Any],
    *,
    source: Any,
    repo_root: Any,
    sha256_text: Any,
    sha256_file: Any,
    result_cls: Any,
):
    """Fetch the build table and refresh the tracked mirror CSV.

    Returns (result, (path, csv_text)) or (None, None) when the config
    block is absent (older configs keep working unchanged). Missing env
    values with the block present fail loudly, matching sync-data style.
    """
    import os

    phase2_cfg = ((cfg.get("sync") or {}).get("phase2") or {})
    mc_cfg = phase2_cfg.get("model_capabilities") or {}
    if not isinstance(mc_cfg, dict) or not mc_cfg:
        return None, None
    base_token_env = str(
        mc_cfg.get("base_token_env") or phase2_cfg.get("base_token_env") or ""
    ).strip()
    table_id_env = str(mc_cfg.get("table_id_env") or "").strip()
    view_id_env = str(mc_cfg.get("view_id_env") or "").strip()
    base_token = os.environ.get(base_token_env, "").strip() if base_token_env else ""
    table_id = os.environ.get(table_id_env, "").strip() if table_id_env else ""
    view_id = os.environ.get(view_id_env, "").strip() if view_id_env else None
    if not base_token or not table_id:
        raise RuntimeError(
            "sync.phase2.model_capabilities is configured but "
            f"{base_token_env or 'base_token_env'} / {table_id_env or 'table_id_env'} "
            "are not set in the environment"
        )
    records = source.fetch_records(
        base_token=base_token, table_id=table_id, view_id=view_id or None)
    capability_fields = load_capability_fields(Path(repo_root) / "data")
    csv_text = capabilities_csv_text(records, capability_fields=capability_fields)
    target_path = repo_root / "data" / "model_capabilities.csv"
    sha256 = sha256_text(csv_text)
    previous_sha256 = sha256_file(target_path)
    result = result_cls(
        logical_name="model_capabilities",
        file_name=target_path.name,
        target_path=target_path,
        row_count=max(0, csv_text.count("\n") - 1),
        sha256=sha256,
        previous_sha256=previous_sha256,
        changed=sha256 != previous_sha256,
    )
    return result, (target_path, csv_text)
