#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.spec_topic_contract import (  # noqa: E402
    SpecTopicFixtures,
    load_spec_topic_fixtures,
    render_spec_topic_report,
    validate_spec_topic_fixtures,
)


SPEC_MASTER_COMPAT_HEADERS: tuple[str, ...] = (
    "document_key",
    "Region",
    "Is_Latest",
    "Page",
    "Section",
    "Section_order",
    "Row_order",
    "Row_key",
    "Slot_key",
    "Row_label_source",
    "Row_label_footnote_refs",
    "Line_order",
    "Param_source",
    "Param_footnote_refs",
    "Value_source",
    "Value_footnote_refs",
    "Row_label_fr",
    "Param_fr",
    "Value_fr",
    "Row_label_es",
    "Model",
    "Param_es",
    "Value_es",
    "Source_lang",
)

FORBIDDEN_OUTPUT_DIRS = (
    Path("data/phase1"),
    Path("data/phase2"),
    Path("docs/_review"),
    Path("docs/_build"),
    Path("reports/releases"),
)


def _resolve_path(path: str | Path, *, root: Path = ROOT) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def _row_value(row: dict[str, str], field_name: str) -> str:
    return str(row.get(field_name, "")).strip()


def _sort_number(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def _topics_by_id(fixtures: SpecTopicFixtures) -> dict[str, dict[str, str]]:
    return {_row_value(row, "topic_id"): row for row in fixtures.spec_topics if _row_value(row, "topic_id")}


def _rows_by_id(fixtures: SpecTopicFixtures) -> dict[str, dict[str, str]]:
    return {_row_value(row, "topic_row_id"): row for row in fixtures.spec_topic_rows if _row_value(row, "topic_row_id")}


def _value_applies(
    row: dict[str, str],
    *,
    document_key: str | None,
    model: str | None,
    region: str | None,
) -> bool:
    if document_key and _row_value(row, "document_key") != document_key:
        return False
    if model and _row_value(row, "model") != model:
        return False
    if region and _row_value(row, "region") != region:
        return False
    return True


def adapt_spec_topics_to_spec_master(
    *,
    fixtures_dir: Path,
    document_key: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> tuple[dict[str, str], ...]:
    result = validate_spec_topic_fixtures(fixtures_dir=fixtures_dir)
    if not result.valid:
        raise RuntimeError(render_spec_topic_report(result))

    fixtures = load_spec_topic_fixtures(fixtures_dir)
    topics = _topics_by_id(fixtures)
    rows = _rows_by_id(fixtures)
    output: list[dict[str, str]] = []

    for value_row in fixtures.spec_topic_values:
        if not _value_applies(value_row, document_key=document_key, model=model, region=region):
            continue
        topic_row = rows[_row_value(value_row, "topic_row_id")]
        topic = topics[_row_value(topic_row, "topic_id")]
        output.append(
            {
                "document_key": _row_value(value_row, "document_key"),
                "Region": _row_value(value_row, "region"),
                "Is_Latest": _row_value(value_row, "is_latest"),
                "Page": _row_value(topic, "page"),
                "Section": _row_value(topic, "section"),
                "Section_order": _row_value(topic, "section_order"),
                "Row_order": _row_value(topic_row, "row_order"),
                "Row_key": _row_value(topic_row, "row_key"),
                "Slot_key": _row_value(topic_row, "slot_key"),
                "Row_label_source": _row_value(value_row, "row_label_source"),
                "Row_label_footnote_refs": _row_value(value_row, "row_label_footnote_refs"),
                "Line_order": _row_value(topic_row, "line_order"),
                "Param_source": _row_value(value_row, "param_source"),
                "Param_footnote_refs": _row_value(value_row, "param_footnote_refs"),
                "Value_source": _row_value(value_row, "value_source"),
                "Value_footnote_refs": _row_value(value_row, "value_footnote_refs"),
                "Row_label_fr": _row_value(value_row, "row_label_fr"),
                "Param_fr": _row_value(value_row, "param_fr"),
                "Value_fr": _row_value(value_row, "value_fr"),
                "Row_label_es": _row_value(value_row, "row_label_es"),
                "Model": _row_value(value_row, "model"),
                "Param_es": _row_value(value_row, "param_es"),
                "Value_es": _row_value(value_row, "value_es"),
                "Source_lang": _row_value(value_row, "source_lang"),
            }
        )

    return tuple(
        sorted(
            output,
            key=lambda row: (
                row["document_key"],
                row["Model"],
                row["Region"],
                _sort_number(row["Section_order"]),
                _sort_number(row["Row_order"]),
                row["Row_key"],
                _sort_number(row["Line_order"]),
                row["Slot_key"],
            ),
        )
    )


def _ensure_safe_output_path(output_path: Path, *, repo_root: Path = ROOT) -> None:
    resolved = output_path.resolve()
    for relative_dir in FORBIDDEN_OUTPUT_DIRS:
        forbidden = (repo_root / relative_dir).resolve()
        try:
            resolved.relative_to(forbidden)
        except ValueError:
            continue
        raise RuntimeError(f"spec topic adapter output must not write under {relative_dir}")


def write_spec_master(rows: tuple[dict[str, str], ...], *, output_path: Path, repo_root: Path = ROOT) -> None:
    _ensure_safe_output_path(output_path, repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SPEC_MASTER_COMPAT_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in SPEC_MASTER_COMPAT_HEADERS})


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export compatible Spec_Master.csv rows from spec-topic fixtures.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    export_parser = subparsers.add_parser("export-spec-master", help="Export a compatible Spec_Master CSV.")
    export_parser.add_argument("--fixtures", required=True, help="Directory containing spec-topic CSV fixtures.")
    export_parser.add_argument("--output", required=True, help="Output CSV path.")
    export_parser.add_argument("--document-key", help="Optional document_key filter.")
    export_parser.add_argument("--model", help="Optional model filter.")
    export_parser.add_argument("--region", help="Optional region filter.")
    args = parser.parse_args(argv)

    try:
        rows = adapt_spec_topics_to_spec_master(
            fixtures_dir=_resolve_path(args.fixtures),
            document_key=args.document_key,
            model=args.model,
            region=args.region,
        )
        write_spec_master(rows, output_path=_resolve_path(args.output))
    except RuntimeError as exc:
        print(f"[spec-topic-adapter] ERROR {exc}", file=sys.stderr)
        return 1

    print(f"[spec-topic-adapter] wrote {_resolve_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
