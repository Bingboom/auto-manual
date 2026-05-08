#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)


SPEC_TOPIC_TABLE_HEADERS: dict[str, tuple[str, ...]] = {
    "spec_topics": (
        "topic_id",
        "topic_type",
        "page",
        "section",
        "section_order",
        "product_family",
        "status",
        "description",
    ),
    "spec_topic_rows": (
        "topic_row_id",
        "topic_id",
        "row_key",
        "row_order",
        "slot_key",
        "line_order",
        "usage_type",
        "placement_key",
        "value_role",
        "variant_key",
        "required",
    ),
    "spec_topic_values": (
        "topic_value_id",
        "topic_row_id",
        "document_key",
        "model",
        "region",
        "is_latest",
        "source_lang",
        "row_label_source",
        "row_label_footnote_refs",
        "param_source",
        "param_footnote_refs",
        "value_source",
        "value_footnote_refs",
        "row_label_fr",
        "param_fr",
        "value_fr",
        "row_label_es",
        "param_es",
        "value_es",
    ),
}

PRIMARY_FIELDS: dict[str, str] = {
    "spec_topics": "topic_id",
    "spec_topic_rows": "topic_row_id",
    "spec_topic_values": "topic_value_id",
}

REQUIRED_VALUE_FIELDS: dict[str, tuple[str, ...]] = {
    "spec_topics": ("topic_id", "topic_type", "page", "section", "section_order", "status"),
    "spec_topic_rows": ("topic_row_id", "topic_id", "row_key", "row_order", "line_order", "required"),
    "spec_topic_values": ("topic_value_id", "topic_row_id", "document_key", "model", "region", "source_lang"),
}

TOPIC_TYPES = {"identity", "spec_section", "page_value_group"}
STATUSES = {"draft", "active", "deprecated"}
USAGE_TYPES = {"spec_value", "page_value", ""}
VALUE_ROLES = {"value", "label", "spec", "body", "title", "alt", ""}


@dataclass(frozen=True)
class SpecTopicIssue:
    code: str
    message: str
    surface: str = ""
    missing: tuple[str, ...] = ()

    def format(self) -> str:
        if self.surface:
            return f"{self.code}: {self.surface}: {self.message}"
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class SpecTopicValidationResult:
    issues: tuple[SpecTopicIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class SpecTopicFixtures:
    spec_topics: tuple[dict[str, str], ...]
    spec_topic_rows: tuple[dict[str, str], ...]
    spec_topic_values: tuple[dict[str, str], ...]


def _row_value(row: dict[str, str], field_name: str) -> str:
    return str(row.get(field_name, "")).strip()


def _is_truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


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


def _fixture_table(fixtures: SpecTopicFixtures, table_name: str) -> tuple[dict[str, str], ...]:
    return getattr(fixtures, table_name)


def inspect_spec_topic_fixture_schema(fixtures_dir: Path) -> list[SpecTopicIssue]:
    issues: list[SpecTopicIssue] = []
    for table_name, required_headers in SPEC_TOPIC_TABLE_HEADERS.items():
        path = fixtures_dir / f"{table_name}.csv"
        if not path.exists():
            issues.append(
                SpecTopicIssue(
                    "spec_topic.table_missing",
                    f"required spec-topic table is missing: {path}",
                    surface=table_name,
                    missing=(path.name,),
                )
            )
            continue
        actual_headers = _csv_headers(path)
        missing_headers = tuple(sorted(set(required_headers) - actual_headers))
        if missing_headers:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.header_missing",
                    "spec-topic table is missing required header(s): " + ", ".join(missing_headers),
                    surface=table_name,
                    missing=missing_headers,
                )
            )
    return issues


def load_spec_topic_fixtures(fixtures_dir: Path) -> SpecTopicFixtures:
    schema_issues = inspect_spec_topic_fixture_schema(fixtures_dir)
    if schema_issues:
        raise RuntimeError(render_spec_topic_report(SpecTopicValidationResult(tuple(schema_issues))))
    return SpecTopicFixtures(
        spec_topics=_read_fixture_rows(fixtures_dir, "spec_topics"),
        spec_topic_rows=_read_fixture_rows(fixtures_dir, "spec_topic_rows"),
        spec_topic_values=_read_fixture_rows(fixtures_dir, "spec_topic_values"),
    )


def _validate_required_values(fixtures: SpecTopicFixtures) -> list[SpecTopicIssue]:
    issues: list[SpecTopicIssue] = []
    for table_name, required_fields in REQUIRED_VALUE_FIELDS.items():
        for idx, row in enumerate(_fixture_table(fixtures, table_name), start=2):
            missing = tuple(field for field in required_fields if not _row_value(row, field))
            if missing:
                issues.append(
                    SpecTopicIssue(
                        "spec_topic.value_missing",
                        "row is missing required value(s): " + ", ".join(missing),
                        surface=f"{table_name}:{idx}",
                        missing=missing,
                    )
                )
    return issues


def _validate_unique_primary_keys(fixtures: SpecTopicFixtures) -> list[SpecTopicIssue]:
    issues: list[SpecTopicIssue] = []
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
                SpecTopicIssue(
                    "spec_topic.duplicate_primary",
                    "duplicate primary value(s): " + ", ".join(sorted(duplicates)),
                    surface=f"{table_name}.{primary_field}",
                    missing=tuple(sorted(duplicates)),
                )
            )
    return issues


def _topics_by_id(fixtures: SpecTopicFixtures) -> dict[str, dict[str, str]]:
    return {_row_value(row, "topic_id"): row for row in fixtures.spec_topics if _row_value(row, "topic_id")}


def _rows_by_id(fixtures: SpecTopicFixtures) -> dict[str, dict[str, str]]:
    return {_row_value(row, "topic_row_id"): row for row in fixtures.spec_topic_rows if _row_value(row, "topic_row_id")}


def _validate_topic_rows(fixtures: SpecTopicFixtures) -> list[SpecTopicIssue]:
    issues: list[SpecTopicIssue] = []
    for row in fixtures.spec_topics:
        topic_id = _row_value(row, "topic_id")
        topic_type = _row_value(row, "topic_type")
        status = _row_value(row, "status").lower()
        if topic_type not in TOPIC_TYPES:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.unknown_topic_type",
                    f"topic uses unknown type: {topic_type}",
                    surface=f"spec_topics.topic_type:{topic_id}",
                    missing=(topic_type,),
                )
            )
        if status not in STATUSES:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.unknown_status",
                    f"topic uses unknown status: {status}",
                    surface=f"spec_topics.status:{topic_id}",
                    missing=(status,),
                )
            )
        try:
            int(_row_value(row, "section_order"))
        except ValueError:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.order_invalid",
                    f"section_order must be an integer: {_row_value(row, 'section_order')}",
                    surface=f"spec_topics.section_order:{topic_id}",
                )
            )
    return issues


def _validate_spec_row_refs(fixtures: SpecTopicFixtures) -> list[SpecTopicIssue]:
    issues: list[SpecTopicIssue] = []
    topics = _topics_by_id(fixtures)
    rows_with_values = {_row_value(row, "topic_row_id") for row in fixtures.spec_topic_values}
    for row in fixtures.spec_topic_rows:
        topic_row_id = _row_value(row, "topic_row_id")
        topic_id = _row_value(row, "topic_id")
        if topic_id and topic_id not in topics:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.topic_ref_missing",
                    f"topic row references missing topic_id: {topic_id}",
                    surface=f"spec_topic_rows.topic_id:{topic_row_id}",
                    missing=(topic_id,),
                )
            )
        usage_type = _row_value(row, "usage_type")
        value_role = _row_value(row, "value_role")
        if usage_type not in USAGE_TYPES:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.unknown_usage_type",
                    f"unknown usage_type: {usage_type}",
                    surface=f"spec_topic_rows.usage_type:{topic_row_id}",
                    missing=(usage_type,),
                )
            )
        if value_role not in VALUE_ROLES:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.unknown_value_role",
                    f"unknown value_role: {value_role}",
                    surface=f"spec_topic_rows.value_role:{topic_row_id}",
                    missing=(value_role,),
                )
            )
        for order_field in ("row_order", "line_order"):
            try:
                int(_row_value(row, order_field))
            except ValueError:
                issues.append(
                    SpecTopicIssue(
                        "spec_topic.order_invalid",
                        f"{order_field} must be an integer: {_row_value(row, order_field)}",
                        surface=f"spec_topic_rows.{order_field}:{topic_row_id}",
                    )
                )
        if _is_truthy(row.get("required", "")) and topic_row_id not in rows_with_values:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.required_row_value_missing",
                    "required topic row has no value rows",
                    surface=f"spec_topic_rows.required:{topic_row_id}",
                    missing=(topic_row_id,),
                )
            )
    return issues


def _validate_value_refs(fixtures: SpecTopicFixtures) -> list[SpecTopicIssue]:
    issues: list[SpecTopicIssue] = []
    rows = _rows_by_id(fixtures)
    topics = _topics_by_id(fixtures)
    selectors: dict[tuple[str, ...], str] = {}
    for value_row in fixtures.spec_topic_values:
        topic_value_id = _row_value(value_row, "topic_value_id")
        topic_row_id = _row_value(value_row, "topic_row_id")
        spec_row = rows.get(topic_row_id)
        if spec_row is None:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.row_ref_missing",
                    f"value row references missing topic_row_id: {topic_row_id}",
                    surface=f"spec_topic_values.topic_row_id:{topic_value_id}",
                    missing=(topic_row_id,),
                )
            )
            continue
        topic = topics.get(_row_value(spec_row, "topic_id"), {})
        selector = (
            _row_value(value_row, "document_key"),
            _row_value(value_row, "model"),
            _row_value(value_row, "region"),
            _row_value(topic, "page"),
            _row_value(spec_row, "row_key"),
            _row_value(spec_row, "slot_key"),
            _row_value(spec_row, "line_order"),
        )
        previous = selectors.get(selector)
        if previous is not None:
            issues.append(
                SpecTopicIssue(
                    "spec_topic.duplicate_selector",
                    f"value row duplicates selector already used by {previous}",
                    surface=f"spec_topic_values:{topic_value_id}",
                    missing=(topic_value_id,),
                )
            )
        selectors[selector] = topic_value_id
        if not (_row_value(value_row, "row_label_source") or _row_value(value_row, "value_source")):
            issues.append(
                SpecTopicIssue(
                    "spec_topic.empty_display_value",
                    "value row should provide row_label_source or value_source",
                    surface=f"spec_topic_values:{topic_value_id}",
                    missing=(topic_value_id,),
                )
            )
    return issues


def validate_spec_topic_fixtures(*, fixtures_dir: Path) -> SpecTopicValidationResult:
    issues = inspect_spec_topic_fixture_schema(fixtures_dir)
    if issues:
        return SpecTopicValidationResult(tuple(issues))

    try:
        fixtures = load_spec_topic_fixtures(fixtures_dir)
    except RuntimeError as exc:
        return SpecTopicValidationResult((SpecTopicIssue("spec_topic.invalid", str(exc)),))

    issues.extend(_validate_required_values(fixtures))
    issues.extend(_validate_unique_primary_keys(fixtures))
    issues.extend(_validate_topic_rows(fixtures))
    issues.extend(_validate_spec_row_refs(fixtures))
    issues.extend(_validate_value_refs(fixtures))
    return SpecTopicValidationResult(tuple(issues))


def render_spec_topic_report(result: SpecTopicValidationResult) -> str:
    if result.valid:
        return "[spec-topic-contract] OK"
    return "\n".join(f"[spec-topic-contract] ERROR {issue.format()}" for issue in result.issues)


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate fixture-backed spec-topic tables.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="Validate spec-topic fixture tables.")
    validate_parser.add_argument("--fixtures", required=True, help="Directory containing spec-topic CSV fixtures.")
    args = parser.parse_args(argv)

    result = validate_spec_topic_fixtures(fixtures_dir=_resolve_path(args.fixtures))
    print(render_spec_topic_report(result), file=sys.stderr if not result.valid else sys.stdout)
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(run())
