#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.content_assembly_contract import ALLOWED_BLOCK_TYPES  # noqa: E402


TOPIC_MAP_TABLE_HEADERS: dict[str, tuple[str, ...]] = {
    "topic_registry": (
        "topic_id",
        "topic_type",
        "topic_title",
        "template_path",
        "repeatable",
        "owner",
        "status",
        "description",
    ),
    "topic_fields": (
        "field_binding_id",
        "topic_id",
        "field_key",
        "source_table",
        "row_key",
        "page_scope",
        "usage_type",
        "placement_key",
        "value_role",
        "variant_key",
        "data_type",
        "required",
        "fallback_policy",
        "default_value",
    ),
    "topic_assets": (
        "asset_binding_id",
        "topic_id",
        "asset_key",
        "asset_path",
        "alt_key",
        "required",
        "region",
        "lang",
        "status",
    ),
    "topic_rules": (
        "rule_id",
        "topic_id",
        "page_id",
        "condition_key",
        "operator",
        "condition_value",
        "action",
        "priority",
        "enabled",
    ),
    "page_topic_map": (
        "page_topic_id",
        "page_id",
        "topic_id",
        "topic_order",
        "slot_key",
        "product_family",
        "region",
        "lang",
        "fallback_lang",
        "enabled",
        "rule_set",
    ),
    "manual_page_map": (
        "manual_page_id",
        "manual_id",
        "product_family",
        "model",
        "region",
        "lang",
        "page_id",
        "page_order",
        "page_source_type",
        "enabled",
    ),
    "topic_content": (
        "content_id",
        "topic_id",
        "content_key",
        "region",
        "lang",
        "content_rst",
        "fallback_lang",
        "status",
    ),
}

PRIMARY_FIELDS: dict[str, str] = {
    "topic_registry": "topic_id",
    "topic_fields": "field_binding_id",
    "topic_assets": "asset_binding_id",
    "topic_rules": "rule_id",
    "page_topic_map": "page_topic_id",
    "manual_page_map": "manual_page_id",
    "topic_content": "content_id",
}

REQUIRED_VALUE_FIELDS: dict[str, tuple[str, ...]] = {
    "topic_registry": ("topic_id", "topic_type", "topic_title", "template_path", "status"),
    "topic_fields": ("field_binding_id", "topic_id", "field_key", "source_table", "row_key", "value_role"),
    "topic_assets": ("asset_binding_id", "topic_id", "asset_key", "asset_path", "status"),
    "topic_rules": ("rule_id", "topic_id", "page_id", "condition_key", "operator", "condition_value", "action"),
    "page_topic_map": (
        "page_topic_id",
        "page_id",
        "topic_id",
        "topic_order",
        "product_family",
        "region",
        "lang",
        "enabled",
    ),
    "manual_page_map": (
        "manual_page_id",
        "manual_id",
        "product_family",
        "model",
        "region",
        "lang",
        "page_id",
        "page_order",
        "page_source_type",
        "enabled",
    ),
    "topic_content": ("content_id", "topic_id", "content_key", "lang", "content_rst", "status"),
}

TOPIC_STATUSES = {"draft", "active", "deprecated"}
CONTENT_STATUSES = {"draft", "active", "deprecated"}
SOURCE_TABLES = {"Spec_Master", "Topic_Content", "Variable_Defaults", "Asset_Registry"}
VALUE_ROLES = {"label", "spec", "body", "title", "alt", "value"}
FALLBACK_POLICIES = {"error", "skip", "fallback", ""}
CONDITION_KEYS = {"region", "lang", "product_family", "model", "build_family"}
OPERATORS = {"equals", "not_equals", "in", "not_in"}
ACTIONS = {"include", "skip", "fallback", "error"}
PAGE_SOURCE_TYPES = {"topic_map", "generated_page", "csv_page", "rst_include", "cover_pdf", "pdf_insert"}
WILDCARD_VALUES = {"", "*", "all", "any"}


@dataclass(frozen=True)
class TopicMapIssue:
    code: str
    message: str
    surface: str = ""
    missing: tuple[str, ...] = ()

    def format(self) -> str:
        if self.surface:
            return f"{self.code}: {self.surface}: {self.message}"
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class TopicMapValidationResult:
    issues: tuple[TopicMapIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class TopicMapFixtures:
    topic_registry: tuple[dict[str, str], ...]
    topic_fields: tuple[dict[str, str], ...]
    topic_assets: tuple[dict[str, str], ...]
    topic_rules: tuple[dict[str, str], ...]
    page_topic_map: tuple[dict[str, str], ...]
    manual_page_map: tuple[dict[str, str], ...]
    topic_content: tuple[dict[str, str], ...]


def _row_value(row: dict[str, str], field_name: str) -> str:
    return str(row.get(field_name, "")).strip()


def _is_truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_wildcard(value: object) -> bool:
    return str(value or "").strip().lower() in WILDCARD_VALUES


def split_multi_value(value: object) -> tuple[str, ...]:
    raw = str(value or "").strip()
    if not raw:
        return ("*",)
    normalized = raw.replace("|", ";").replace(",", ";")
    values = tuple(part.strip() for part in normalized.split(";") if part.strip())
    return values or ("*",)


def _resolve_path(path: str | Path, *, root: Path = ROOT) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def _csv_headers(path: Path) -> set[str]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except OSError as exc:
        raise RuntimeError(f"{path} cannot be read: {exc}") from exc
    return {str(item).strip() for item in header if str(item).strip()}


def _read_fixture_rows(fixtures_dir: Path, table_name: str) -> tuple[dict[str, str], ...]:
    path = fixtures_dir / f"{table_name}.csv"
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = [
                {str(key).strip(): str(value or "").strip() for key, value in row.items() if key is not None}
                for row in csv.DictReader(handle)
            ]
    except OSError as exc:
        raise RuntimeError(f"{path} cannot be read: {exc}") from exc
    return tuple(rows)


def _fixture_table(fixtures: TopicMapFixtures, table_name: str) -> tuple[dict[str, str], ...]:
    return getattr(fixtures, table_name)


def inspect_topic_map_fixture_schema(fixtures_dir: Path) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    for table_name, required_headers in TOPIC_MAP_TABLE_HEADERS.items():
        path = fixtures_dir / f"{table_name}.csv"
        if not path.exists():
            issues.append(
                TopicMapIssue(
                    "topic_map.table_missing",
                    f"required topic-map table is missing: {path}",
                    surface=table_name,
                    missing=(path.name,),
                )
            )
            continue
        actual_headers = _csv_headers(path)
        missing_headers = tuple(sorted(set(required_headers) - actual_headers))
        if missing_headers:
            issues.append(
                TopicMapIssue(
                    "topic_map.header_missing",
                    "topic-map table is missing required header(s): " + ", ".join(missing_headers),
                    surface=table_name,
                    missing=missing_headers,
                )
            )
    return issues


def load_topic_map_fixtures(fixtures_dir: Path) -> TopicMapFixtures:
    schema_issues = inspect_topic_map_fixture_schema(fixtures_dir)
    if schema_issues:
        raise RuntimeError(render_topic_map_report(TopicMapValidationResult(tuple(schema_issues))))

    return TopicMapFixtures(
        topic_registry=_read_fixture_rows(fixtures_dir, "topic_registry"),
        topic_fields=_read_fixture_rows(fixtures_dir, "topic_fields"),
        topic_assets=_read_fixture_rows(fixtures_dir, "topic_assets"),
        topic_rules=_read_fixture_rows(fixtures_dir, "topic_rules"),
        page_topic_map=_read_fixture_rows(fixtures_dir, "page_topic_map"),
        manual_page_map=_read_fixture_rows(fixtures_dir, "manual_page_map"),
        topic_content=_read_fixture_rows(fixtures_dir, "topic_content"),
    )


def _validate_required_values(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    for table_name, required_fields in REQUIRED_VALUE_FIELDS.items():
        for idx, row in enumerate(_fixture_table(fixtures, table_name), start=2):
            missing = tuple(field for field in required_fields if not _row_value(row, field))
            if missing:
                issues.append(
                    TopicMapIssue(
                        "topic_map.value_missing",
                        "row is missing required value(s): " + ", ".join(missing),
                        surface=f"{table_name}:{idx}",
                        missing=missing,
                    )
                )
    return issues


def _validate_unique_primary_keys(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    for table_name, primary_field in PRIMARY_FIELDS.items():
        seen: set[str] = set()
        duplicates: set[str] = set()
        for row in _fixture_table(fixtures, table_name):
            value = _row_value(row, primary_field)
            if not value:
                continue
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        if duplicates:
            issues.append(
                TopicMapIssue(
                    "topic_map.duplicate_primary",
                    "duplicate primary value(s): " + ", ".join(sorted(duplicates)),
                    surface=f"{table_name}.{primary_field}",
                    missing=tuple(sorted(duplicates)),
                )
            )
    return issues


def _registry_by_id(fixtures: TopicMapFixtures) -> dict[str, dict[str, str]]:
    return {_row_value(row, "topic_id"): row for row in fixtures.topic_registry if _row_value(row, "topic_id")}


def _rule_ids(fixtures: TopicMapFixtures) -> set[str]:
    return {_row_value(row, "rule_id") for row in fixtures.topic_rules if _row_value(row, "rule_id")}


def _validate_topic_registry(
    fixtures: TopicMapFixtures,
    *,
    repo_root: Path,
) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    for row in fixtures.topic_registry:
        topic_id = _row_value(row, "topic_id")
        topic_type = _row_value(row, "topic_type")
        status = _row_value(row, "status").lower()
        if topic_type not in ALLOWED_BLOCK_TYPES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_topic_type",
                    f"topic uses unknown type: {topic_type}",
                    surface=f"topic_registry.topic_type:{topic_id}",
                    missing=(topic_type,),
                )
            )
        if status and status not in TOPIC_STATUSES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_status",
                    f"topic uses unknown status: {status}",
                    surface=f"topic_registry.status:{topic_id}",
                    missing=(status,),
                )
            )
        template_path = _row_value(row, "template_path")
        if status == "active" and template_path and not _resolve_path(template_path, root=repo_root).exists():
            issues.append(
                TopicMapIssue(
                    "topic_map.template_missing",
                    f"template path does not exist: {template_path}",
                    surface=f"topic_registry.template_path:{topic_id}",
                    missing=(template_path,),
                )
            )
    return issues


def _validate_topic_references(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    registry = _registry_by_id(fixtures)
    reference_surfaces = (
        ("topic_fields", "field_binding_id"),
        ("topic_assets", "asset_binding_id"),
        ("topic_rules", "rule_id"),
        ("page_topic_map", "page_topic_id"),
        ("topic_content", "content_id"),
    )
    for table_name, primary_field in reference_surfaces:
        missing: list[str] = []
        for row in _fixture_table(fixtures, table_name):
            topic_id = _row_value(row, "topic_id")
            if topic_id and topic_id not in registry:
                missing.append(_row_value(row, primary_field) or topic_id)
        if missing:
            issues.append(
                TopicMapIssue(
                    "topic_map.topic_ref_missing",
                    "row(s) reference missing topic_id: " + ", ".join(missing),
                    surface=f"{table_name}.topic_id",
                    missing=tuple(missing),
                )
            )
    return issues


def _validate_field_rows(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    for row in fixtures.topic_fields:
        binding_id = _row_value(row, "field_binding_id")
        source_table = _row_value(row, "source_table")
        value_role = _row_value(row, "value_role")
        fallback_policy = _row_value(row, "fallback_policy").lower()
        if source_table and source_table not in SOURCE_TABLES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_source_table",
                    f"unknown source_table: {source_table}",
                    surface=f"topic_fields.source_table:{binding_id}",
                    missing=(source_table,),
                )
            )
        if value_role and value_role not in VALUE_ROLES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_value_role",
                    f"unknown value_role: {value_role}",
                    surface=f"topic_fields.value_role:{binding_id}",
                    missing=(value_role,),
                )
            )
        if fallback_policy not in FALLBACK_POLICIES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_fallback_policy",
                    f"unknown fallback_policy: {fallback_policy}",
                    surface=f"topic_fields.fallback_policy:{binding_id}",
                    missing=(fallback_policy,),
                )
            )
    return issues


def _validate_asset_rows(fixtures: TopicMapFixtures, *, repo_root: Path) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    asset_keys: set[str] = set()
    duplicate_asset_keys: set[str] = set()
    for row in fixtures.topic_assets:
        asset_key = _row_value(row, "asset_key")
        if asset_key in asset_keys:
            duplicate_asset_keys.add(asset_key)
        asset_keys.add(asset_key)
        status = _row_value(row, "status").lower()
        if status and status not in CONTENT_STATUSES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_status",
                    f"asset uses unknown status: {status}",
                    surface=f"topic_assets.status:{asset_key}",
                    missing=(status,),
                )
            )
        asset_path = _row_value(row, "asset_path")
        if status == "active" and asset_path and not _resolve_path(asset_path, root=repo_root).exists():
            issues.append(
                TopicMapIssue(
                    "topic_map.asset_missing",
                    f"asset path does not exist: {asset_path}",
                    surface=f"topic_assets.asset_path:{asset_key}",
                    missing=(asset_path,),
                )
            )
    if duplicate_asset_keys:
        issues.append(
            TopicMapIssue(
                "topic_map.duplicate_asset_key",
                "asset_key values must be unique for the first adapter: " + ", ".join(sorted(duplicate_asset_keys)),
                surface="topic_assets.asset_key",
                missing=tuple(sorted(duplicate_asset_keys)),
            )
        )
    return issues


def _validate_rule_rows(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    for row in fixtures.topic_rules:
        rule_id = _row_value(row, "rule_id")
        condition_key = _row_value(row, "condition_key")
        operator = _row_value(row, "operator")
        action = _row_value(row, "action")
        priority = _row_value(row, "priority")
        if condition_key and condition_key not in CONDITION_KEYS:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_condition_key",
                    f"unknown condition_key: {condition_key}",
                    surface=f"topic_rules.condition_key:{rule_id}",
                    missing=(condition_key,),
                )
            )
        if operator and operator not in OPERATORS:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_operator",
                    f"unknown operator: {operator}",
                    surface=f"topic_rules.operator:{rule_id}",
                    missing=(operator,),
                )
            )
        if action and action not in ACTIONS:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_action",
                    f"unknown action: {action}",
                    surface=f"topic_rules.action:{rule_id}",
                    missing=(action,),
                )
            )
        if priority:
            try:
                int(priority)
            except ValueError:
                issues.append(
                    TopicMapIssue(
                        "topic_map.priority_invalid",
                        f"priority must be an integer: {priority}",
                        surface=f"topic_rules.priority:{rule_id}",
                        missing=(priority,),
                    )
                )
    return issues


def _iter_rule_refs(value: str) -> Iterable[str]:
    for item in split_multi_value(value):
        if not _is_wildcard(item):
            yield item


def _validate_page_topic_rows(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    registry = _registry_by_id(fixtures)
    rules = _rule_ids(fixtures)
    for row in fixtures.page_topic_map:
        page_topic_id = _row_value(row, "page_topic_id")
        topic_id = _row_value(row, "topic_id")
        topic = registry.get(topic_id)
        if topic and _is_truthy(row.get("enabled", "")) and _row_value(topic, "status").lower() != "active":
            issues.append(
                TopicMapIssue(
                    "topic_map.inactive_topic_used",
                    f"enabled page topic references non-active topic: {topic_id}",
                    surface=f"page_topic_map.topic_id:{page_topic_id}",
                    missing=(topic_id,),
                )
            )
        try:
            int(_row_value(row, "topic_order"))
        except ValueError:
            issues.append(
                TopicMapIssue(
                    "topic_map.order_invalid",
                    f"topic_order must be an integer: {_row_value(row, 'topic_order')}",
                    surface=f"page_topic_map.topic_order:{page_topic_id}",
                    missing=(_row_value(row, "topic_order"),),
                )
            )
        langs = split_multi_value(_row_value(row, "lang"))
        if _is_truthy(row.get("enabled", "")) and any(not _is_wildcard(lang) for lang in langs):
            if not _row_value(row, "fallback_lang"):
                issues.append(
                    TopicMapIssue(
                        "topic_map.fallback_missing",
                        "enabled page-topic rows with explicit lang must declare fallback_lang",
                        surface=f"page_topic_map.fallback_lang:{page_topic_id}",
                    )
                )
        missing_rule_refs = tuple(rule_id for rule_id in _iter_rule_refs(_row_value(row, "rule_set")) if rule_id not in rules)
        if missing_rule_refs:
            issues.append(
                TopicMapIssue(
                    "topic_map.rule_ref_missing",
                    "page topic references missing rule(s): " + ", ".join(missing_rule_refs),
                    surface=f"page_topic_map.rule_set:{page_topic_id}",
                    missing=missing_rule_refs,
                )
            )
    return issues


def _validate_manual_page_rows(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    page_ids = {_row_value(row, "page_id") for row in fixtures.page_topic_map if _row_value(row, "page_id")}
    for row in fixtures.manual_page_map:
        manual_page_id = _row_value(row, "manual_page_id")
        source_type = _row_value(row, "page_source_type")
        if source_type and source_type not in PAGE_SOURCE_TYPES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_page_source_type",
                    f"unknown page_source_type: {source_type}",
                    surface=f"manual_page_map.page_source_type:{manual_page_id}",
                    missing=(source_type,),
                )
            )
        if source_type == "topic_map" and _row_value(row, "page_id") not in page_ids:
            issues.append(
                TopicMapIssue(
                    "topic_map.page_ref_missing",
                    f"manual page references missing page topic map: {_row_value(row, 'page_id')}",
                    surface=f"manual_page_map.page_id:{manual_page_id}",
                    missing=(_row_value(row, "page_id"),),
                )
            )
        try:
            int(_row_value(row, "page_order"))
        except ValueError:
            issues.append(
                TopicMapIssue(
                    "topic_map.order_invalid",
                    f"page_order must be an integer: {_row_value(row, 'page_order')}",
                    surface=f"manual_page_map.page_order:{manual_page_id}",
                    missing=(_row_value(row, "page_order"),),
                )
            )
    return issues


def _validate_topic_content_rows(fixtures: TopicMapFixtures) -> list[TopicMapIssue]:
    issues: list[TopicMapIssue] = []
    for row in fixtures.topic_content:
        content_id = _row_value(row, "content_id")
        status = _row_value(row, "status").lower()
        if status and status not in CONTENT_STATUSES:
            issues.append(
                TopicMapIssue(
                    "topic_map.unknown_status",
                    f"topic content uses unknown status: {status}",
                    surface=f"topic_content.status:{content_id}",
                    missing=(status,),
                )
            )
        lang = _row_value(row, "lang")
        if not _is_wildcard(lang) and _row_value(row, "fallback_lang") == "" and lang.lower() != "en":
            issues.append(
                TopicMapIssue(
                    "topic_map.fallback_missing",
                    "localized topic content must declare fallback_lang",
                    surface=f"topic_content.fallback_lang:{content_id}",
                )
            )
    return issues


def validate_topic_map_fixtures(
    *,
    fixtures_dir: Path,
    repo_root: Path = ROOT,
) -> TopicMapValidationResult:
    issues = inspect_topic_map_fixture_schema(fixtures_dir)
    if issues:
        return TopicMapValidationResult(tuple(issues))

    try:
        fixtures = load_topic_map_fixtures(fixtures_dir)
    except RuntimeError as exc:
        return TopicMapValidationResult((TopicMapIssue("topic_map.invalid", str(exc)),))

    issues.extend(_validate_required_values(fixtures))
    issues.extend(_validate_unique_primary_keys(fixtures))
    issues.extend(_validate_topic_registry(fixtures, repo_root=repo_root))
    issues.extend(_validate_topic_references(fixtures))
    issues.extend(_validate_field_rows(fixtures))
    issues.extend(_validate_asset_rows(fixtures, repo_root=repo_root))
    issues.extend(_validate_rule_rows(fixtures))
    issues.extend(_validate_page_topic_rows(fixtures))
    issues.extend(_validate_manual_page_rows(fixtures))
    issues.extend(_validate_topic_content_rows(fixtures))

    return TopicMapValidationResult(tuple(issues))


def render_topic_map_report(result: TopicMapValidationResult) -> str:
    if result.valid:
        return "[topic-map-contract] OK"
    return "\n".join(f"[topic-map-contract] ERROR {issue.format()}" for issue in result.issues)


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate fixture-backed topic-map tables.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="Validate topic-map fixture tables.")
    validate_parser.add_argument("--fixtures", required=True, help="Directory containing topic-map CSV fixtures.")
    args = parser.parse_args(argv)

    fixtures_dir = _resolve_path(args.fixtures)
    result = validate_topic_map_fixtures(fixtures_dir=fixtures_dir)
    print(render_topic_map_report(result), file=sys.stderr if not result.valid else sys.stdout)
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(run())
