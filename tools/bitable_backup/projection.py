# -*- coding: utf-8 -*-
"""Projected, fail-closed record reads for the content backup.

lark-cli's ``+record-list`` projects at most 50 fields per call, so a table with
more columns than that (the product matrix's 矩阵 table has one column per
attribute) must be read in projected slices and merged by record id — the same
approach ``tools/product_matrix_base/stage.py`` takes.

Every read here fails rather than writing a backup that looks complete but is
not: a field list that errored, is empty, or is shorter than its reported
``total`` / ``has_more``; a slice that misses a projected column; a row whose
cell count differs from the column count; a full page with no ``has_more``;
and record-id sets that differ between slices (a row added or deleted while the
table was read). Error messages carry only table ids and counts, never cell
values.

``export --projected-read`` (the product-matrix step) reads every table this
way. Without it the plain ``bitable_schema._read_records`` path stays in use
and projection only steps in for a table wider than 50 fields.
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
    """Every field of a table (one page of up to 200), refusing an errored, empty or truncated list."""
    fl = bs._lark(["base", "+field-list", "--base-token", base_token, "--table-id", tid,
                   "--limit", str(FIELD_LIST_LIMIT), "--format", "json", "--as", "bot"], lark_cli)
    if fl.get("ok") is False or "_raw" in fl:
        raise ProjectionError(f"table {tid}: field list failed")
    data = fl.get("data") or {}
    fields = [f for f in (data.get("fields") or data.get("items") or [])
              if isinstance(f, dict) and (f.get("field_name") or f.get("name"))]
    if not fields:
        raise ProjectionError(f"table {tid}: field list is empty")
    total = data.get("total")
    if data.get("has_more") or (isinstance(total, int) and total > len(fields)):
        raise ProjectionError(f"table {tid}: field list returned {len(fields)} of "
                              f"{total if isinstance(total, int) else 'more'} fields; the backup reads one page only")
    return fields


def field_types(fields: list[dict[str, Any]]) -> dict[str, str]:
    """``{field name: lower-case type}`` in field-list order."""
    return {str(f.get("field_name") or f.get("name")): (f.get("type") or "").lower() for f in fields}


def field_id_names(fields: list[dict[str, Any]]) -> dict[str, str]:
    """``{field id: field name}`` for mapping a record list's ``field_id_list``."""
    return {str(f.get("field_id") or f.get("id") or ""): str(f.get("field_name") or f.get("name")) for f in fields}


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
        result = bs._lark(args, lark_cli)
        if result.get("ok") is False or "_raw" in result:
            raise ProjectionError(f"table {tid}: record list failed at offset {offset}")
        return result

    def page_items(payload: dict[str, Any]) -> list[Any]:
        return (payload.get("data") or {}).get("data") or []

    def page_has_more(payload: dict[str, Any], _offset: int) -> bool:
        data = payload.get("data") or {}
        if "has_more" not in data and len(page_items(payload)) >= PAGE_LIMIT:
            # a full page without has_more cannot tell "last page" from "more pages"
            raise ProjectionError(f"table {tid}: a full page of {PAGE_LIMIT} rows came without has_more")
        return bool(data.get("has_more"))

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
        short = sum(1 for row in raw_rows if not isinstance(row, list) or len(row) != len(cols))
        if short:
            raise ProjectionError(f"table {tid}: {short} row(s) do not have exactly {len(cols)} cells")
        page_rids = data.get("record_id_list") or []
        if len(page_rids) != len(raw_rows):
            raise ProjectionError(f"table {tid}: {len(raw_rows)} row(s) but {len(page_rids)} record id(s) in one page")
        rows.extend(dict(zip(cols, row, strict=True)) for row in raw_rows)
        rids.extend(page_rids)
    return rows, rids


def read_projected_records(base_token: str, tid: str, ftypes: dict[str, str], id_name: dict[str, str],
                           lark_cli: str) -> tuple[list[dict[str, Any]], list[str]]:
    """``([row], [record_id])`` with every column in ``ftypes``, read 50 fields at a time and merged by record."""
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
    return [merged[rid] for rid in order], order


def read_wide_records(base_token: str, tid: str, first_ftypes: dict[str, str],
                      lark_cli: str) -> tuple[dict[str, str], list[dict[str, Any]], list[str]]:
    """``(field types, [row], [record_id])`` for a table the default field list showed as wider than 50 fields.

    The field list is re-read with an explicit page size so a short default page
    cannot drop tail columns; it must still contain every field the first read saw.
    """
    fields = list_fields(base_token, tid, lark_cli)
    ftypes = field_types(fields)
    lost = [name for name in first_ftypes if name not in ftypes]
    if lost:
        raise ProjectionError(f"table {tid}: the explicit field list lacks {len(lost)} of the "
                              f"{len(first_ftypes)} fields the first read returned")
    rows, rids = read_projected_records(base_token, tid, ftypes, field_id_names(fields), lark_cli)
    return ftypes, rows, rids
