"""Create-or-update one row in the published-manual catalog (发布文档管理).

``tools/manual_index_query.py`` only reads this Base; no tool in this repo
writes it. This module closes that gap for the Web Publish Git-only receipt
step (``build.py web-receipt``): given one released target's model/region/
lang/link/version, it locates the matching catalog row (if any) by
(model, region, lang, doc_type) and creates or updates it, then reads the
written record back to confirm the persisted value -- the mandatory
write-readback discipline in
``.agents/skills/lark-cli-bitable-ops/SKILL.md``.

Field *names* are not re-guessed here: they are imported from
``tools.manual_index_query``, the one place that already declares this
table's field constants from a live read. Two things are still assumptions
this module introduces, and both need confirming against the live Base
before the first ``--write`` run:

- ``CATALOG_WEB_DOC_TYPE`` (the literal ``"web"`` value written to
  ``文档类型``). Existing rows use hand-entered, human-language doc-type
  labels (``User Manual``, ``取扱説明書``, ``사용자 매뉴얼``); there is no
  established convention for a pipeline-authored Web release row.
  ``文档类型`` is a Select-type field elsewhere in this Base, so a brand new
  option name may need to be added (or an existing one reassigned) in the
  Feishu UI before a write can persist.
- the region/language *values* written to ``区域`` / ``源语言``:
  :func:`resolve_catalog_region_label` reuses this table's own
  ``manual_index_query._REGION_ALIASES`` vocabulary (Chinese labels such as
  "美加规", "欧规"); :func:`resolve_catalog_lang_label` reuses
  ``manual_index_query._LANG_ALIASES`` (``EN``/``JP``/``CN``/``KR``) and
  falls back to an uppercased raw code for a language that vocabulary does
  not cover (for example ``fr`` -> ``FR``). ``源语言`` historically records
  the *source* manual's language, not a rendered target language, so a Web
  release's target language may be a new kind of value for that column too.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from tools.document_link_queue import scalar_text
from tools.manual_index_query import (
    FIELD_DOC_TYPE,
    FIELD_MANUAL_LINK,
    FIELD_MODELS,
    FIELD_REGION,
    FIELD_SOURCE_LANG,
    FIELD_VERSION,
    ManualIndexRow,
    ManualIndexSettings,
    _LANG_ALIASES,
    _REGION_ALIASES,
    manual_index_row_from_record,
)

# See the module docstring: not yet confirmed against a live `文档类型`
# Select-field option list.
CATALOG_WEB_DOC_TYPE = "web"

_MODEL_DELIMITER_RE = re.compile(r"[,，/、]+")


@dataclass(frozen=True)
class RecordReadbackResult:
    """Outcome of re-fetching one record and comparing it against what was written."""

    ok: bool
    detail: str


@dataclass(frozen=True)
class CatalogWritebackResult:
    status: str  # "created" | "updated" | "ambiguous" | "failed"
    record_id: str | None
    detail: str
    written_fields: dict[str, str] | None = None


def resolve_catalog_region_label(region: str) -> str:
    """Map a build region code (``US``, ``eu``, ...) to this table's stored label."""

    cleaned = str(region or "").strip()
    return _REGION_ALIASES.get(cleaned.casefold(), cleaned)


def resolve_catalog_lang_label(lang: str) -> str:
    """Map a build language code (``en``, ``fr``, ...) to this table's stored label."""

    cleaned = str(lang or "").strip()
    return _LANG_ALIASES.get(cleaned.casefold(), cleaned.upper())


def _model_tokens(values: tuple[str, ...]) -> tuple[str, ...]:
    tokens: list[str] = []
    for value in values:
        tokens.extend(part.strip() for part in _MODEL_DELIMITER_RE.split(value) if part.strip())
    return tuple(tokens)


def find_catalog_candidates(
    rows: list[ManualIndexRow],
    *,
    model: str,
    region_label: str,
    lang_label: str,
    doc_type: str = CATALOG_WEB_DOC_TYPE,
) -> tuple[ManualIndexRow, ...]:
    """Filter already-parsed catalog rows to the (model, region, lang, doc_type) match set."""

    model_key = model.strip().casefold()
    region_key = region_label.strip().casefold()
    lang_key = lang_label.strip().casefold()
    doc_type_key = doc_type.strip().casefold()
    matches: list[ManualIndexRow] = []
    for row in rows:
        if model_key not in {token.casefold() for token in _model_tokens(row.product_models)}:
            continue
        if region_key not in {value.casefold() for value in row.region}:
            continue
        if lang_key not in {value.casefold() for value in row.source_lang}:
            continue
        if doc_type_key not in {value.casefold() for value in row.doc_type}:
            continue
        matches.append(row)
    return tuple(matches)


def verify_record_fields(
    *,
    source: Any,
    base_token: str,
    table_id: str,
    view_id: str | None,
    record_id: str,
    expected_fields: dict[str, str],
) -> RecordReadbackResult:
    """GET the record back (via a fresh list fetch) and confirm every expected field.

    There is no dedicated single-record GET wrapper on ``LarkCliSource``
    today, so the readback reuses the already-tested ``fetch_records_with_ids``
    surface (the same one every other read path in this table's tooling
    uses) and locates the one row by ``record_id``.
    """

    raw_records = source.fetch_records_with_ids(base_token=base_token, table_id=table_id, view_id=view_id)
    for record in raw_records:
        if str(record.get("record_id") or "").strip() != record_id:
            continue
        fields_raw = record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        mismatches = {
            key: {"expected": expected, "actual": scalar_text(fields.get(key))}
            for key, expected in expected_fields.items()
            if scalar_text(fields.get(key)) != expected
        }
        if mismatches:
            return RecordReadbackResult(False, f"readback mismatch for {record_id}: {mismatches}")
        confirmed = ", ".join(f"{key}={value}" for key, value in expected_fields.items())
        return RecordReadbackResult(True, f"readback confirmed {record_id}: {confirmed}")
    return RecordReadbackResult(False, f"readback did not find record {record_id} after write")


def write_catalog_record(
    *,
    source: Any,
    settings: ManualIndexSettings,
    model: str,
    region: str,
    lang: str,
    link: str,
    version: str,
    doc_type: str = CATALOG_WEB_DOC_TYPE,
) -> CatalogWritebackResult:
    """Create or update the one catalog row for (model, region, lang, doc_type).

    Zero matching rows -> create one (with the key fields plus link/version).
    Exactly one match -> update only 说明书链接/版本 on that row. More than one
    match is ambiguous and is rejected with every candidate record_id listed,
    same as the Document_link receipt locator -- resolving that is a human
    decision, not something this module guesses at.
    """

    region_label = resolve_catalog_region_label(region)
    lang_label = resolve_catalog_lang_label(lang)
    raw_records = source.fetch_records_with_ids(
        base_token=settings.base_token,
        table_id=settings.table_id,
        view_id=settings.view_id or None,
    )
    rows = [manual_index_row_from_record(record) for record in raw_records]
    candidates = find_catalog_candidates(
        rows,
        model=model,
        region_label=region_label,
        lang_label=lang_label,
        doc_type=doc_type,
    )
    if len(candidates) > 1:
        candidate_ids = ", ".join(row.record_id for row in candidates)
        return CatalogWritebackResult(
            status="ambiguous",
            record_id=None,
            detail=(
                f"{len(candidates)} catalog rows matched model={model} region={region_label} "
                f"lang={lang_label} doc_type={doc_type}; candidates: {candidate_ids}"
            ),
        )

    link_and_version = {FIELD_MANUAL_LINK: link, FIELD_VERSION: version}
    if candidates:
        record_id = candidates[0].record_id
        source.upsert_record(
            base_token=settings.base_token,
            table_id=settings.table_id,
            record_id=record_id,
            record=link_and_version,
        )
        action = "updated"
    else:
        create_fields = {
            FIELD_MODELS: model,
            FIELD_REGION: region_label,
            FIELD_SOURCE_LANG: lang_label,
            FIELD_DOC_TYPE: doc_type,
            **link_and_version,
        }
        record_id = source.create_record(
            base_token=settings.base_token,
            table_id=settings.table_id,
            fields=create_fields,
        )
        action = "created"

    readback = verify_record_fields(
        source=source,
        base_token=settings.base_token,
        table_id=settings.table_id,
        view_id=settings.view_id or None,
        record_id=record_id,
        expected_fields=link_and_version,
    )
    if not readback.ok:
        return CatalogWritebackResult(status="failed", record_id=record_id, detail=readback.detail)
    return CatalogWritebackResult(
        status=action,
        record_id=record_id,
        detail=f"{action} catalog row; {readback.detail}",
        written_fields=dict(link_and_version),
    )


__all__ = (
    "CATALOG_WEB_DOC_TYPE",
    "CatalogWritebackResult",
    "RecordReadbackResult",
    "find_catalog_candidates",
    "resolve_catalog_lang_label",
    "resolve_catalog_region_label",
    "verify_record_fields",
    "write_catalog_record",
)
