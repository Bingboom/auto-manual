"""``build.py web-receipt``: the Web Publish Git-only transaction's receipt step.

``build.py web-release`` (steps 2-3 of the Git-only transaction in
``code-as-doc/dev/web_publish_pipeline.md`` §2.2) builds, seals and stages one
Web Publish book, but never touches any live Feishu table. Two records still
need to land after an operator reviews and merges the resulting release:

1. ``Document_link.HTML_link`` -- the deterministic Read the Docs route. The
   existing writer (``tools/write_web_publish_html_link.py``) only locates a
   row through ``publish_meta.json``'s ``queue_record_ids``, which is empty
   for every Git-only book (there was never a queue row), so this has always
   been a manual step for that path.
2. One row in the published-manual catalog (发布文档管理), which today has no
   writer at all (``tools/manual_index_query.py`` only reads it); see
   ``tools/manual_catalog_writeback.py``.

This module is the orchestration layer: for every discovered
``latest/web/publish_meta.json`` target (optionally narrowed by
``--model``/``--region``/``--lang``), it resolves the Document_link row
through an explicit priority chain (``--receipt-record-id`` overrides ->
``publish_meta.json`` ``queue_record_ids`` -> live search by
model/region/lang), then writes both records and GETs each one back to
confirm the persisted value -- the mandatory write-readback discipline in
``.agents/skills/lark-cli-bitable-ops/SKILL.md``.

Defaults to dry-run: without ``--write`` this only reads local
``publish_meta.json`` files and prints the resolved plan. No live table is
read or written unless ``--write`` is passed explicitly.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from tools.document_link_queue import (
    document_key_from_document_id,
    explicit_document_key,
    looks_like_explicit_document_key,
    parse_document_key,
    scalar_text,
)
from tools.language_aliases import normalize_language, normalize_region
from tools.listen_build_queue_lark import fetch_field_id_map
from tools.manual_catalog_writeback import (
    CATALOG_WEB_DOC_TYPE,
    CatalogWritebackResult,
    resolve_catalog_lang_label,
    resolve_catalog_region_label,
    verify_record_fields,
    write_catalog_record,
)
from tools.manual_index_query import manual_index_settings_from_env
from tools.phase2_support import LarkCliSource, cli_bin, load_config, phase2_identity
from tools.queue_bound_binding import collect_queue_preflight_errors, resolve_document_link_binding
from tools.queue_bound_lark_ops import run_lark_cli_json
from tools.queue_contract import DOCUMENT_ID_FIELD, DOCUMENT_KEY_FIELD, LANG_FIELD, VERSION_FIELD
from tools.write_web_publish_html_link import (
    latest_web_publish_metadata,
    resolve_html_link_field_name,
    target_record_ids_from_publish_meta,
    target_rtd_url,
)

DEFAULT_RTD_BASE_URL = "https://ht-doc.readthedocs.io"


@dataclass(frozen=True)
class ReceiptTarget:
    model: str
    region: str
    lang: str
    metadata_path: Path
    payload: dict[str, Any]

    def label(self) -> str:
        return f"{self.model}/{self.region}/{self.lang}"


@dataclass(frozen=True)
class ReceiptWriteResult:
    status: str  # "written" | "skipped" | "ambiguous" | "failed"
    record_ids: tuple[str, ...]
    detail: str
    url: str | None = None


@dataclass(frozen=True)
class TargetReceiptOutcome:
    target: ReceiptTarget
    html: ReceiptWriteResult | None
    catalog: CatalogWritebackResult | None

    @property
    def status(self) -> str:
        bad_statuses = {"ambiguous", "failed"}
        html_bad = self.html is not None and self.html.status in bad_statuses
        catalog_bad = self.catalog is not None and self.catalog.status in bad_statuses
        return "failed" if (html_bad or catalog_bad) else "ok"


def _read_metadata(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Web Publish metadata root must be an object: {path}")
    if str(payload.get("schema_version") or "") != "auto-manual-web-publish/v1":
        raise RuntimeError(f"Unsupported Web Publish metadata schema: {path}")
    return payload


def discover_receipt_targets(
    releases_root: Path,
    *,
    model: str | None = None,
    region: str | None = None,
    lang: str | None = None,
) -> list[ReceiptTarget]:
    """Find every ``latest/web/publish_meta.json`` target, optionally narrowed."""

    targets: list[ReceiptTarget] = []
    for metadata_path in latest_web_publish_metadata(releases_root):
        payload = _read_metadata(metadata_path)
        target_model = str(payload.get("model") or "").strip()
        target_region = str(payload.get("region") or "").strip()
        target_lang = str(payload.get("lang") or "").strip()
        if not target_model or not target_region or not target_lang:
            raise RuntimeError(
                f"Web Publish metadata is missing model, region, or lang: {metadata_path}"
            )
        if model and model.strip().casefold() != target_model.casefold():
            continue
        if region and region.strip().casefold() != target_region.casefold():
            continue
        if lang and normalize_language(lang).casefold() != normalize_language(target_lang).casefold():
            continue
        targets.append(
            ReceiptTarget(
                model=target_model,
                region=target_region,
                lang=target_lang,
                metadata_path=metadata_path,
                payload=payload,
            )
        )
    if not targets:
        raise RuntimeError(f"No Web Publish metadata matched the requested filters under {releases_root}")
    return targets


def _resolve_document_link_row_target(fields: dict[str, Any]) -> tuple[str, str] | None:
    """Resolve one Document_link row's (model, region), tolerantly.

    Mirrors ``document_link_queue.resolve_target_for_record`` but returns
    ``None`` instead of raising, since this scans every row in the table
    looking for a match and an unresolvable sibling row is not an error.
    """

    document_key_raw = scalar_text(fields.get(DOCUMENT_KEY_FIELD))
    document_id_raw = scalar_text(fields.get(DOCUMENT_ID_FIELD))
    lang_raw = scalar_text(fields.get(LANG_FIELD))
    version_raw = scalar_text(fields.get(VERSION_FIELD))
    candidates: list[str] = []
    explicit_key = explicit_document_key(document_key_raw)
    if explicit_key:
        candidates.append(explicit_key)
    fallback_key = document_key_from_document_id(
        document_id=document_id_raw, lang=lang_raw, version=version_raw
    )
    if looks_like_explicit_document_key(fallback_key) and fallback_key not in candidates:
        candidates.append(fallback_key)
    for candidate in candidates:
        try:
            return parse_document_key(candidate)
        except RuntimeError:
            continue
    return None


def find_document_link_candidates(
    raw_records: list[dict[str, Any]],
    *,
    model: str,
    region: str,
    lang: str,
) -> tuple[str, ...]:
    """Search Document_link rows for ones whose resolved target matches.

    Used only as the last-resort locator (see the priority chain in the
    module docstring), when neither an explicit record id nor
    ``publish_meta.json``'s ``queue_record_ids`` is available -- the normal
    case for a Git-only book, which never had a queue row.
    """

    target_model = model.strip().casefold()
    target_region = normalize_region(region).casefold()
    target_lang = normalize_language(lang).casefold()
    matches: list[str] = []
    for record in raw_records:
        record_id = str(record.get("record_id") or "").strip()
        if not record_id:
            continue
        fields_raw = record.get("fields", {})
        fields = fields_raw if isinstance(fields_raw, dict) else {}
        resolved = _resolve_document_link_row_target(fields)
        if resolved is None:
            continue
        row_model, row_region = resolved
        if row_model.strip().casefold() != target_model:
            continue
        if row_region.casefold() != target_region:
            continue
        row_lang = normalize_language(scalar_text(fields.get(LANG_FIELD))).casefold()
        if row_lang != target_lang:
            continue
        if record_id not in matches:
            matches.append(record_id)
    return tuple(matches)


def resolve_receipt_record_ids(
    *,
    target: ReceiptTarget,
    explicit_record_ids: tuple[str, ...],
    source: Any,
    binding: Any,
) -> tuple[tuple[str, ...], str]:
    """Apply the locate priority chain; returns (record_ids, locate_mode)."""

    if explicit_record_ids:
        return target_record_ids_from_publish_meta(
            target.payload, explicit_record_ids=explicit_record_ids
        ), "explicit --receipt-record-id"
    from_meta = target_record_ids_from_publish_meta(target.payload)
    if from_meta:
        return from_meta, "publish_meta.json queue_record_ids"
    raw_records = source.fetch_records_with_ids(
        base_token=binding.base_token, table_id=binding.table_id, view_id=binding.view_id
    )
    found = find_document_link_candidates(
        raw_records, model=target.model, region=target.region, lang=target.lang
    )
    return found, "search Document_link by model/region/lang"


def write_html_receipt(
    *,
    target: ReceiptTarget,
    explicit_record_ids: tuple[str, ...],
    base_url: str,
    source: Any,
    binding: Any,
    field_name: str,
) -> ReceiptWriteResult:
    url = target_rtd_url(base_url=base_url, payload=target.payload)
    record_ids, locate_mode = resolve_receipt_record_ids(
        target=target, explicit_record_ids=explicit_record_ids, source=source, binding=binding
    )
    if not record_ids:
        return ReceiptWriteResult(
            status="skipped",
            record_ids=(),
            detail=f"no Document_link row found via {locate_mode}",
            url=url,
        )
    if len(record_ids) > 1:
        return ReceiptWriteResult(
            status="ambiguous",
            record_ids=record_ids,
            detail=(
                f"{len(record_ids)} Document_link rows matched via {locate_mode}; "
                f"candidates: {', '.join(record_ids)}"
            ),
            url=url,
        )

    record_id = record_ids[0]
    source.upsert_record(
        base_token=binding.base_token,
        table_id=binding.table_id,
        record_id=record_id,
        record={field_name: url},
    )
    readback = verify_record_fields(
        source=source,
        base_token=binding.base_token,
        table_id=binding.table_id,
        view_id=binding.view_id,
        record_id=record_id,
        expected_fields={field_name: url},
    )
    if not readback.ok:
        return ReceiptWriteResult(status="failed", record_ids=record_ids, detail=readback.detail, url=url)
    return ReceiptWriteResult(
        status="written",
        record_ids=record_ids,
        detail=f"located via {locate_mode}; {readback.detail}",
        url=url,
    )


def _locate_mode_preview(target: ReceiptTarget, *, explicit_record_ids: tuple[str, ...]) -> str:
    if explicit_record_ids:
        return "explicit --receipt-record-id"
    if target_record_ids_from_publish_meta(target.payload):
        return "publish_meta.json queue_record_ids"
    return "search Document_link by model/region/lang (resolved only with --write)"


def _print_dry_run_plan(
    targets: Sequence[ReceiptTarget], *, base_url: str, explicit_record_ids: tuple[str, ...]
) -> None:
    print(f"[web-receipt] plan: {len(targets)} target(s); no live table will be read or written (--dry-run)")
    for target in targets:
        url = target_rtd_url(base_url=base_url, payload=target.payload)
        region_label = resolve_catalog_region_label(target.region)
        lang_label = resolve_catalog_lang_label(target.lang)
        version = str(target.payload.get("version") or "")
        locate_mode = _locate_mode_preview(target, explicit_record_ids=explicit_record_ids)
        print(f"[web-receipt]   - {target.label()}")
        print(f"[web-receipt]       HTML_link -> {url} (locate via {locate_mode})")
        print(
            "[web-receipt]       catalog    -> model="
            f"{target.model} region={region_label} lang={lang_label} "
            f"doc_type={CATALOG_WEB_DOC_TYPE} version={version} link={url}"
        )


def _print_summary(outcomes: Sequence[TargetReceiptOutcome]) -> None:
    print("[web-receipt] summary:")
    for outcome in outcomes:
        html_id = (
            ", ".join(outcome.html.record_ids)
            if outcome.html is not None and outcome.html.record_ids
            else "-"
        )
        catalog_id = outcome.catalog.record_id if outcome.catalog is not None and outcome.catalog.record_id else "-"
        print(
            f"[web-receipt]   {outcome.target.label():16} | html={html_id} | catalog={catalog_id} "
            f"| status={outcome.status.upper()}"
        )
    ok = sum(1 for outcome in outcomes if outcome.status == "ok")
    print(f"[web-receipt] {ok}/{len(outcomes)} target(s) receipted")


def run_web_receipt(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    resolve_path_from_root: Callable[[str], Path],
) -> None:
    """Entry point wired as ``build.py``'s ``web-receipt`` action."""

    config_path = resolve_path_from_root(args.config)
    releases_root = resolve_path_from_root(str(getattr(args, "releases_root", None) or "reports/releases"))
    base_url = str(getattr(args, "base_url", None) or "").strip() or DEFAULT_RTD_BASE_URL
    explicit_record_ids = tuple(
        dict.fromkeys(
            str(item).strip()
            for item in (getattr(args, "receipt_record_id", None) or ())
            if str(item).strip()
        )
    )
    model_filter = str(getattr(args, "model", None) or "").strip() or None
    region_filter = str(getattr(args, "region", None) or "").strip() or None
    lang_filter = str(getattr(args, "lang", None) or "").strip() or None
    write = bool(getattr(args, "write", False))

    targets = discover_receipt_targets(
        releases_root, model=model_filter, region=region_filter, lang=lang_filter
    )

    if not write:
        _print_dry_run_plan(targets, base_url=base_url, explicit_record_ids=explicit_record_ids)
        return

    cfg = load_config(config_path)
    errors = collect_queue_preflight_errors(cfg)
    if errors:
        raise RuntimeError("web-receipt preflight failed:\n- " + "\n- ".join(errors))
    binding = resolve_document_link_binding(cfg)
    resolved_cli_bin = cli_bin(cfg)
    identity = phase2_identity()
    html_source = LarkCliSource(cli_bin=resolved_cli_bin, identity=identity)
    field_id_map = fetch_field_id_map(
        cli_bin=resolved_cli_bin,
        base_token=binding.base_token,
        table_id=binding.table_id,
        identity=identity,
        run_lark_cli_json=run_lark_cli_json,
    )
    html_field_name = resolve_html_link_field_name(field_id_map)
    if not html_field_name:
        raise RuntimeError("Document_link does not expose a writable HTML_link field")

    catalog_settings = manual_index_settings_from_env(cfg)
    catalog_source = LarkCliSource(cli_bin=resolved_cli_bin, identity=catalog_settings.identity)

    outcomes: list[TargetReceiptOutcome] = []
    for target in targets:
        try:
            html_result = write_html_receipt(
                target=target,
                explicit_record_ids=explicit_record_ids,
                base_url=base_url,
                source=html_source,
                binding=binding,
                field_name=html_field_name,
            )
        except (RuntimeError, OSError) as exc:
            html_result = ReceiptWriteResult(status="failed", record_ids=(), detail=str(exc))
        print(f"[web-receipt] {target.label()} HTML_link: {html_result.status} - {html_result.detail}")

        version = str(target.payload.get("version") or "").strip()
        link_for_catalog = html_result.url or target_rtd_url(base_url=base_url, payload=target.payload)
        try:
            catalog_result = write_catalog_record(
                source=catalog_source,
                settings=catalog_settings,
                model=target.model,
                region=target.region,
                lang=target.lang,
                link=link_for_catalog,
                version=version,
            )
        except (RuntimeError, OSError) as exc:
            catalog_result = CatalogWritebackResult(status="failed", record_id=None, detail=str(exc))
        print(f"[web-receipt] {target.label()} catalog: {catalog_result.status} - {catalog_result.detail}")

        outcomes.append(TargetReceiptOutcome(target=target, html=html_result, catalog=catalog_result))

    _print_summary(outcomes)
    failed = [outcome for outcome in outcomes if outcome.status == "failed"]
    if failed:
        raise RuntimeError(
            f"web-receipt: {len(failed)}/{len(outcomes)} target(s) failed: "
            + "; ".join(outcome.target.label() for outcome in failed)
        )


__all__ = (
    "DEFAULT_RTD_BASE_URL",
    "ReceiptTarget",
    "ReceiptWriteResult",
    "TargetReceiptOutcome",
    "discover_receipt_targets",
    "find_document_link_candidates",
    "resolve_receipt_record_ids",
    "run_web_receipt",
    "write_html_receipt",
)
