#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from itertools import product
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.content_assembly_contract import CONTENT_ASSEMBLY_TABLE_HEADERS  # noqa: E402
from tools.topic_map_contract import (  # noqa: E402
    TopicMapFixtures,
    load_topic_map_fixtures,
    render_topic_map_report,
    split_multi_value,
    validate_topic_map_fixtures,
)


FORBIDDEN_OUTPUT_DIRS = (
    Path("docs/templates"),
    Path("docs/_review"),
    Path("docs/_build"),
    Path("reports/releases"),
)

CONTENT_ASSEMBLY_TABLE_ORDER = (
    "page_assembly",
    "content_blocks",
    "block_fields",
    "asset_registry",
    "block_rules",
)


def _resolve_path(path: str | Path, *, root: Path = ROOT) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def _row_value(row: dict[str, str], field_name: str) -> str:
    return str(row.get(field_name, "")).strip()


def _is_truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _sort_number(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def _registry_by_id(fixtures: TopicMapFixtures) -> dict[str, dict[str, str]]:
    return {_row_value(row, "topic_id"): row for row in fixtures.topic_registry if _row_value(row, "topic_id")}


def _active_topic_ids_for_page_rows(page_rows: tuple[dict[str, str], ...]) -> set[str]:
    return {_row_value(row, "topic_id") for row in page_rows if _row_value(row, "topic_id")}


def _page_topic_rows(
    fixtures: TopicMapFixtures,
    *,
    page_id: str | None = None,
    product_family: str | None = None,
) -> tuple[dict[str, str], ...]:
    rows = []
    for row in fixtures.page_topic_map:
        if page_id and _row_value(row, "page_id") != page_id:
            continue
        if product_family and _row_value(row, "product_family") != product_family:
            continue
        rows.append(row)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_value(row, "page_id"),
                _row_value(row, "product_family"),
                _sort_number(_row_value(row, "topic_order")),
                _row_value(row, "topic_id"),
                _row_value(row, "region"),
                _row_value(row, "lang"),
            ),
        )
    )


def _asset_rows_by_topic(fixtures: TopicMapFixtures, topic_ids: set[str]) -> dict[str, list[dict[str, str]]]:
    assets: dict[str, list[dict[str, str]]] = {topic_id: [] for topic_id in topic_ids}
    for row in fixtures.topic_assets:
        topic_id = _row_value(row, "topic_id")
        if topic_id in topic_ids and _row_value(row, "status").lower() == "active":
            assets.setdefault(topic_id, []).append(row)
    for rows in assets.values():
        rows.sort(key=lambda row: (not _is_truthy(row.get("required", "")), _row_value(row, "asset_key")))
    return assets


def _asset_key_for_topic(assets_by_topic: dict[str, list[dict[str, str]]], topic_id: str) -> str:
    rows = assets_by_topic.get(topic_id, [])
    if not rows:
        return ""
    return _row_value(rows[0], "asset_key")


def _title_overrides_by_topic(fixtures: TopicMapFixtures, topic_ids: set[str]) -> dict[str, list[dict[str, str]]]:
    overrides: dict[str, list[dict[str, str]]] = {topic_id: [] for topic_id in topic_ids}
    for row in fixtures.topic_content:
        topic_id = _row_value(row, "topic_id")
        if (
            topic_id in topic_ids
            and _row_value(row, "status").lower() == "active"
            and _row_value(row, "content_key") == "title_key"
        ):
            overrides.setdefault(topic_id, []).append(row)
    for rows in overrides.values():
        rows.sort(key=lambda row: (_row_value(row, "region"), _row_value(row, "lang"), _row_value(row, "content_id")))
    return overrides


def _adapt_page_assembly(
    fixtures: TopicMapFixtures,
    *,
    page_rows: tuple[dict[str, str], ...],
) -> tuple[dict[str, str], ...]:
    registry = _registry_by_id(fixtures)
    rows: list[dict[str, str]] = []
    for row in page_rows:
        topic_id = _row_value(row, "topic_id")
        topic = registry.get(topic_id, {})
        for region, lang in product(split_multi_value(_row_value(row, "region")), split_multi_value(_row_value(row, "lang"))):
            rows.append(
                {
                    "page_id": _row_value(row, "page_id"),
                    "product_family": _row_value(row, "product_family"),
                    "region": region,
                    "lang": lang.lower() if lang != "*" else lang,
                    "block_id": topic_id,
                    "block_type": _row_value(topic, "topic_type"),
                    "order": _row_value(row, "topic_order"),
                    "enabled": _row_value(row, "enabled"),
                    "fallback_lang": _row_value(row, "fallback_lang"),
                }
            )
    return tuple(rows)


def _adapt_content_blocks(
    fixtures: TopicMapFixtures,
    *,
    topic_ids: set[str],
) -> tuple[dict[str, str], ...]:
    assets_by_topic = _asset_rows_by_topic(fixtures, topic_ids)
    title_overrides = _title_overrides_by_topic(fixtures, topic_ids)
    rows: list[dict[str, str]] = []
    for topic in sorted(fixtures.topic_registry, key=lambda row: _row_value(row, "topic_id")):
        topic_id = _row_value(topic, "topic_id")
        if topic_id not in topic_ids:
            continue
        base_row = {
            "block_id": topic_id,
            "block_type": _row_value(topic, "topic_type"),
            "parent_block_id": "",
            "title_key": _row_value(topic, "topic_title"),
            "asset_key": _asset_key_for_topic(assets_by_topic, topic_id),
            "repeatable": _row_value(topic, "repeatable"),
            "region": "*",
            "lang": "*",
        }
        rows.append(base_row)
        for override in title_overrides.get(topic_id, []):
            rows.append(
                {
                    **base_row,
                    "title_key": _row_value(override, "content_rst"),
                    "region": _row_value(override, "region") or "*",
                    "lang": (_row_value(override, "lang") or "*").lower(),
                }
            )
    return tuple(rows)


def _adapt_block_fields(
    fixtures: TopicMapFixtures,
    *,
    topic_ids: set[str],
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for row in fixtures.topic_fields:
        topic_id = _row_value(row, "topic_id")
        if topic_id not in topic_ids:
            continue
        rows.append(
            {
                "block_id": topic_id,
                "field_key": _row_value(row, "field_key"),
                "row_key": _row_value(row, "row_key"),
                "value_role": _row_value(row, "value_role"),
                "placement_key": _row_value(row, "placement_key"),
                "variant_key": _row_value(row, "variant_key"),
                "required": _row_value(row, "required"),
                "fallback_policy": _row_value(row, "fallback_policy"),
            }
        )
    return tuple(rows)


def _adapt_asset_registry(
    fixtures: TopicMapFixtures,
    *,
    topic_ids: set[str],
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for row in fixtures.topic_assets:
        if _row_value(row, "topic_id") not in topic_ids or _row_value(row, "status").lower() != "active":
            continue
        rows.append(
            {
                "asset_key": _row_value(row, "asset_key"),
                "path": _row_value(row, "asset_path"),
                "alt_key": _row_value(row, "alt_key"),
                "region": _row_value(row, "region") or "*",
                "lang": (_row_value(row, "lang") or "*").lower(),
                "required": _row_value(row, "required"),
            }
        )
    return tuple(sorted(rows, key=lambda row: _row_value(row, "asset_key")))


def _adapt_block_rules(
    fixtures: TopicMapFixtures,
    *,
    topic_ids: set[str],
) -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for row in fixtures.topic_rules:
        if _row_value(row, "topic_id") not in topic_ids or not _is_truthy(row.get("enabled", "")):
            continue
        rows.append(
            {
                "block_id": _row_value(row, "topic_id"),
                "condition_key": _row_value(row, "condition_key"),
                "operator": _row_value(row, "operator"),
                "condition_value": _row_value(row, "condition_value"),
                "action": _row_value(row, "action"),
            }
        )
    return tuple(rows)


def adapt_topic_map_to_content_assembly(
    *,
    fixtures_dir: Path,
    page_id: str | None = None,
    product_family: str | None = None,
    repo_root: Path = ROOT,
) -> dict[str, tuple[dict[str, str], ...]]:
    result = validate_topic_map_fixtures(fixtures_dir=fixtures_dir, repo_root=repo_root)
    if not result.valid:
        raise RuntimeError(render_topic_map_report(result))

    fixtures = load_topic_map_fixtures(fixtures_dir)
    page_rows = _page_topic_rows(fixtures, page_id=page_id, product_family=product_family)
    if not page_rows:
        raise RuntimeError("topic map adapter found no page_topic_map rows for the requested scope")
    topic_ids = _active_topic_ids_for_page_rows(page_rows)

    return {
        "page_assembly": _adapt_page_assembly(fixtures, page_rows=page_rows),
        "content_blocks": _adapt_content_blocks(fixtures, topic_ids=topic_ids),
        "block_fields": _adapt_block_fields(fixtures, topic_ids=topic_ids),
        "asset_registry": _adapt_asset_registry(fixtures, topic_ids=topic_ids),
        "block_rules": _adapt_block_rules(fixtures, topic_ids=topic_ids),
    }


def _ensure_safe_output_dir(output_dir: Path, *, repo_root: Path = ROOT) -> None:
    resolved = output_dir.resolve()
    for relative_dir in FORBIDDEN_OUTPUT_DIRS:
        forbidden = (repo_root / relative_dir).resolve()
        try:
            resolved.relative_to(forbidden)
        except ValueError:
            continue
        raise RuntimeError(f"topic map adapter output must not write under {relative_dir}")


def write_content_assembly_fixtures(
    tables: dict[str, tuple[dict[str, str], ...]],
    *,
    output_dir: Path,
    repo_root: Path = ROOT,
) -> None:
    _ensure_safe_output_dir(output_dir, repo_root=repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name in CONTENT_ASSEMBLY_TABLE_ORDER:
        path = output_dir / f"{table_name}.csv"
        headers = CONTENT_ASSEMBLY_TABLE_HEADERS[table_name]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            for row in tables[table_name]:
                writer.writerow({header: row.get(header, "") for header in headers})


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adapt topic-map fixture tables into content-assembly fixture tables.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    export_parser = subparsers.add_parser(
        "export-content-assembly",
        help="Export content-assembly CSV tables from topic-map fixtures.",
    )
    export_parser.add_argument("--fixtures", required=True, help="Directory containing topic-map CSV fixtures.")
    export_parser.add_argument("--output", required=True, help="Output directory for content-assembly CSVs.")
    export_parser.add_argument("--page-id", help="Optional page_id filter.")
    export_parser.add_argument("--product-family", help="Optional product_family filter.")
    args = parser.parse_args(argv)

    fixtures_dir = _resolve_path(args.fixtures)
    output_dir = _resolve_path(args.output)
    try:
        tables = adapt_topic_map_to_content_assembly(
            fixtures_dir=fixtures_dir,
            page_id=args.page_id,
            product_family=args.product_family,
        )
        write_content_assembly_fixtures(tables, output_dir=output_dir)
    except RuntimeError as exc:
        print(f"[topic-map-adapter] ERROR {exc}", file=sys.stderr)
        return 1

    print(f"[topic-map-adapter] wrote {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
