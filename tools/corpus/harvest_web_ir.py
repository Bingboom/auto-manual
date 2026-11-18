"""Harvest aligned multilingual copy units from committed Web manual.ir.json files."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

from tools import lang_registry
from tools.corpus.align import (
    AbstainedPage,
    AlignedSegmentPair,
    align_ir_pair,
    normalize_space,
)
from tools.corpus.discover import (
    default_anchor_lang,
    discover_ir_pairs,
)
from tools.manual_copy_source import (
    MANUAL_COPY_TAG,
    MANUAL_COPY_TAG_FIELD,
    TM_LANGUAGE_FIELDS,
)

HARVEST_SCHEMA_VERSION = "auto-manual-web-ir-tm-harvest/v1"
REPO_ROOT = Path(__file__).resolve().parents[2]


def tm_column_for_lang(lang: str) -> str:
    """Map an IR language code to its Translation_Memory column name."""

    raw = (lang or "").strip()
    normalized = raw.casefold().replace("_", "-")
    if normalized in TM_LANGUAGE_FIELDS:
        return TM_LANGUAGE_FIELDS[normalized]
    spec = lang_registry.language_spec(normalized)
    if spec is not None:
        return spec.tm_column
    return raw


def _cell_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return normalize_space(value)
    if isinstance(value, dict):
        return normalize_space(str(value.get("name") or value.get("text") or ""))
    if isinstance(value, (list, tuple)):
        parts = [_cell_to_text(item) for item in value]
        return normalize_space(" ".join(part for part in parts if part))
    return normalize_space(str(value))


def _row_status(fields: dict[str, str]) -> str:
    raw = fields.get("Status") or fields.get("status") or ""
    return raw.strip().casefold()


def _normalize_snapshot_rows(raw_rows: list[Any]) -> list[tuple[str, dict[str, str]]]:
    normalized: list[tuple[str, dict[str, str]]] = []
    for item in raw_rows:
        if not isinstance(item, dict):
            continue
        fields_raw = item.get("fields")
        if isinstance(fields_raw, dict):
            rid = str(item.get("record_id") or "")
            fields = {str(k): _cell_to_text(v) for k, v in fields_raw.items()}
        else:
            rid = str(item.get("record_id") or item.get("_record_id") or "")
            fields = {
                str(k): _cell_to_text(v)
                for k, v in item.items()
                if k not in ("record_id", "_record_id")
            }
        normalized.append((rid, fields))
    return normalized


def load_tm_snapshot(
    snapshot_path: Path,
    *,
    anchor_column: str,
) -> dict[str, list[dict[str, Any]]]:
    """Load a Translation_Memory JSON cache or CSV backup indexed by anchor text."""

    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    suffix = snapshot_path.suffix.casefold()
    rows: list[tuple[str, dict[str, str]]] = []
    if suffix == ".json":
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            rows = _normalize_snapshot_rows(payload["rows"])
        elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
            rows = _normalize_snapshot_rows(payload["records"])
        elif isinstance(payload, list):
            rows = _normalize_snapshot_rows(payload)
        else:
            raise ValueError(f"Unsupported TM JSON snapshot shape: {snapshot_path}")
    else:
        with snapshot_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = _normalize_snapshot_rows(list(reader))

    for rid, fields in rows:
        if _row_status(fields) == "deprecated":
            continue
        anchor_text = normalize_space(fields.get(anchor_column, ""))
        if not anchor_text:
            continue
        index[anchor_text.casefold()].append({"record_id": rid, "fields": fields})
    return dict(index)


def _provenance_for_pairs(pairs: Sequence[AlignedSegmentPair]) -> dict[str, list[str]]:
    models = sorted({pair.model for pair in pairs})
    regions = sorted({pair.region for pair in pairs})
    page_stems = sorted({pair.page_stem for pair in pairs})
    shas = sorted(
        {pair.anchor_ir_sha256 for pair in pairs} | {pair.target_ir_sha256 for pair in pairs}
    )
    paths = sorted(
        {pair.anchor_ir_path for pair in pairs} | {pair.target_ir_path for pair in pairs}
    )
    return {
        "models": models,
        "regions": regions,
        "page_stems": page_stems,
        "source_ir_sha256": shas,
        "source_ir_paths": paths,
    }


def _build_conflict_record(
    *,
    en_text: str,
    content_attribute: str | None,
    lang_column: str,
    variants: dict[str, list[AlignedSegmentPair]],
) -> dict[str, Any]:
    variant_entries = [
        {
            "translation": translation,
            "count": len(occ),
            "models": sorted({item.model for item in occ}),
            "regions": sorted({item.region for item in occ}),
            "page_stems": sorted({item.page_stem for item in occ}),
            "source_ir_paths": sorted({item.target_ir_path for item in occ}),
        }
        for translation, occ in sorted(variants.items())
    ]
    return {
        "en": en_text,
        "content_attribute": content_attribute,
        "lang_column": lang_column,
        "variants": variant_entries,
    }


def _resolve_model_variants(
    *,
    en_text: str,
    content_attribute: str | None,
    lang_column: str,
    occ: list[AlignedSegmentPair],
    conflicts: list[dict[str, Any]],
) -> dict[str, str]:
    by_model: dict[str, dict[str, list[AlignedSegmentPair]]] = defaultdict(lambda: defaultdict(list))
    for pair in occ:
        by_model[pair.model][normalize_space(pair.target_text)].append(pair)
    resolved: dict[str, str] = {}
    for model_name, variants in sorted(by_model.items()):
        if len(variants) == 1:
            resolved[model_name] = next(iter(variants))
        else:
            conflicts.append(
                _build_conflict_record(
                    en_text=en_text,
                    content_attribute=content_attribute,
                    lang_column=f"{lang_column}@{model_name}",
                    variants=variants,
                )
            )
    return resolved


def _resolve_group_translations(
    *,
    en_text: str,
    content_attribute: str | None,
    group_pairs: list[AlignedSegmentPair],
    allow_model_variants: bool,
    conflicts: list[dict[str, Any]],
) -> list[tuple[str | None, dict[str, str], list[AlignedSegmentPair]]]:
    by_col: dict[str, dict[str, list[AlignedSegmentPair]]] = defaultdict(lambda: defaultdict(list))
    for pair in group_pairs:
        col = tm_column_for_lang(pair.target_lang)
        target_norm = normalize_space(pair.target_text)
        if col and target_norm:
            by_col[col][target_norm].append(pair)

    consensus: dict[str, str] = {}
    variant_cols: dict[str, dict[str, str]] = {}
    for col, variants in sorted(by_col.items()):
        if len(variants) == 1:
            consensus[col] = next(iter(variants))
        elif allow_model_variants:
            occ = [pair for plist in variants.values() for pair in plist]
            per_model = _resolve_model_variants(
                en_text=en_text,
                content_attribute=content_attribute,
                lang_column=col,
                occ=occ,
                conflicts=conflicts,
            )
            if per_model:
                variant_cols[col] = per_model
        else:
            conflicts.append(
                _build_conflict_record(
                    en_text=en_text,
                    content_attribute=content_attribute,
                    lang_column=col,
                    variants=variants,
                )
            )

    if not variant_cols:
        return [(None, consensus, group_pairs)] if consensus else []

    models_with_variants = sorted(
        {model for per_model in variant_cols.values() for model in per_model}
    )
    scoped_rows: list[tuple[str | None, dict[str, str], list[AlignedSegmentPair]]] = []
    for model_name in models_with_variants:
        merged = dict(consensus)
        for col, per_model in sorted(variant_cols.items()):
            if model_name in per_model:
                merged[col] = per_model[model_name]
        model_pairs = [pair for pair in group_pairs if pair.model == model_name]
        if merged:
            scoped_rows.append((model_name, merged, model_pairs))
    return scoped_rows


def _build_create_record(
    *,
    anchor_column: str,
    anchor_text: str,
    translations: dict[str, str],
    content_attribute: str | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        anchor_column: anchor_text,
        **dict(sorted(translations.items())),
        "Status": "Draft",
        MANUAL_COPY_TAG_FIELD: [MANUAL_COPY_TAG],
    }
    if content_attribute:
        record["content_attribute"] = [content_attribute]
    return record


def _classify_against_tm(
    *,
    anchor_column: str,
    en_text: str,
    content_attribute: str | None,
    translations: dict[str, str],
    model_scope: str | None,
    supporting_pairs: list[AlignedSegmentPair],
    tm_index: dict[str, list[dict[str, Any]]],
    new_rows: list[dict[str, Any]],
    backfill_candidates: list[dict[str, Any]],
    create_records: list[dict[str, Any]],
) -> int:
    provenance = _provenance_for_pairs(supporting_pairs)
    matched_tm = tm_index.get(en_text.casefold())
    if matched_tm is not None:
        missing_fields: dict[str, str] = {}
        for col, val in sorted(translations.items()):
            if not any(row["fields"].get(col) for row in matched_tm):
                missing_fields[col] = val
        if missing_fields:
            backfill_candidates.append(
                {
                    "en": en_text,
                    "content_attribute": content_attribute,
                    "tm_record_ids": [row["record_id"] for row in matched_tm if row["record_id"]],
                    "missing_fields": missing_fields,
                    "provenance": provenance,
                }
            )
        return 1

    row_entry: dict[str, Any] = {
        "en": en_text,
        "content_attribute": content_attribute,
        "translations": dict(sorted(translations.items())),
        "provenance": provenance,
    }
    if model_scope:
        row_entry["model_scope"] = model_scope
    new_rows.append(row_entry)
    create_records.append(
        _build_create_record(
            anchor_column=anchor_column,
            anchor_text=en_text,
            translations=translations,
            content_attribute=content_attribute,
        )
    )
    return 0


def harvest_web_ir(
    *,
    repo_root: Path = REPO_ROOT,
    roots: Sequence[Path] = (),
    model: str | None = None,
    region: str | None = None,
    anchor_lang: str | None = None,
    explicit_anchor_irs: Sequence[Path] = (),
    tm_snapshot_path: Path | None = None,
    allow_model_variants: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run read-only Web IR corpus harvest and return (report, staging_payload)."""

    effective_anchor = anchor_lang or default_anchor_lang()
    anchor_column = tm_column_for_lang(effective_anchor)
    tm_index = (
        load_tm_snapshot(tm_snapshot_path, anchor_column=anchor_column)
        if tm_snapshot_path is not None
        else {}
    )

    discovered, pairs, pkg_abstentions, skipped_files = discover_ir_pairs(
        repo_root=repo_root,
        roots=roots,
        model=model,
        region=region,
        anchor_lang=effective_anchor,
        explicit_anchor_irs=explicit_anchor_irs,
    )

    aligned_segments: list[AlignedSegmentPair] = []
    abstained_pages: list[AbstainedPage] = []
    aligned_page_count = 0
    for pair in pairs:
        segs, page_abstentions, ok_pages = align_ir_pair(pair)
        aligned_segments.extend(segs)
        abstained_pages.extend(page_abstentions)
        aligned_page_count += ok_pages

    grouped: dict[tuple[str, str | None], list[AlignedSegmentPair]] = defaultdict(list)
    for seg in aligned_segments:
        grouped[(normalize_space(seg.en_text), seg.content_attribute)].append(seg)

    conflicts: list[dict[str, Any]] = []
    new_rows: list[dict[str, Any]] = []
    backfill_candidates: list[dict[str, Any]] = []
    create_records: list[dict[str, Any]] = []
    skipped_existing_in_tm = 0

    for (en_text, content_attr), group_pairs in sorted(
        grouped.items(), key=lambda kv: (kv[0][0].casefold(), kv[0][0], kv[0][1] or "")
    ):
        resolved_rows = _resolve_group_translations(
            en_text=en_text,
            content_attribute=content_attr,
            group_pairs=group_pairs,
            allow_model_variants=allow_model_variants,
            conflicts=conflicts,
        )
        for model_scope, translations, supporting_pairs in resolved_rows:
            skipped_existing_in_tm += _classify_against_tm(
                anchor_column=anchor_column,
                en_text=en_text,
                content_attribute=content_attr,
                translations=translations,
                model_scope=model_scope,
                supporting_pairs=supporting_pairs,
                tm_index=tm_index,
                new_rows=new_rows,
                backfill_candidates=backfill_candidates,
                create_records=create_records,
            )

    report: dict[str, Any] = {
        "schema_version": HARVEST_SCHEMA_VERSION,
        "anchor_lang": anchor_column,
        "allow_model_variants": allow_model_variants,
        "summary": {
            "discovered_irs": len(discovered),
            "paired_irs": len(pairs),
            "abstained_packages": len(pkg_abstentions),
            "skipped_files": len(skipped_files),
            "aligned_pages": aligned_page_count,
            "abstained_pages": len(abstained_pages),
            "extracted_segments": len(aligned_segments),
            "new_rows": len(new_rows),
            "backfill_candidates": len(backfill_candidates),
            "skipped_existing_in_tm": skipped_existing_in_tm,
            "conflicts": len(conflicts),
            "create_records": len(create_records),
        },
        "new_rows": new_rows,
        "backfill_candidates": backfill_candidates,
        "conflicts": conflicts,
        "abstained_pages": [item.to_dict() for item in abstained_pages],
        "abstained_packages": [item.to_dict() for item in pkg_abstentions],
        "skipped_files": skipped_files,
    }
    staging_payload = {"create_records": create_records}
    return report, staging_payload


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for harvest_web_ir."""

    parser = argparse.ArgumentParser(
        description="Harvest aligned multilingual copy from committed Web manual.ir.json bundles."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used for default source discovery and relative paths.",
    )
    parser.add_argument(
        "--root",
        dest="roots",
        action="append",
        type=Path,
        default=[],
        help="Source directory or manual.ir.json path to scan (repeatable).",
    )
    parser.add_argument("--model", default=None, help="Filter to a single model name.")
    parser.add_argument("--region", default=None, help="Filter to a single region.")
    parser.add_argument(
        "--anchor-lang",
        default=None,
        help="Anchor language code (defaults to TM_LANGUAGE_FIELDS English key).",
    )
    parser.add_argument(
        "--anchor-ir",
        dest="anchor_irs",
        action="append",
        type=Path,
        default=[],
        help="Explicit anchor manual.ir.json path for split-package pairing.",
    )
    parser.add_argument(
        "--tm-snapshot",
        type=Path,
        default=None,
        help="Existing Translation_Memory JSON cache or CSV backup for deduplication.",
    )
    parser.add_argument(
        "--allow-model-variants",
        action="store_true",
        help="Emit per-model scoped rows when models disagree on a target translation.",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=None,
        help="Optional path to write the full harvest report JSON.",
    )
    parser.add_argument(
        "--staging-out",
        type=Path,
        default=None,
        help="Optional path to write Feishu create_records staging JSON (Status: Draft).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for tools.corpus.harvest_web_ir."""

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    report, staging_payload = harvest_web_ir(
        repo_root=args.repo_root.resolve(),
        roots=args.roots,
        model=args.model,
        region=args.region,
        anchor_lang=args.anchor_lang,
        explicit_anchor_irs=args.anchor_irs,
        tm_snapshot_path=args.tm_snapshot,
        allow_model_variants=args.allow_model_variants,
    )
    if args.report_out is not None:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.staging_out is not None:
        args.staging_out.parent.mkdir(parents=True, exist_ok=True)
        args.staging_out.write_text(
            json.dumps(staging_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.report_out is None:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
