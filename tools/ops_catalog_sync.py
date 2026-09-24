#!/usr/bin/env python3
"""Idempotent ops-catalog sync and three-face reconcile for the Web manual catalog.

REV-07 (plan §5.3 M1/M2): the operations sheet 「说明书目录」 is a **derived
view** of the frozen publication record — ``docs/publish/publish_manifest.json``
on Hello-Docs ``main`` (the single A-face authority per REV-06/M0-10). This tool
keeps that view honest without ever touching the human-owned columns:

- ``sync`` (M2): upsert the machine columns (A..K: 文档ID/型号/市场/语言/当前版本/
  正文链接/根别名链接/语言范围声明/目标构建时间UTC/内容提交/收录状态) keyed by the
  (model, region, lang) triple. New targets append at the bottom; existing rows
  are rewritten only when a machine column actually differs; rows whose key has
  left the manifest are reported as orphans and never modified or deleted; the
  human columns (L..O: 负责人/运营状态/下次复盘日期/运营备注) are never written on
  existing rows (new rows seed 运营状态=待评估 only). Dry-run by default;
  ``--write`` applies row by row with a same-row readback, and a failed row is
  recorded for retry without blocking the other rows.
- ``reconcile`` (M1): read-only three-face cross-check of manifest ↔ ops sheet ↔
  Document_link queue receipts (``HTML_link``). Differences are classified
  against the committed whitelist (``data/ops_catalog_reconcile_whitelist.json``,
  seeded from the REV-06 M0 diff table): a whitelisted difference is reported
  and exits 0; any new difference exits 1. Per M0-11 the alignment key is the
  identity triple — version vocabularies are display-only and not reconciled.

Live-table writes stay operator-gated: run ``--write`` only under an explicit
authorization, and keep the produced report (plan + per-row readbacks) as the
write evidence. Contract notes live in
``code-as-doc/dev/web_publish_pipeline.md`` §2.3.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root


ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.document_link_queue import split_rendered_url  # noqa: E402
from tools.feishu_record_transport import run_lark_cli_json as _transport_run  # noqa: E402
from tools.manual_operations_online_health import publication_url  # noqa: E402
from tools.phase2_support import parse_json_payload, resolved_cli_command_parts  # noqa: E402
from tools.queue_runtime import command_failure_message, format_command  # noqa: E402
from tools.rtd_deployment_receipt import DEFAULT_RTD_BASE_URL  # noqa: E402
from tools.utils.path_utils import ops_catalog_reconcile_whitelist_of  # noqa: E402
from tools.verify_web_deployment_targets import (  # noqa: E402
    MANIFEST_SCHEMA,
    fetch_manifest_bytes,
    manifest_targets,
)

REPORT_SCHEMA = "auto-manual-ops-catalog-sync/v1"
WHITELIST_SCHEMA = "auto-manual-ops-catalog-reconcile-whitelist/v1"
# GitHub coordinates of the business-plane publication record. The commit is
# resolved first so the manifest fetch is pinned to one recorded source SHA.
HELLO_DOCS_COMMIT_URL = "https://api.github.com/repos/Bingboom/Hello-Docs/commits/main"
HELLO_DOCS_MANIFEST_URL_TEMPLATE = (
    "https://api.github.com/repos/Bingboom/Hello-Docs/contents/"
    "docs/publish/publish_manifest.json?ref={ref}"
)

# The sheet contract: header row 1 must match exactly, otherwise every write is
# refused — a reordered or renamed column silently retargeting machine writes
# is the failure mode this guards against.
EXPECTED_HEADERS = (
    "文档ID",
    "型号",
    "市场",
    "语言",
    "当前版本",
    "正文链接",
    "根别名链接",
    "语言范围声明",
    "目标构建时间UTC",
    "内容提交",
    "收录状态",
    "负责人",
    "运营状态",
    "下次复盘日期",
    "运营备注",
)
MACHINE_COL_COUNT = 11  # A..K derived from the manifest; L..O are human-owned.
COL_COUNT = len(EXPECTED_HEADERS)
LAST_COL = "O"
LAST_MACHINE_COL = "K"
CATALOG_STATUS_VALUE = "发布目录收录"
NEW_ROW_OPS_STATUS = "待评估"
# Style block matching the existing catalog rows (writes_log 2026-09-19: number
# format "@" keeps versions like "2.0" as text, sibling rows use font 11 /
# vertical middle). Applied to appended rows only; updates write values only.
NEW_ROW_CELL_STYLES = {"font_size": 11, "number_format": "@", "vertical_alignment": "middle"}

_SAFE_SEGMENT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_ROW_PREFIX_RE = re.compile(r"^\[row=(\d+)\]\s?")
_URL_RE = re.compile(r"https?://[^\s\)\]]+")

EXIT_OK = 0
EXIT_DIFF = 1
EXIT_ERROR = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- lark-cli access layer --------------------------------------------------


def default_runner(*, cli_bin: str, args: list[str]) -> dict[str, Any]:
    """Shared hardened lark-cli transport (retry/backoff, ok-validation)."""
    return _transport_run(
        cli_bin=cli_bin,
        args=args,
        repo_root=ROOT,
        resolved_cli_command_parts=resolved_cli_command_parts,
        parse_json_payload=parse_json_payload,
        command_failure_message=command_failure_message,
        on_command=lambda cmd: print(f"[ops-catalog] {format_command(cmd)}"),
    )


@dataclass
class LarkOps:
    """Thin lark-cli wrapper; ``runner`` is injectable so tests exercise the
    real payload assembly against a fake transport."""

    cli_bin: str = "lark-cli"
    identity: str = "bot"
    runner: Callable[..., dict[str, Any]] = default_runner

    def _run(self, args: list[str]) -> dict[str, Any]:
        return self.runner(cli_bin=self.cli_bin, args=args)

    def sheet_grid_rows(self, spreadsheet_token: str, sheet_id: str) -> int:
        payload = self._run(
            [
                "sheets",
                "+workbook-info",
                "--as",
                self.identity,
                "--spreadsheet-token",
                spreadsheet_token,
            ]
        )
        for sheet in _dig(payload, "data", "sheets") or []:
            if isinstance(sheet, dict) and str(sheet.get("sheet_id") or "") == sheet_id:
                grid = sheet.get("grid_properties")
                row_count = (grid or {}).get("row_count") if isinstance(grid, dict) else None
                if row_count is None:
                    row_count = sheet.get("row_count")
                if isinstance(row_count, int) and row_count > 0:
                    return row_count
        raise RuntimeError(f"workbook-info did not report a row_count for sheet {sheet_id}")

    def read_range_csv(self, spreadsheet_token: str, sheet_id: str, cell_range: str) -> dict[str, Any]:
        payload = self._run(
            [
                "sheets",
                "+csv-get",
                "--as",
                self.identity,
                "--spreadsheet-token",
                spreadsheet_token,
                "--sheet-id",
                sheet_id,
                "--range",
                cell_range,
                "--format",
                "json",
            ]
        )
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("annotated_csv"), str):
            raise RuntimeError(f"csv-get returned no annotated_csv for range {cell_range}")
        if data.get("has_more"):
            raise RuntimeError(
                f"csv-get truncated the read for range {cell_range} (has_more=true); "
                "a partial grid must never drive an upsert plan"
            )
        return data

    def set_cells(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        cell_range: str,
        cells: list[list[dict[str, Any]]],
        *,
        allow_overwrite: bool,
    ) -> dict[str, Any]:
        return self._run(
            [
                "sheets",
                "+cells-set",
                "--as",
                self.identity,
                "--spreadsheet-token",
                spreadsheet_token,
                "--sheet-id",
                sheet_id,
                "--range",
                cell_range,
                "--allow-overwrite=" + ("true" if allow_overwrite else "false"),
                "--cells",
                json.dumps(cells, ensure_ascii=False),
            ]
        )

    def sheet_revision(self, spreadsheet_token: str) -> Any:
        payload = self._run(
            [
                "sheets",
                "+revision-get",
                "--as",
                self.identity,
                "--spreadsheet-token",
                spreadsheet_token,
            ]
        )
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("revision", "version"):
                if key in data:
                    return data[key]
        return None

    def bitable_records(self, base_token: str, table_id: str) -> list[dict[str, Any]]:
        """Read every Document_link row (read-only) as {field_name: value} maps.

        ``+record-list`` caps at 200 rows per call, so paginate by offset until
        a short page arrives.
        """
        records: list[dict[str, Any]] = []
        offset = 0
        limit = 200
        while True:
            payload = self._run(
                [
                    "base",
                    "+record-list",
                    "--as",
                    self.identity,
                    "--base-token",
                    base_token,
                    "--table-id",
                    table_id,
                    "--format",
                    "json",
                    "--limit",
                    str(limit),
                    "--offset",
                    str(offset),
                ]
            )
            data = payload.get("data")
            if not isinstance(data, dict):
                raise RuntimeError("record-list returned no data payload")
            fields = [_field_name(item) for item in data.get("fields") or []]
            rows = data.get("data") or []
            record_ids = data.get("record_id_list") or []
            for index, row in enumerate(rows):
                if not isinstance(row, list):
                    continue
                entry = dict(zip(fields, row))
                if index < len(record_ids):
                    entry["_record_id"] = record_ids[index]
                records.append(entry)
            if len(rows) < limit:
                return records
            offset += limit


def _field_name(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or item.get("field_name") or "")
    return str(item)


def _dig(payload: Any, *keys: str) -> Any:
    node = payload
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


# --- manifest face ----------------------------------------------------------


@dataclass(frozen=True)
class CatalogTarget:
    model: str
    region: str
    lang: str
    version: str
    built_at: str
    git_ref: str
    language_scope: str
    page_url: str
    alias_url: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.model, self.region, self.lang)

    @property
    def doc_id(self) -> str:
        return f"{self.model}/{self.region}/{self.lang}"

    def machine_values(self) -> list[str]:
        return [
            self.doc_id,
            self.model,
            self.region,
            self.lang,
            self.version,
            self.page_url,
            self.alias_url,
            self.language_scope,
            self.built_at,
            self.git_ref,
            CATALOG_STATUS_VALUE,
        ]


def catalog_targets(payload: Any, *, base_url: str) -> list[CatalogTarget]:
    """Validated manifest targets with the derived catalog link columns.

    Identity and route validation is delegated to
    ``verify_web_deployment_targets.manifest_targets`` (same trust posture: the
    manifest is data, unsafe segments never become URLs); the extra display
    fields are joined back from the raw payload by identity.
    """
    validated = manifest_targets(payload)
    raw_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in payload.get("targets") or []:
        raw_by_key[(str(item.get("model")), str(item.get("region")), str(item.get("lang")))] = item
    targets = []
    for entry in validated:
        key = (entry["model"], entry["region"], entry["lang"])
        raw = raw_by_key.get(key)
        if raw is None:  # pragma: no cover - manifest_targets built from the same list
            raise RuntimeError(f"validated target missing from raw manifest: {key}")
        alias_url = ""
        aliases = raw.get("legacy_aliases")
        if raw.get("legacy_default") and isinstance(aliases, list) and aliases:
            alias = str(aliases[0])
            if not _SAFE_SEGMENT_RE.fullmatch(alias):
                raise RuntimeError(f"Publish manifest target has an unsafe legacy alias: {alias!r}")
            alias_url = publication_url(base_url, f"{alias}.html")
        targets.append(
            CatalogTarget(
                model=entry["model"],
                region=entry["region"],
                lang=entry["lang"],
                version=str(raw.get("version") or ""),
                built_at=str(raw.get("built_at") or ""),
                git_ref=str(raw.get("git_ref") or ""),
                language_scope=str(raw.get("language_scope") or ""),
                page_url=publication_url(base_url, entry["page"]),
                alias_url=alias_url,
            )
        )
    return targets


def resolve_manifest(
    *,
    manifest_path: Path | None,
    manifest_ref: str,
    token: str | None,
    fetch_bytes: Callable[..., bytes] = fetch_manifest_bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (payload, source descriptor). Remote fetches pin the recorded SHA:
    the ``main`` tip commit is resolved first and the manifest is fetched at
    exactly that commit."""
    if manifest_path is not None:
        raw = manifest_path.read_bytes()
        source: dict[str, Any] = {"kind": "local", "path": str(manifest_path)}
    else:
        ref = manifest_ref
        if ref == "main":
            commit_payload = json.loads(
                fetch_bytes(HELLO_DOCS_COMMIT_URL, token=token)
            )
            sha = str(commit_payload.get("sha") or "").strip()
            if not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise RuntimeError("Could not resolve the Hello-Docs main commit SHA")
            ref = sha
        url = HELLO_DOCS_MANIFEST_URL_TEMPLATE.format(ref=ref)
        raw = fetch_bytes(url, token=token)
        source = {"kind": "remote", "url": url, "git_sha": ref}
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("schema_version") != MANIFEST_SCHEMA:
        raise RuntimeError("Unsupported publish manifest schema")
    source["manifest_built_at"] = str(payload.get("built_at") or "")
    return payload, source


# --- sheet face -------------------------------------------------------------


@dataclass(frozen=True)
class SheetRow:
    row_number: int
    values: tuple[str, ...]  # exactly COL_COUNT entries

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.values[1], self.values[2], self.values[3])

    @property
    def machine(self) -> tuple[str, ...]:
        return self.values[:MACHINE_COL_COUNT]

    @property
    def human(self) -> tuple[str, ...]:
        return self.values[MACHINE_COL_COUNT:]

    @property
    def is_blank(self) -> bool:
        return not any(self.values)


def parse_annotated_csv(annotated_csv: str) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    for line in annotated_csv.splitlines():
        match = _ROW_PREFIX_RE.match(line)
        if not match:
            raise RuntimeError(f"csv-get line is missing its [row=N] prefix: {line[:80]!r}")
        row_number = int(match.group(1))
        parsed = next(csv.reader(io.StringIO(line[match.end():])), [])
        values = [cell.strip() for cell in parsed]
        values = (values + [""] * COL_COUNT)[:COL_COUNT]
        rows.append((row_number, values))
    return rows


def load_sheet_rows(data: dict[str, Any]) -> list[SheetRow]:
    parsed = parse_annotated_csv(str(data["annotated_csv"]))
    if not parsed:
        raise RuntimeError("The catalog sheet read returned no rows")
    header_number, header = parsed[0]
    if header_number != 1 or tuple(header) != EXPECTED_HEADERS:
        raise RuntimeError(
            "The catalog sheet header does not match the expected 15-column layout; "
            f"refusing every write. Got: {header}"
        )
    return [SheetRow(row_number=number, values=tuple(values)) for number, values in parsed[1:]]


# --- sync planning ----------------------------------------------------------


@dataclass
class SyncPlan:
    in_sync: list[dict[str, Any]] = field(default_factory=list)
    updates: list[dict[str, Any]] = field(default_factory=list)
    appends: list[dict[str, Any]] = field(default_factory=list)
    orphans: list[dict[str, Any]] = field(default_factory=list)
    duplicates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_writes(self) -> bool:
        return bool(self.updates or self.appends)


def plan_sync(targets: list[CatalogTarget], rows: list[SheetRow]) -> SyncPlan:
    plan = SyncPlan()
    data_rows = [row for row in rows if not row.is_blank]
    rows_by_key: dict[tuple[str, str, str], list[SheetRow]] = {}
    for row in data_rows:
        rows_by_key.setdefault(row.key, []).append(row)
    target_keys = {target.key for target in targets}
    for key, key_rows in rows_by_key.items():
        if len(key_rows) > 1:
            plan.duplicates.append(
                {
                    "doc_id": "/".join(key),
                    "rows": [row.row_number for row in key_rows],
                    "reason": "duplicate key rows: not written, needs operator cleanup",
                }
            )
        if key not in target_keys:
            for row in key_rows:
                plan.orphans.append(
                    {
                        "doc_id": "/".join(key),
                        "row": row.row_number,
                        "reason": "row key is absent from the manifest; never modified or deleted by sync",
                    }
                )
    for target in sorted(targets, key=lambda item: item.doc_id):
        key_rows = rows_by_key.get(target.key, [])
        if not key_rows:
            plan.appends.append({"doc_id": target.doc_id, "machine_values": target.machine_values()})
            continue
        if len(key_rows) > 1:
            continue  # recorded under duplicates; refuse to guess which row to update
        row = key_rows[0]
        expected = tuple(target.machine_values())
        if row.machine == expected:
            plan.in_sync.append({"doc_id": target.doc_id, "row": row.row_number})
            continue
        changed = [
            {
                "column": EXPECTED_HEADERS[index],
                "before": row.machine[index],
                "after": expected[index],
            }
            for index in range(MACHINE_COL_COUNT)
            if row.machine[index] != expected[index]
        ]
        plan.updates.append(
            {
                "doc_id": target.doc_id,
                "row": row.row_number,
                "machine_values": list(expected),
                "human_values_before": list(row.human),
                "changed": changed,
            }
        )
    return plan


# --- sync write path --------------------------------------------------------


def _value_cells(values: list[str], *, styles: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cells = []
    for value in values:
        cell: dict[str, Any] = {}
        if value:
            cell["value"] = value
        elif styles is None:
            # An update must be able to blank a stale machine cell (e.g. a
            # withdrawn root alias); appends leave empty cells value-free.
            cell["value"] = ""
        if styles is not None:
            cell["cell_styles"] = dict(styles)
        cells.append(cell)
    return cells


def _readback_row(ops: LarkOps, spreadsheet_token: str, sheet_id: str, row_number: int) -> list[str]:
    data = ops.read_range_csv(
        spreadsheet_token, sheet_id, f"A{row_number}:{LAST_COL}{row_number}"
    )
    parsed = parse_annotated_csv(str(data["annotated_csv"]))
    if len(parsed) != 1 or parsed[0][0] != row_number:
        raise RuntimeError(f"readback returned unexpected rows for row {row_number}")
    return parsed[0][1]


def apply_sync_plan(
    ops: LarkOps,
    plan: SyncPlan,
    *,
    spreadsheet_token: str,
    sheet_id: str,
    first_append_row: int,
    grid_rows: int,
) -> dict[str, Any]:
    """Apply updates then appends, one row per lark-cli call.

    Every row is written independently and read back through the live API; a
    failed row lands in ``failures`` (with enough detail to retry just that
    row) without blocking the remaining rows.
    """
    applied: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for update in plan.updates:
        row_number = int(update["row"])
        expected_machine = [str(v) for v in update["machine_values"]]
        expected_human = [str(v) for v in update["human_values_before"]]
        entry = {"action": "update", "doc_id": update["doc_id"], "row": row_number}
        try:
            ops.set_cells(
                spreadsheet_token,
                sheet_id,
                f"A{row_number}:{LAST_MACHINE_COL}{row_number}",
                [_value_cells(expected_machine)],
                allow_overwrite=True,
            )
            after = _readback_row(ops, spreadsheet_token, sheet_id, row_number)
            if after[:MACHINE_COL_COUNT] != expected_machine:
                raise RuntimeError(
                    f"readback mismatch on machine columns: {after[:MACHINE_COL_COUNT]!r}"
                )
            if after[MACHINE_COL_COUNT:] != expected_human:
                raise RuntimeError(
                    "human columns changed during a machine-column update: "
                    f"{after[MACHINE_COL_COUNT:]!r} != {expected_human!r}"
                )
        except Exception as exc:
            failures.append({**entry, "error": f"{type(exc).__name__}: {exc}"})
        else:
            applied.append({**entry, "readback": after})

    next_row = first_append_row
    for append in plan.appends:
        row_number = next_row
        next_row += 1
        entry = {"action": "append", "doc_id": append["doc_id"], "row": row_number}
        machine = [str(v) for v in append["machine_values"]]
        full_values = machine + ["", NEW_ROW_OPS_STATUS, "", ""]
        try:
            if row_number > grid_rows:
                raise RuntimeError(
                    f"append row {row_number} exceeds the sheet grid ({grid_rows} rows); "
                    "grow the sheet first"
                )
            ops.set_cells(
                spreadsheet_token,
                sheet_id,
                f"A{row_number}:{LAST_COL}{row_number}",
                [_value_cells(full_values, styles=NEW_ROW_CELL_STYLES)],
                allow_overwrite=False,
            )
            after = _readback_row(ops, spreadsheet_token, sheet_id, row_number)
            if after != full_values:
                raise RuntimeError(f"readback mismatch on appended row: {after!r}")
        except Exception as exc:
            failures.append({**entry, "error": f"{type(exc).__name__}: {exc}"})
        else:
            applied.append({**entry, "readback": after})

    return {"applied": applied, "failures": failures}


# --- reconcile (M1) ---------------------------------------------------------

RECEIPT_LINK_FIELD = "HTML_link"
RECEIPT_IDENTITY_FIELDS = ("Task_id", "Document_ID", "Workflow_action")


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(
            _flatten_text(value.get(key)) for key in ("text", "link", "url") if value.get(key)
        )
    if value is None:
        return ""
    return str(value)


def extract_link(value: Any) -> str:
    """The URL a Document_link ``HTML_link`` cell points at, or ``""``.

    Reconcile is a lenient reader by design: it reports what the catalog holds.
    The ``url``-field rendering shape (``[label](target)``) is owned by
    ``document_link_queue.split_rendered_url`` — the link *target* is what a
    reader would open, so it wins over any label. Everything else falls back to
    the first URL found anywhere in the flattened cell.
    """
    text = _flatten_text(value)
    pair = split_rendered_url(text)
    if pair is not None and pair[1]:
        return pair[1].rstrip(")].,")
    match = _URL_RE.search(text)
    return match.group(0).rstrip(")].,") if match else ""


@dataclass(frozen=True)
class Diff:
    kind: str
    key: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "key": self.key, "detail": self.detail}


def load_whitelist(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != WHITELIST_SCHEMA:
        raise RuntimeError(f"Unsupported reconcile whitelist schema in {path}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise RuntimeError(f"Reconcile whitelist {path} has no entries list")
    return payload


def whitelist_index(payload: dict[str, Any]) -> dict[tuple[str, str], str]:
    index: dict[tuple[str, str], str] = {}
    for entry in payload["entries"]:
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("kind") or "")
        key = str(entry.get("key") or "")
        if kind and key:
            index[(kind, key)] = str(entry.get("reason") or "")
    return index


def reconcile_diffs(
    targets: list[CatalogTarget],
    rows: list[SheetRow],
    receipts: list[dict[str, Any]],
) -> list[Diff]:
    diffs: list[Diff] = []
    plan = plan_sync(targets, rows)
    for item in plan.appends:
        diffs.append(Diff("ops_missing_row", item["doc_id"], "manifest target has no catalog row"))
    for item in plan.updates:
        changed = ", ".join(change["column"] for change in item["changed"])
        diffs.append(
            Diff("ops_stale_row", item["doc_id"], f"row {item['row']} machine columns differ: {changed}")
        )
    for item in plan.orphans:
        diffs.append(
            Diff("ops_orphan_row", item["doc_id"], f"row {item['row']} has no manifest target")
        )
    for item in plan.duplicates:
        diffs.append(
            Diff("ops_duplicate_row", item["doc_id"], f"rows {item['rows']} share one key")
        )

    page_index = {target.page_url: target for target in targets}
    alias_index = {target.alias_url: target for target in targets if target.alias_url}
    registered: set[tuple[str, str, str]] = set()
    for record in receipts:
        link = extract_link(record.get(RECEIPT_LINK_FIELD))
        if not link:
            continue
        identity = next(
            (
                _flatten_text(record.get(field_name)).strip()
                for field_name in RECEIPT_IDENTITY_FIELDS
                if _flatten_text(record.get(field_name)).strip()
            ),
            str(record.get("_record_id") or "unknown"),
        )
        if link in page_index:
            registered.add(page_index[link].key)
            continue
        if link in alias_index:
            target = alias_index[link]
            registered.add(target.key)
            diffs.append(
                Diff(
                    "receipt_flat_form_link",
                    identity,
                    f"HTML_link uses the flat root alias {link}; the M4 contract "
                    f"registers the nested page {target.page_url}",
                )
            )
            continue
        diffs.append(
            Diff("receipt_unmatched_link", identity, f"HTML_link {link} maps to no manifest target")
        )
    for target in sorted(targets, key=lambda item: item.doc_id):
        if target.key not in registered:
            diffs.append(
                Diff(
                    "target_unregistered",
                    target.doc_id,
                    "manifest target has no Document_link HTML_link receipt",
                )
            )
    return diffs


def classify_diffs(
    diffs: list[Diff], whitelist: dict[tuple[str, str], str]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    known: list[dict[str, str]] = []
    new: list[dict[str, str]] = []
    for diff in diffs:
        reason = whitelist.get((diff.kind, diff.key))
        if reason is None:
            new.append(diff.as_dict())
        else:
            known.append({**diff.as_dict(), "whitelist_reason": reason})
    return known, new


# --- CLI --------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--manifest-path", type=Path, default=None,
                       help="Local publish_manifest.json (skips the remote fetch)")
        p.add_argument("--manifest-ref", default="main",
                       help="Hello-Docs git ref for the remote manifest (default: main tip, pinned by SHA)")
        p.add_argument("--base-url", default=DEFAULT_RTD_BASE_URL)
        p.add_argument("--spreadsheet-token", default=None,
                       help="Ops catalog spreadsheet token (env OPS_CATALOG_SPREADSHEET_TOKEN)")
        p.add_argument("--sheet-id", default=None,
                       help="Ops catalog sheet id (env OPS_CATALOG_SHEET_ID)")
        p.add_argument("--cli-bin", default="lark-cli",
                       help='lark-cli command, e.g. "lark-cli --profile <name>"')
        p.add_argument("--identity", choices=("user", "bot"), default="bot")
        p.add_argument("--report-json", type=Path, default=None)

    sync = sub.add_parser("sync", help="M2: idempotent machine-column upsert (dry-run unless --write)")
    common(sync)
    sync.add_argument("--write", action="store_true",
                      help="Apply the plan (operator-authorized runs only); default is dry-run")

    rec = sub.add_parser("reconcile", help="M1: read-only manifest/ops-sheet/queue-receipt cross-check")
    common(rec)
    rec.add_argument("--doc-link-base-token", default=None,
                     help="Document_link base token (env FEISHU_PHASE2_BASE_TOKEN)")
    rec.add_argument("--doc-link-table-id", default=None,
                     help="Document_link table id (env FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID)")
    rec.add_argument("--whitelist", type=Path, default=None,
                     help="Reconcile whitelist path (default: data/ops_catalog_reconcile_whitelist.json)")
    return parser.parse_args(argv)


def _required(value: str | None, env_name: str, flag: str) -> str:
    import os

    resolved = (value or os.environ.get(env_name, "")).strip()
    if not resolved:
        raise RuntimeError(f"Missing {flag} (or environment variable {env_name})")
    return resolved


def _load_faces(
    args: argparse.Namespace, ops: LarkOps
) -> tuple[list[CatalogTarget], list[SheetRow], dict[str, Any], dict[str, Any]]:
    import os

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or None
    payload, source = resolve_manifest(
        manifest_path=args.manifest_path, manifest_ref=str(args.manifest_ref), token=token
    )
    targets = catalog_targets(payload, base_url=str(args.base_url))
    spreadsheet_token = _required(
        args.spreadsheet_token, "OPS_CATALOG_SPREADSHEET_TOKEN", "--spreadsheet-token"
    )
    sheet_id = _required(args.sheet_id, "OPS_CATALOG_SHEET_ID", "--sheet-id")
    grid_rows = ops.sheet_grid_rows(spreadsheet_token, sheet_id)
    data = ops.read_range_csv(spreadsheet_token, sheet_id, f"A1:{LAST_COL}{grid_rows}")
    rows = load_sheet_rows(data)
    sheet_meta = {
        "spreadsheet_token": spreadsheet_token,
        "sheet_id": sheet_id,
        "grid_rows": grid_rows,
        "revision": data.get("revision"),
        "data_rows": sum(1 for row in rows if not row.is_blank),
    }
    return targets, rows, source, sheet_meta


def _emit_report(args: argparse.Namespace, report: dict[str, Any]) -> None:
    if args.report_json is not None:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def run_sync(args: argparse.Namespace, ops: LarkOps) -> tuple[int, dict[str, Any]]:
    targets, rows, source, sheet_meta = _load_faces(args, ops)
    plan = plan_sync(targets, rows)
    data_row_numbers = [row.row_number for row in rows if not row.is_blank]
    first_append_row = (max(data_row_numbers) if data_row_numbers else 1) + 1
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "mode": "sync",
        "written": bool(args.write),
        "utc": utc_now(),
        "manifest_source": source,
        "manifest_targets": len(targets),
        "sheet": sheet_meta,
        "plan": {
            "in_sync": len(plan.in_sync),
            "updates": plan.updates,
            "appends": plan.appends,
            "orphans": plan.orphans,
            "duplicates": plan.duplicates,
        },
    }
    prefix = "[ops-catalog-sync]"
    print(
        f"{prefix} manifest targets={len(targets)} sheet data rows={sheet_meta['data_rows']} "
        f"in_sync={len(plan.in_sync)} updates={len(plan.updates)} appends={len(plan.appends)} "
        f"orphans={len(plan.orphans)} duplicates={len(plan.duplicates)}"
    )
    for item in plan.updates:
        changes = "; ".join(
            f"{change['column']}: {change['before']!r} -> {change['after']!r}" for change in item["changed"]
        )
        print(f"{prefix} UPDATE row {item['row']} {item['doc_id']}: {changes}")
    for item in plan.appends:
        print(f"{prefix} APPEND {item['doc_id']}")
    for item in plan.orphans:
        print(f"{prefix} ORPHAN row {item['row']} {item['doc_id']} (left untouched)")
    for item in plan.duplicates:
        print(f"{prefix} DUPLICATE {item['doc_id']} rows {item['rows']} (left untouched)")

    if not args.write:
        print(f"{prefix} dry-run only; pass --write (operator-authorized) to apply")
        return EXIT_OK, report

    outcome = apply_sync_plan(
        ops,
        plan,
        spreadsheet_token=str(sheet_meta["spreadsheet_token"]),
        sheet_id=str(sheet_meta["sheet_id"]),
        first_append_row=first_append_row,
        grid_rows=int(sheet_meta["grid_rows"]),
    )
    report["write"] = outcome
    report["write"]["revision_after"] = ops.sheet_revision(str(sheet_meta["spreadsheet_token"]))
    for item in outcome["applied"]:
        print(f"{prefix} WROTE {item['action']} row {item['row']} {item['doc_id']} (readback ok)")
    for item in outcome["failures"]:
        print(f"{prefix} FAILED {item['action']} {item['doc_id']}: {item['error']}", file=sys.stderr)
    if outcome["failures"]:
        print(
            f"{prefix} {len(outcome['failures'])} row(s) failed; rerun sync to retry just those rows "
            "(the plan is idempotent)",
            file=sys.stderr,
        )
        return EXIT_DIFF, report
    return EXIT_OK, report


def run_reconcile(args: argparse.Namespace, ops: LarkOps) -> tuple[int, dict[str, Any]]:
    targets, rows, source, sheet_meta = _load_faces(args, ops)
    base_token = _required(args.doc_link_base_token, "FEISHU_PHASE2_BASE_TOKEN", "--doc-link-base-token")
    table_id = _required(
        args.doc_link_table_id, "FEISHU_PHASE2_DOCUMENT_LINK_TABLE_ID", "--doc-link-table-id"
    )
    receipts = ops.bitable_records(base_token, table_id)
    whitelist_path = args.whitelist or ops_catalog_reconcile_whitelist_of(ROOT)
    whitelist_payload = load_whitelist(whitelist_path)
    known, new = classify_diffs(
        reconcile_diffs(targets, rows, receipts), whitelist_index(whitelist_payload)
    )
    report = {
        "schema": REPORT_SCHEMA,
        "mode": "reconcile",
        "utc": utc_now(),
        "manifest_source": source,
        "manifest_targets": len(targets),
        "sheet": sheet_meta,
        "receipt_rows": len(receipts),
        "whitelist": {"path": str(whitelist_path), "entries": len(whitelist_payload["entries"])},
        "known_diffs": known,
        "new_diffs": new,
        "status": "failed" if new else "ok",
    }
    prefix = "[ops-catalog-reconcile]"
    for item in known:
        print(f"{prefix} KNOWN {item['kind']} {item['key']}: {item['detail']} "
              f"(whitelist: {item['whitelist_reason']})")
    for item in new:
        print(f"{prefix} NEW {item['kind']} {item['key']}: {item['detail']}")
    print(
        f"{prefix} {report['status']}: targets={len(targets)} receipts={len(receipts)} "
        f"known={len(known)} new={len(new)}"
    )
    return (EXIT_DIFF if new else EXIT_OK), report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ops = LarkOps(cli_bin=str(args.cli_bin), identity=str(args.identity))
    try:
        if args.mode == "sync":
            exit_code, report = run_sync(args, ops)
        else:
            exit_code, report = run_reconcile(args, ops)
    except Exception as exc:
        print(f"[ops-catalog-sync] ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR
    _emit_report(args, report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
