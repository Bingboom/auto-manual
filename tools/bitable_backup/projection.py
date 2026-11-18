# -*- coding: utf-8 -*-
"""Read every column of a wide Bitable table for the content backup.

lark-cli's ``+record-list`` projects at most 50 fields per call, so a table with
more columns than that (the product matrix's 矩阵 table has one column per
attribute) must be read in projected slices and merged by record id — the same
approach ``tools/product_matrix_base/stage.py`` takes. Tables at or under the
limit keep the plain ``bitable_schema._read_records`` path.

The slices are read one after another, so a row added or deleted between two
slices would leave a half-filled row in the backup. The record-id sets of all
slices must therefore match; otherwise the export fails (and the nightly
workflow's sentinel Issue opens) rather than writing an inconsistent restore
point. Error messages carry only table ids and counts, never cell values.
"""

from __future__ import annotations

from typing import Any

from tools import bitable_schema as bs
from tools.feishu_record_transport import iter_lark_pages

FIELDS_PER_READ = 50  # lark-cli projects at most 50 fields per record list
FIELD_LIST_LIMIT = 200
PAGE_LIMIT = 200


class ProjectionError(RuntimeError):
    """A wide table could not be read completely and consistently."""


def needs_projection(ftypes: dict[str, str]) -> bool:
    """Whether a table has more columns than one record list returns."""
    return len(ftypes) > FIELDS_PER_READ


def list_fields(base_token: str, tid: str, lark_cli: str) -> list[dict[str, Any]]:
    """Every field of a table (one page of up to 200), refusing a truncated list."""
    fl = bs._lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid,
                   "--limit", str(FIELD_LIST_LIMIT), "--format", "json", "--as", "bot"], lark_cli)
    data = fl.get("data") or {}
    if data.get("has_more"):
        raise ProjectionError(f"table {tid} has more than {FIELD_LIST_LIMIT} fields; the backup reads one page only")
    return [f for f in (data.get("fields") or data.get("items") or []) if isinstance(f, dict)]


def _read_slice(base_token: str, tid: str, names: list[str], id_name: dict[str, str],
                lark_cli: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    rids: list[str] = []

    def fetch_page(offset: int, page_limit: int) -> dict[str, Any]:
        args = ["base", "+record-list", "--base-token", base_token, "--table-id", tid,
                "--limit", str(page_limit), "--format", "json", "--as", "bot"]
        if offset:
            args += ["--offset", str(offset)]
        for name in names:
            args += ["--field-id", name]
        return bs._lark(args, lark_cli)

    def page_items(payload: dict[str, Any]) -> list[Any]:
        return (payload.get("data") or {}).get("data") or []

    def page_has_more(payload: dict[str, Any], _offset: int) -> bool:
        return bool((payload.get("data") or {}).get("has_more"))

    for payload, raw_rows in iter_lark_pages(fetch_page, items_from_payload=page_items,
                                             has_more_from_payload=page_has_more, limit=PAGE_LIMIT):
        data = payload.get("data") or {}
        display = data.get("fields") or []
        field_ids = data.get("field_id_list") or []
        if field_ids:
            cols = [id_name.get(str(fid)) or (display[i] if i < len(display) else str(fid))
                    for i, fid in enumerate(field_ids)]
        else:
            cols = list(display)
        if raw_rows and set(names) - set(cols):
            raise ProjectionError(
                f"table {tid}: record list returned {len(set(names) & set(cols))} of {len(names)} projected fields")
        page_rids = data.get("record_id_list") or []
        if len(page_rids) != len(raw_rows):
            raise ProjectionError(f"table {tid}: {len(raw_rows)} row(s) but {len(page_rids)} record id(s) in one page")
        rows.extend(dict(zip(cols, row, strict=False)) for row in raw_rows)
        rids.extend(page_rids)
    return rows, rids


def read_wide_records(base_token: str, tid: str,
                      lark_cli: str) -> tuple[dict[str, str], list[dict[str, Any]], list[str]]:
    """``(field types, [row], [record_id])`` with every column, read 50 fields at a time.

    The field list is re-read with an explicit page size so a default page can
    never silently drop the tail columns of a wide table.
    """
    fields = list_fields(base_token, tid, lark_cli)
    ftypes = {str(f.get("field_name") or f.get("name") or ""): (f.get("type") or "").lower() for f in fields}
    ftypes.pop("", None)
    id_name = {str(f.get("field_id") or f.get("id") or ""): str(f.get("field_name") or f.get("name") or "")
               for f in fields}
    names = list(ftypes)
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    first_ids: set[str] | None = None
    for start in range(0, len(names), FIELDS_PER_READ):
        rows, rids = _read_slice(base_token, tid, names[start:start + FIELDS_PER_READ], id_name, lark_cli)
        ids = set(rids)
        if len(ids) != len(rids):
            raise ProjectionError(f"table {tid}: a record id repeated within one slice; the offset is not honoured")
        if first_ids is None:
            first_ids = ids
            order = list(rids)
        elif ids != first_ids:
            raise ProjectionError(
                f"table {tid}: rows changed while it was read in slices "
                f"({len(first_ids)} vs {len(ids)} record ids); re-run the export")
        for row, rid in zip(rows, rids, strict=True):
            merged.setdefault(rid, {}).update(row)
    return ftypes, [merged[rid] for rid in order], order
