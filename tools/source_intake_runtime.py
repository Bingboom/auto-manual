from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from tools.source_intake_extract import MarkdownTable, parse_markdown_tables, table_payload
from tools.source_intake_model import (
    CANDIDATE_SCHEMA_VERSION,
    FOOTNOTE_TEXT_FIELDS,
    MANUAL_COPY_TEXT_FIELDS,
    NOTE_TEXT_FIELDS,
    SPEC_TEXT_FIELDS,
    TARGET_MANUAL_COPY,
    TARGET_PAGE_PLACEHOLDERS,
    TARGET_SPEC_FOOTNOTES,
    TARGET_SPEC_MASTER,
    TARGET_SPEC_NOTES,
    UPDATE_CAPABLE_TABLES,
    candidate_hash,
    compact_dict,
    delta_hash,
    normalize_space,
    page_is_specifications,
)
from tools.source_record_index import load_index, resolve_by_table
from tools.spec_master_sources import model_region_from_document_key
from tools.source_table_sync import CHANGE_REQUEST_SCHEMA_VERSION


_HEADER_CLEAN_RE = re.compile(r"[^a-z0-9]+")
_KEY_CLEAN_RE = re.compile(r"[^A-Za-z0-9._-]+")

_ALIASES: dict[str, tuple[str, ...]] = {
    "target_table": ("target table", "table", "source table"),
    "page": ("page", "page id"),
    "section": ("section", "section title"),
    "section_order": ("section_order", "section order", "section no", "section no."),
    "row_order": ("row_order", "row order", "order", "no", "no."),
    "line_order": ("line_order", "line order", "line"),
    "row_key": ("row_key", "row key", "key"),
    "slot_key": ("slot_key", "slot key", "slot", "placement", "variant"),
    "row_label_source": ("row_label_source", "row label", "label", "item", "name"),
    "row_label_footnote_refs": ("row_label_footnote_refs", "row label footnotes", "label footnotes"),
    "param_source": ("param_source", "param", "parameter", "parameter name"),
    "param_footnote_refs": ("param_footnote_refs", "param footnotes", "parameter footnotes"),
    "value_source": ("value_source", "value", "specification", "spec", "description"),
    "value_footnote_refs": ("value_footnote_refs", "value footnotes", "spec footnotes"),
    "copy_key": ("copy_key", "copy key"),
    "page_id": ("page_id", "page id"),
    "copy_type": ("copy_type", "copy type", "type"),
    "source_text": ("source_text", "source text", "text"),
    "market": ("market", "region"),
    "model": ("model",),
    "source_lang": ("source_lang", "source lang", "lang"),
    "is_latest": ("is_latest", "is latest"),
    "version": ("version",),
    "notes": ("notes", "note"),
    "footnote_id": ("footnote_id", "footnote id"),
    "footnote_order": ("footnote_order", "footnote order", "order"),
    "note_id": ("note_id", "note id"),
    "note_order": ("note_order", "note order", "order"),
    "text": ("text", "text_en", "footnote text", "note text"),
    "enabled": ("enabled",),
}

_SPEC_LIKE_CANONICAL = {
    "row_key",
    "row_label_source",
    "param_source",
    "value_source",
    "slot_key",
}


def _header_key(value: str) -> str:
    return _HEADER_CLEAN_RE.sub("_", str(value or "").strip().casefold()).strip("_")


_ALIAS_LOOKUP = {
    _header_key(alias): canonical
    for canonical, aliases in _ALIASES.items()
    for alias in (canonical, *aliases)
}


def _canonicalize_row(row: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw_key, value in row.items():
        canonical = _ALIAS_LOOKUP.get(_header_key(raw_key))
        if canonical:
            out[canonical] = normalize_space(value)
        else:
            out[_header_key(raw_key)] = normalize_space(value)
    return out


def _slug(value: str, *, fallback: str = "row") -> str:
    token = _KEY_CLEAN_RE.sub("_", normalize_space(value).casefold()).strip("._-")
    return token or fallback


def _infer_page(table: MarkdownTable, row: dict[str, str]) -> str:
    explicit = row.get("page")
    if explicit:
        return explicit
    haystack = " / ".join(table.heading_path).casefold()
    if "product overview" in haystack or "overview" in haystack:
        return "Product overview"
    if "operation guide" in haystack or "operation" in haystack:
        return "operation_guide"
    if "app setup" in haystack or "app" in haystack:
        return "app_setup"
    return "specifications"


def _target_for_spec_like(table: MarkdownTable, row: dict[str, str]) -> str:
    explicit = normalize_space(row.get("target_table")).casefold()
    if explicit in {"page_placeholders_source", "page placeholders source", "page_placeholders"}:
        return TARGET_PAGE_PLACEHOLDERS
    if explicit in {"spec_master", "spec master"}:
        return TARGET_SPEC_MASTER
    return TARGET_SPEC_MASTER if page_is_specifications(_infer_page(table, row)) else TARGET_PAGE_PLACEHOLDERS


def _section_for(table: MarkdownTable, row: dict[str, str]) -> str:
    if row.get("section"):
        return row["section"]
    for part in reversed(table.heading_path):
        if part.casefold() not in {"specifications", "specification", "specs", "product overview"}:
            return part
    return table.heading_path[-1] if table.heading_path else ""


def _table_kind(table: MarkdownTable) -> str | None:
    canonical_headers = {_ALIAS_LOOKUP.get(_header_key(header), _header_key(header)) for header in table.headers}
    if {"copy_key", "source_text"} <= canonical_headers:
        return TARGET_MANUAL_COPY
    if "footnote_id" in canonical_headers:
        return TARGET_SPEC_FOOTNOTES
    if "note_id" in canonical_headers:
        return TARGET_SPEC_NOTES
    if canonical_headers & _SPEC_LIKE_CANONICAL:
        return "spec_like"
    return None


def _base_candidate(
    *,
    target_table: str,
    business_key: dict[str, str],
    fields: dict[str, str],
    table: MarkdownTable,
    row_index: int,
    status: str,
    warnings: list[str],
    operation: str = "unknown",
) -> dict[str, Any]:
    candidate = {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "candidate_hash": "",
        "target_table": target_table,
        "operation": operation,
        "status": status,
        "business_key": compact_dict(business_key),
        "fields": compact_dict(fields),
        "field_diffs": [],
        "warnings": warnings,
        "source_evidence": {
            "heading_path": list(table.heading_path),
            "table_start_line": table.start_line,
            "row_number": row_index + 1,
            "table": table_payload(table),
        },
    }
    candidate["candidate_hash"] = candidate_hash(candidate)
    return candidate


def _spec_candidate(
    table: MarkdownTable,
    raw_row: dict[str, str],
    *,
    row_index: int,
    document_key: str,
    source_lang: str,
    version: str,
    section_order: int,
) -> dict[str, Any]:
    row = _canonicalize_row(raw_row)
    model, region = model_region_from_document_key(document_key)
    page = _infer_page(table, row)
    target_table = _target_for_spec_like(table, row)
    row_label = row.get("row_label_source", "")
    row_key = row.get("row_key", "")
    warnings: list[str] = []
    if not row_key:
        row_key = _slug(row_label or row.get("param_source") or row.get("value_source"), fallback="")
        warnings.append("missing Row_key; generated a review-only suggested key")
    slot_key = row.get("slot_key", "")
    line_order = row.get("line_order") or "1"
    row_order = row.get("row_order") or str(row_index + 1)
    section = _section_for(table, row)
    fields = {
        "document_key": document_key,
        "Model": row.get("model") or model,
        "Region": region,
        "Source_lang": row.get("source_lang") or source_lang,
        "Version": row.get("version") or version,
        "Is_Latest": row.get("is_latest") or "TRUE",
        "Page": page,
        "Section": section,
        "Section_order": row.get("section_order") or str(section_order),
        "Row_order": row_order,
        "Row_key": row_key,
        "Slot_key": slot_key,
        "Row_label_source": row_label,
        "Row_label_footnote_refs": row.get("row_label_footnote_refs", ""),
        "Line_order": line_order,
        "Param_source": row.get("param_source", ""),
        "Param_footnote_refs": row.get("param_footnote_refs", ""),
        "Value_source": row.get("value_source", ""),
        "Value_footnote_refs": row.get("value_footnote_refs", ""),
    }
    has_text = any(fields.get(field) for field in SPEC_TEXT_FIELDS)
    status = "ready" if document_key and row.get("row_key") and has_text else "needs_review"
    if not has_text:
        warnings.append("no source text field was detected")
    return _base_candidate(
        target_table=target_table,
        business_key={
            "document_key": document_key,
            "row_key": row_key,
            "slot_key": slot_key,
            "line_order": line_order,
            "section": section,
        },
        fields=fields,
        table=table,
        row_index=row_index,
        status=status,
        warnings=warnings,
    )


def _manual_copy_candidate(
    table: MarkdownTable,
    raw_row: dict[str, str],
    *,
    row_index: int,
    source_lang: str,
    version: str,
) -> dict[str, Any]:
    row = _canonicalize_row(raw_row)
    warnings: list[str] = []
    if not row.get("copy_key"):
        warnings.append("missing copy_key")
    if not row.get("source_text"):
        warnings.append("missing source_text")
    fields = {
        "copy_key": row.get("copy_key", ""),
        "page_id": row.get("page_id", ""),
        "copy_type": row.get("copy_type", ""),
        "Market": row.get("market") or "ALL",
        "Model": row.get("model") or "ALL",
        "Source_lang": row.get("source_lang") or source_lang,
        "Is_Latest": row.get("is_latest") or "TRUE",
        "Version": row.get("version") or version,
        "source_text": row.get("source_text", ""),
        "section_order": row.get("section_order", ""),
        "notes": row.get("notes", ""),
    }
    return _base_candidate(
        target_table=TARGET_MANUAL_COPY,
        business_key={"copy_key": row.get("copy_key", "")},
        fields=fields,
        table=table,
        row_index=row_index,
        status="ready" if not warnings else "needs_review",
        warnings=warnings,
    )


def _footnote_candidate(
    table: MarkdownTable,
    raw_row: dict[str, str],
    *,
    row_index: int,
    target_table: str,
    document_key: str,
    source_lang: str,
) -> dict[str, Any]:
    row = _canonicalize_row(raw_row)
    model, region = model_region_from_document_key(document_key)
    id_field = "Footnote_id" if target_table == TARGET_SPEC_FOOTNOTES else "Note_id"
    order_field = "Footnote_order" if target_table == TARGET_SPEC_FOOTNOTES else "Note_order"
    key_name = "footnote_id" if target_table == TARGET_SPEC_FOOTNOTES else "note_id"
    order_name = "footnote_order" if target_table == TARGET_SPEC_FOOTNOTES else "note_order"
    text_field = f"Text_{source_lang}" if source_lang != "pt-BR" else "Text_pt-BR"
    if text_field not in FOOTNOTE_TEXT_FIELDS:
        text_field = "Text_en"
    warnings: list[str] = []
    if not row.get(key_name):
        warnings.append(f"missing {id_field}")
    text = row.get("text", "")
    if not text:
        warnings.append("missing text")
    fields = {
        id_field: row.get(key_name, ""),
        "Region": region,
        "Model": model,
        "Source_lang": row.get("source_lang") or source_lang,
        "Is_Latest": row.get("is_latest") or "TRUE",
        "Page": row.get("page") or "specifications",
        order_field: row.get(order_name) or str(row_index + 1),
        "Type": "Footnote" if target_table == TARGET_SPEC_FOOTNOTES else "Note",
        text_field: text,
        "Enabled": row.get("enabled") or "TRUE",
    }
    return _base_candidate(
        target_table=target_table,
        business_key={
            id_field: row.get(key_name, ""),
            "Region": region,
            "Model": model,
            "Page": fields["Page"],
        },
        fields=fields,
        table=table,
        row_index=row_index,
        status="ready" if not warnings else "needs_review",
        warnings=warnings,
    )


def extract_candidates_from_text(
    text: str,
    *,
    document_key: str,
    source_lang: str = "en",
    version: str = "",
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    section_order_by_path: dict[tuple[str, ...], int] = {}
    for table in parse_markdown_tables(text):
        kind = _table_kind(table)
        if kind is None:
            continue
        section_order_by_path.setdefault(table.heading_path, len(section_order_by_path) + 1)
        for row_index, raw_row in enumerate(table.rows):
            if kind == "spec_like":
                candidates.append(
                    _spec_candidate(
                        table,
                        raw_row,
                        row_index=row_index,
                        document_key=document_key,
                        source_lang=source_lang,
                        version=version,
                        section_order=section_order_by_path[table.heading_path],
                    )
                )
            elif kind == TARGET_MANUAL_COPY:
                candidates.append(
                    _manual_copy_candidate(
                        table,
                        raw_row,
                        row_index=row_index,
                        source_lang=source_lang,
                        version=version,
                    )
                )
            elif kind in {TARGET_SPEC_FOOTNOTES, TARGET_SPEC_NOTES}:
                candidates.append(
                    _footnote_candidate(
                        table,
                        raw_row,
                        row_index=row_index,
                        target_table=kind,
                        document_key=document_key,
                        source_lang=source_lang,
                    )
                )
    return candidates


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _source_rows_for_target(data_root: Path, target_table: str) -> list[dict[str, str]]:
    if target_table in {TARGET_SPEC_MASTER, TARGET_PAGE_PLACEHOLDERS}:
        rows = _read_csv(data_root / "Spec_Master.csv")
        if target_table == TARGET_SPEC_MASTER:
            return [row for row in rows if page_is_specifications(row.get("Page"))]
        return [row for row in rows if not page_is_specifications(row.get("Page"))]
    if target_table == TARGET_MANUAL_COPY:
        return _read_csv(data_root / "Manual_Copy_Source.csv")
    if target_table == TARGET_SPEC_FOOTNOTES:
        return _read_csv(data_root / "Spec_Footnotes.csv")
    if target_table == TARGET_SPEC_NOTES:
        return _read_csv(data_root / "Spec_Notes.csv")
    return []


def _matching_existing_rows(candidate: dict[str, Any], rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], str]:
    key = candidate.get("business_key") or {}
    target_table = candidate.get("target_table")
    if target_table in {TARGET_SPEC_MASTER, TARGET_PAGE_PLACEHOLDERS}:
        matches = [
            row
            for row in rows
            if normalize_space(row.get("document_key")) == normalize_space(key.get("document_key"))
            and normalize_space(row.get("Row_key")) == normalize_space(key.get("row_key"))
            and normalize_space(row.get("Slot_key")) == normalize_space(key.get("slot_key"))
        ]
        if len(matches) > 1 and key.get("line_order"):
            narrowed = [row for row in matches if normalize_space(row.get("Line_order")) == normalize_space(key.get("line_order"))]
            if narrowed:
                matches = narrowed
        if len(matches) > 1 and key.get("section"):
            narrowed = [row for row in matches if normalize_space(row.get("Section")).casefold() == normalize_space(key.get("section")).casefold()]
            if narrowed:
                matches = narrowed
        return matches, "business_key"
    if target_table == TARGET_MANUAL_COPY:
        return [row for row in rows if normalize_space(row.get("copy_key")) == normalize_space(key.get("copy_key"))], "copy_key"
    if target_table == TARGET_SPEC_FOOTNOTES:
        return [
            row
            for row in rows
            if normalize_space(row.get("Footnote_id")) == normalize_space(key.get("Footnote_id"))
            and normalize_space(row.get("Region")) == normalize_space(key.get("Region"))
            and normalize_space(row.get("Model")) == normalize_space(key.get("Model"))
            and normalize_space(row.get("Page")) == normalize_space(key.get("Page"))
        ], "Footnote_id+Region+Model+Page"
    if target_table == TARGET_SPEC_NOTES:
        return [
            row
            for row in rows
            if normalize_space(row.get("Note_id")) == normalize_space(key.get("Note_id"))
            and normalize_space(row.get("Region")) == normalize_space(key.get("Region"))
            and normalize_space(row.get("Model")) == normalize_space(key.get("Model"))
            and normalize_space(row.get("Page")) == normalize_space(key.get("Page"))
        ], "Note_id+Region+Model+Page"
    return [], "unsupported"


def _writable_fields_for(candidate: dict[str, Any]) -> tuple[str, ...]:
    target = candidate.get("target_table")
    if target in {TARGET_SPEC_MASTER, TARGET_PAGE_PLACEHOLDERS}:
        return SPEC_TEXT_FIELDS
    if target == TARGET_MANUAL_COPY:
        return MANUAL_COPY_TEXT_FIELDS
    if target == TARGET_SPEC_FOOTNOTES:
        return FOOTNOTE_TEXT_FIELDS
    if target == TARGET_SPEC_NOTES:
        return NOTE_TEXT_FIELDS
    return ()


def enrich_candidates_with_snapshot(candidates: list[dict[str, Any]], *, data_root: Path) -> list[dict[str, Any]]:
    rows_by_target = {
        target: _source_rows_for_target(data_root, target)
        for target in {
            TARGET_SPEC_MASTER,
            TARGET_PAGE_PLACEHOLDERS,
            TARGET_MANUAL_COPY,
            TARGET_SPEC_FOOTNOTES,
            TARGET_SPEC_NOTES,
        }
    }
    enriched: list[dict[str, Any]] = []
    for candidate in candidates:
        item = dict(candidate)
        rows = rows_by_target.get(str(item.get("target_table")), [])
        matches, strategy = _matching_existing_rows(item, rows)
        item["resolution"] = {"strategy": strategy, "matches": len(matches)}
        if item.get("status") != "ready":
            item["operation"] = "needs_review"
        elif not matches:
            item["operation"] = "create"
            item.setdefault("warnings", []).append("new record creation is review-only in MVP")
        elif len(matches) > 1:
            item["operation"] = "needs_review"
            item["status"] = "needs_review"
            item.setdefault("warnings", []).append("business key matched multiple snapshot rows")
        else:
            existing = matches[0]
            diffs = []
            for field in _writable_fields_for(item):
                new_value = item.get("fields", {}).get(field)
                if new_value in (None, ""):
                    continue
                old_value = existing.get(field, "")
                if normalize_space(old_value) != normalize_space(new_value):
                    diffs.append({"field": field, "old_value": old_value, "new_value": new_value})
            item["field_diffs"] = diffs
            item["operation"] = "update" if diffs else "noop"
        enriched.append(item)
    return enriched


def _source_ref_for(candidate: dict[str, Any], field: str, old_value: Any) -> dict[str, Any]:
    key = candidate.get("business_key") or {}
    table = candidate.get("target_table")
    source_ref: dict[str, Any] = {"table": table, "field": field, "matched_value": old_value}
    if table in {TARGET_SPEC_MASTER, TARGET_PAGE_PLACEHOLDERS}:
        source_ref.update(
            {
                "document_key": key.get("document_key"),
                "row_key": key.get("row_key"),
                "slot_key": key.get("slot_key", ""),
                "line_order": key.get("line_order", ""),
                "section": key.get("section", ""),
            }
        )
    elif table == TARGET_MANUAL_COPY:
        source_ref.update({"copy_key": key.get("copy_key")})
    return compact_dict(source_ref)


def _resolve_record_id(candidate: dict[str, Any], source_ref: dict[str, Any], sidecar_index: dict[str, Any] | None) -> tuple[str | None, str]:
    if not sidecar_index:
        return None, "snapshot_only"
    table = candidate.get("target_table")
    if table in {TARGET_SPEC_MASTER, TARGET_PAGE_PLACEHOLDERS}:
        return resolve_by_table(sidecar_index, source_ref)
    if table == TARGET_MANUAL_COPY:
        table_index = (sidecar_index.get("tables") or {}).get(TARGET_MANUAL_COPY)
        if not isinstance(table_index, dict):
            return None, "unresolved"
        copy_key = normalize_space((candidate.get("business_key") or {}).get("copy_key"))
        if not copy_key:
            return None, "unresolved"
        record_id = (table_index.get("records") or {}).get(copy_key)
        if record_id:
            return record_id, "resolved"
        if copy_key in (table_index.get("ambiguous") or []):
            return None, "ambiguous"
        return None, "unresolved"
    return None, "unsupported_table"


def build_change_request_report(candidates: list[dict[str, Any]], *, data_root: Path | None) -> dict[str, Any]:
    sidecar = load_index(data_root) if data_root else None
    requests: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("operation") != "update" or candidate.get("target_table") not in UPDATE_CAPABLE_TABLES:
            continue
        for diff in candidate.get("field_diffs") or []:
            field = str(diff.get("field") or "")
            old_value = diff.get("old_value")
            new_value = diff.get("new_value")
            source_ref = _source_ref_for(candidate, field, old_value)
            record_id, status = _resolve_record_id(candidate, source_ref, sidecar)
            requests.append(
                {
                    "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
                    "delta_hash": delta_hash(candidate, field, old_value, new_value),
                    "table": candidate.get("target_table"),
                    "field": field,
                    "record_id": record_id,
                    "resolution_status": status,
                    "old_text": old_value,
                    "new_text": new_value,
                    "old_value": old_value,
                    "new_value": new_value,
                    "source_ref": source_ref,
                    "blast_radius": [candidate.get("business_key")],
                    "external_write": False,
                    "intake_candidate_hash": candidate.get("candidate_hash"),
                }
            )
    return {
        "schema_version": CHANGE_REQUEST_SCHEMA_VERSION,
        "source": "source-intake",
        "external_write": False,
        "summary": {
            "requests": len(requests),
            "resolved_record_ids": sum(1 for request in requests if request.get("resolution_status") == "resolved"),
            "skipped_create_candidates": sum(1 for candidate in candidates if candidate.get("operation") == "create"),
            "needs_review_candidates": sum(1 for candidate in candidates if candidate.get("status") == "needs_review"),
        },
        "requests": requests,
    }


def candidates_payload(
    candidates: list[dict[str, Any]],
    *,
    run_id: str,
    source: str,
    document_key: str,
    data_root: Path | None,
) -> dict[str, Any]:
    summary = {
        "candidates": len(candidates),
        "ready": sum(1 for candidate in candidates if candidate.get("status") == "ready"),
        "needs_review": sum(1 for candidate in candidates if candidate.get("status") == "needs_review"),
        "create": sum(1 for candidate in candidates if candidate.get("operation") == "create"),
        "update": sum(1 for candidate in candidates if candidate.get("operation") == "update"),
        "noop": sum(1 for candidate in candidates if candidate.get("operation") == "noop"),
    }
    return {
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "run_id": run_id,
        "source": source,
        "document_key": document_key,
        "data_root": str(data_root) if data_root else None,
        "summary": summary,
        "candidates": candidates,
    }


def candidates_markdown(payload: dict[str, Any], change_report: dict[str, Any] | None = None) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "# Source Intake Report",
        "",
        f"- Run ID: `{payload.get('run_id')}`",
        f"- Source: `{payload.get('source')}`",
        f"- Document key: `{payload.get('document_key')}`",
        f"- Data root: `{payload.get('data_root') or 'not provided'}`",
        "",
        "## Checklist",
        "",
        "- [x] Read source document",
        "- [x] Extract candidate structured rows",
        "- [x] Classify candidates by target source table",
        f"- [{'x' if payload.get('data_root') else ' '}] Compare with current snapshot",
        f"- [{'x' if change_report is not None else ' '}] Emit approval-gated source-table change request",
        "- [ ] Human approves selected hashes",
        "- [ ] Apply approved requests with existing source-table writer",
        "- [ ] Run sync-data after live write",
        "- [ ] Run build/review/backport validation",
        "",
        "## Summary",
        "",
        f"- Candidates: {summary.get('candidates', 0)}",
        f"- Ready: {summary.get('ready', 0)}",
        f"- Needs review: {summary.get('needs_review', 0)}",
        f"- Create candidates: {summary.get('create', 0)}",
        f"- Update candidates: {summary.get('update', 0)}",
        f"- No-op candidates: {summary.get('noop', 0)}",
        "",
    ]
    if change_report is not None:
        cr_summary = change_report.get("summary") or {}
        lines.extend(
            [
                "## Change Request",
                "",
                f"- Requests: {cr_summary.get('requests', 0)}",
                f"- Resolved record IDs: {cr_summary.get('resolved_record_ids', 0)}",
                f"- Create candidates skipped by MVP writer: {cr_summary.get('skipped_create_candidates', 0)}",
                "",
            ]
        )
    lines.extend(["## Candidates", ""])
    for candidate in payload.get("candidates") or []:
        fields = candidate.get("fields") or {}
        warnings = "; ".join(candidate.get("warnings") or [])
        label = fields.get("Row_label_source") or fields.get("source_text") or fields.get("Value_source") or candidate.get("candidate_hash")
        lines.append(
            f"- `{candidate.get('status')}` `{candidate.get('operation')}` "
            f"{candidate.get('target_table')} `{candidate.get('candidate_hash')}` — {label}"
        )
        if warnings:
            lines.append(f"  warnings: {warnings}")
        for diff in candidate.get("field_diffs") or []:
            lines.append(
                f"  diff `{diff.get('field')}`: {diff.get('old_value')!r} -> {diff.get('new_value')!r}"
            )
    lines.append("")
    return "\n".join(lines)


def write_intake_outputs(
    *,
    out_dir: Path,
    candidates: list[dict[str, Any]],
    run_id: str,
    source: str,
    document_key: str,
    data_root: Path | None,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    change_report = build_change_request_report(candidates, data_root=data_root) if data_root else None
    payload = candidates_payload(
        candidates,
        run_id=run_id,
        source=source,
        document_key=document_key,
        data_root=data_root,
    )
    candidates_path = out_dir / "source_intake_candidates.json"
    report_path = out_dir / "source_intake_report.md"
    candidates_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(candidates_markdown(payload, change_report), encoding="utf-8")
    paths = {"candidates": candidates_path, "report": report_path}
    if change_report is not None:
        change_path = out_dir / "source_intake_source_table_change_request.json"
        change_path.write_text(json.dumps(change_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths["change_request"] = change_path
    return paths
