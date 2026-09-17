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
table's field constants from a live read. The first ``--write`` live-run
(2026-09-17) surfaced two Select-field collisions and the operator settled
both (a third decision from that same round -- treating a Git-only book's
``HTML_link`` skip as expected, not a failure -- lives in ``web_receipt.py``
instead, since it is about the Document_link table, not this one):

- ``文档类型`` is a Select field whose existing options are all hand-entered,
  per-language *printed*-manual labels (``User Manual``, ``取扱説明書``,
  ``사용자 매뉴얼``, ...) -- reusing one of those for a pipeline-authored Web
  row would make the (model, region, lang, doc_type) keyed lookup collide
  with the printed row it is supposed to sit beside. ``CATALOG_WEB_DOC_TYPE``
  is therefore its own dedicated option, ``"Web手册"``, distinct from every
  printed-manual label.
- ``版本`` is also a Select field, pre-populated with a small fixed
  vocabulary (``V2.0``, ``V1.0``, ``未知``, ...). A raw git version/commit
  string written there would pollute that option list with one-off values,
  so every Web-receipted row writes the constant
  ``CATALOG_UNKNOWN_VERSION_LABEL`` ("未知", an option that already exists)
  instead. The real version string -- together with the HTML_link alias URL
  -- is preserved in ``备注`` (:func:`format_catalog_notes`), a free-text
  field, so nothing is actually lost.
- the region/language *values* written to ``区域`` / ``源语言``:
  :func:`resolve_catalog_region_label` reuses this table's own
  ``manual_index_query._REGION_ALIASES`` vocabulary (Chinese labels such as
  "美加规", "欧规"); :func:`resolve_catalog_lang_label` reuses
  ``manual_index_query._LANG_ALIASES`` (``EN``/``JP``/``CN``/``KR``) and
  falls back to an uppercased raw code for a language that vocabulary does
  not cover (for example ``fr`` -> ``FR``). ``源语言`` historically records
  the *source* manual's language, not a rendered target language, so a Web
  release's target language may be a new kind of value for that column too.

Both Select fields are option-checked before every create (see
:func:`ensure_select_option`): missing options are appended via a full-PUT
``+field-update`` (existing options carried through unchanged) rather than
assumed to already exist, since a write against an unknown option name fails
outright (``not_found``).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable

from tools.document_link_queue import scalar_text
from tools.manual_index_query import (
    FIELD_DOC_TYPE,
    FIELD_MANUAL_LINK,
    FIELD_MODELS,
    FIELD_NOTES,
    FIELD_REGION,
    FIELD_SOURCE_LANG,
    FIELD_VERSION,
    MANUAL_INDEX_IDENTITY_ENV,
    ManualIndexRow,
    ManualIndexSettings,
    _LANG_ALIASES,
    _REGION_ALIASES,
    manual_index_row_from_record,
    manual_index_settings_from_env,
)
from tools.queue_bound_lark_ops import run_lark_cli_json

# See the module docstring: confirmed against the live `文档类型` Select-field
# option list on the 2026-09-17 --write first-run (operator decision).
CATALOG_WEB_DOC_TYPE = "Web手册"

# The `版本` Select field's placeholder value for every Web-receipted row;
# the real version string lives in `备注` instead (see format_catalog_notes).
CATALOG_UNKNOWN_VERSION_LABEL = "未知"

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


def catalog_writeback_settings_from_env(cfg: dict[str, Any]) -> ManualIndexSettings:
    """Resolve the catalog Base coordinates like the read path does, but default identity to "user".

    ``manual_index_query.manual_index_settings_from_env`` is the read-only path (also used by
    chat-facing lookups): when ``FEISHU_MANUAL_INDEX_IDENTITY`` is unset it falls back to
    ``FEISHU_PHASE2_IDENTITY``/``phase2_identity()``, which in this repo's local/CI environment
    commonly resolves to the phase2 "bot" application. Live-tested 2026-09-17: writing to the
    发布文档管理 Base as that bot fails with error 91403 -- it has never been granted access to
    this business Base -- while the interactive "user" identity can both read and write it.

    A catalog *write* must not silently inherit the read path's bot-leaning fallback, so identity
    is resolved independently here: default to "user" unless ``FEISHU_MANUAL_INDEX_IDENTITY`` is
    set explicitly (which still wins outright, including an explicit "bot" if that grant is ever
    added). The read-only query path in ``manual_index_query`` is intentionally left unchanged --
    this function only covers the writeback side.
    """

    explicit_identity = os.environ.get(MANUAL_INDEX_IDENTITY_ENV, "").strip().lower()
    identity = explicit_identity or "user"
    if identity not in {"user", "bot"}:
        raise RuntimeError(f"{MANUAL_INDEX_IDENTITY_ENV} must be one of: bot, user")
    base = manual_index_settings_from_env(cfg)
    return ManualIndexSettings(
        base_token=base.base_token,
        table_id=base.table_id,
        view_id=base.view_id,
        identity=identity,
        source_url=base.source_url,
    )


def format_catalog_notes(*, version: str, link: str) -> str:
    """Build the ``备注`` payload that preserves the real version and the HTML_link alias URL.

    ``版本`` always gets the constant :data:`CATALOG_UNKNOWN_VERSION_LABEL` (see the module
    docstring), so the actual version string would otherwise be lost. ``备注`` is a plain text
    field, so it carries both the real version and the alias URL instead.
    """

    return f"version={version}; alias={link}"


def _fetch_select_field(
    *,
    cli_bin: str,
    identity: str,
    base_token: str,
    table_id: str,
    field_name: str,
    run_lark_cli_json: Callable[..., dict[str, Any]],
) -> tuple[str, list[dict[str, Any]], bool] | None:
    """Return ``(field_id, options, multiple)`` for one Select field, or ``None`` if not found."""

    payload = run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "base",
            "+field-list",
            "--as",
            identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--format",
            "json",
            "--limit",
            "200",
        ],
    )
    data = payload.get("data")
    items = data.get("items") if isinstance(data, dict) else None
    if items is None and isinstance(data, dict):
        items = data.get("fields")
    if not isinstance(items, list):
        raise RuntimeError("Lark CLI field list response has invalid items/fields payload")
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("field_name") or item.get("name") or "").strip()
        if name != field_name:
            continue
        field_id = str(item.get("field_id") or item.get("id") or "").strip()
        prop = item.get("property") if isinstance(item.get("property"), dict) else {}
        options_raw = item.get("options")
        if options_raw is None:
            options_raw = prop.get("options")
        options = [option for option in (options_raw or []) if isinstance(option, dict)]
        multiple = bool(item.get("multiple") or prop.get("multiple"))
        return field_id, options, multiple
    return None


def ensure_select_option(
    *,
    cli_bin: str,
    identity: str,
    base_token: str,
    table_id: str,
    field_name: str,
    option_name: str,
    run_lark_cli_json: Callable[..., dict[str, Any]],
) -> bool:
    """Add ``option_name`` to a Select field's options if it is not already there.

    A record write against an option name that does not yet exist on the field fails outright
    (``not_found``), so this is the mandatory pre-check before writing a brand new option value
    (see ``.agents/skills/lark-cli-bitable-ops/references/cli-recipes.md``, the Select /
    Multi-select field-type trap row). ``+field-update`` is a full PUT of the options array, so
    every existing option is carried through unchanged (name, hue, lightness, ...) and only the
    missing one is appended -- nothing already on the field is dropped or reordered.

    Returns ``True`` if an option was actually appended, ``False`` if it already existed.
    """

    option_name = option_name.strip()
    if not option_name:
        return False
    resolved = _fetch_select_field(
        cli_bin=cli_bin,
        identity=identity,
        base_token=base_token,
        table_id=table_id,
        field_name=field_name,
        run_lark_cli_json=run_lark_cli_json,
    )
    if resolved is None:
        raise RuntimeError(f"catalog field {field_name!r} was not found via +field-list")
    field_id, options, multiple = resolved
    existing_names = {str(option.get("name") or "").strip() for option in options}
    if option_name in existing_names:
        return False
    updated_options = [*options, {"name": option_name}]
    field_payload: dict[str, Any] = {"name": field_name, "type": "select", "options": updated_options}
    if multiple:
        field_payload["multiple"] = True
    run_lark_cli_json(
        cli_bin=cli_bin,
        args=[
            "base",
            "+field-update",
            "--as",
            identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--field-id",
            field_id,
            "--format",
            "json",
            "--json",
            json.dumps(field_payload, ensure_ascii=False),
        ],
    )
    return True


def _ensure_catalog_select_options(
    *,
    source: Any,
    settings: ManualIndexSettings,
    doc_type: str,
    version_label: str,
) -> None:
    """Pre-check + append missing ``文档类型``/``版本`` Select options before a create."""

    cli_bin = getattr(source, "cli_bin", "")
    identity = getattr(source, "identity", "") or settings.identity
    for field_name, option_name in ((FIELD_DOC_TYPE, doc_type), (FIELD_VERSION, version_label)):
        ensure_select_option(
            cli_bin=cli_bin,
            identity=identity,
            base_token=settings.base_token,
            table_id=settings.table_id,
            field_name=field_name,
            option_name=option_name,
            run_lark_cli_json=run_lark_cli_json,
        )


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

    Zero matching rows -> create one (with the key fields plus link/notes, and 版本 fixed to
    :data:`CATALOG_UNKNOWN_VERSION_LABEL`). Exactly one match -> update only 说明书链接/备注 on
    that row; 版本 is left untouched (operator decision -- see the module docstring). More than
    one match is ambiguous and is rejected with every candidate record_id listed, same as the
    Document_link receipt locator -- resolving that is a human decision, not something this
    module guesses at.

    ``version`` here is the real build version string; it is never written to the ``版本``
    Select field (which would pollute its fixed option vocabulary) -- it is preserved in ``备注``
    instead, alongside the ``link`` alias URL (:func:`format_catalog_notes`).
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

    notes_value = format_catalog_notes(version=version, link=link)
    if candidates:
        record_id = candidates[0].record_id
        written_fields = {FIELD_MANUAL_LINK: link, FIELD_NOTES: notes_value}
        source.upsert_record(
            base_token=settings.base_token,
            table_id=settings.table_id,
            record_id=record_id,
            record=written_fields,
        )
        action = "updated"
    else:
        _ensure_catalog_select_options(
            source=source,
            settings=settings,
            doc_type=doc_type,
            version_label=CATALOG_UNKNOWN_VERSION_LABEL,
        )
        written_fields = {
            FIELD_MANUAL_LINK: link,
            FIELD_VERSION: CATALOG_UNKNOWN_VERSION_LABEL,
            FIELD_NOTES: notes_value,
        }
        create_fields = {
            FIELD_MODELS: model,
            FIELD_REGION: region_label,
            FIELD_SOURCE_LANG: lang_label,
            FIELD_DOC_TYPE: doc_type,
            **written_fields,
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
        expected_fields=written_fields,
    )
    if not readback.ok:
        return CatalogWritebackResult(status="failed", record_id=record_id, detail=readback.detail)
    return CatalogWritebackResult(
        status=action,
        record_id=record_id,
        detail=f"{action} catalog row; {readback.detail}",
        written_fields=dict(written_fields),
    )


__all__ = (
    "CATALOG_UNKNOWN_VERSION_LABEL",
    "CATALOG_WEB_DOC_TYPE",
    "CatalogWritebackResult",
    "RecordReadbackResult",
    "catalog_writeback_settings_from_env",
    "ensure_select_option",
    "find_catalog_candidates",
    "format_catalog_notes",
    "resolve_catalog_lang_label",
    "resolve_catalog_region_label",
    "verify_record_fields",
    "write_catalog_record",
)
