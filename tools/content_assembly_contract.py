#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)


ALLOWED_BLOCK_TYPES: tuple[str, ...] = (
    "product_identity",
    "feature_overview",
    "spec_summary",
    "asset_callout",
    "warning_notice",
    "operation_steps",
    "app_instruction",
    "maintenance_block",
    "troubleshooting_case",
)

CONTENT_ASSEMBLY_TABLE_HEADERS: dict[str, tuple[str, ...]] = {
    "page_assembly": (
        "page_id",
        "product_family",
        "region",
        "lang",
        "block_id",
        "block_type",
        "order",
        "enabled",
        "fallback_lang",
    ),
    "content_blocks": (
        "block_id",
        "block_type",
        "parent_block_id",
        "title_key",
        "asset_key",
        "repeatable",
        "region",
        "lang",
    ),
    "block_fields": (
        "block_id",
        "field_key",
        "row_key",
        "value_role",
        "placement_key",
        "variant_key",
        "required",
        "fallback_policy",
    ),
    "asset_registry": (
        "asset_key",
        "path",
        "alt_key",
        "region",
        "lang",
        "required",
    ),
    "block_rules": (
        "block_id",
        "condition_key",
        "operator",
        "condition_value",
        "action",
    ),
}

WILDCARD_VALUES = {"", "*", "all", "any"}


@dataclass(frozen=True)
class ContentAssemblyIssue:
    code: str
    message: str
    surface: str = ""
    missing: tuple[str, ...] = ()

    def format(self) -> str:
        if self.surface:
            return f"{self.code}: {self.surface}: {self.message}"
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class ContentAssemblyValidationResult:
    issues: tuple[ContentAssemblyIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class AssemblyContract:
    page_id: str
    product_family: str
    regions: tuple[str, ...]
    langs: tuple[str, ...]
    fallback_lang: str | None
    blocks: tuple[str, ...]
    required_fields: tuple[str, ...]


@dataclass(frozen=True)
class ContentAssemblyFixtures:
    page_assembly: tuple[dict[str, str], ...]
    content_blocks: tuple[dict[str, str], ...]
    block_fields: tuple[dict[str, str], ...]
    asset_registry: tuple[dict[str, str], ...]
    block_rules: tuple[dict[str, str], ...]


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed. Please run: pip install pyyaml") from exc

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise RuntimeError(f"{path} cannot be read: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} root must be a mapping")
    return data


def _string_list(raw: object, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise RuntimeError(f"{field_name} must be a list")
    values = tuple(str(item).strip() for item in raw if str(item).strip())
    if not values:
        raise RuntimeError(f"{field_name} must contain at least one value")
    return values


def _lower_string_list(raw: object, *, field_name: str) -> tuple[str, ...]:
    return tuple(item.lower() for item in _string_list(raw, field_name=field_name))


def _resolve_path(path: str | Path, *, root: Path = ROOT) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def _is_wildcard(value: object) -> bool:
    return str(value or "").strip().lower() in WILDCARD_VALUES


def _is_truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _row_value(row: dict[str, str], field_name: str) -> str:
    return str(row.get(field_name, "")).strip()


def row_applies(row: dict[str, str], *, region: str | None = None, lang: str | None = None) -> bool:
    row_region = _row_value(row, "region")
    row_lang = _row_value(row, "lang")
    if region is not None and not _is_wildcard(row_region) and row_region != region:
        return False
    if lang is not None and not _is_wildcard(row_lang) and row_lang.lower() != lang.lower():
        return False
    return True


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


def inspect_content_assembly_fixture_schema(fixtures_dir: Path) -> list[ContentAssemblyIssue]:
    issues: list[ContentAssemblyIssue] = []
    for table_name, required_headers in CONTENT_ASSEMBLY_TABLE_HEADERS.items():
        path = fixtures_dir / f"{table_name}.csv"
        if not path.exists():
            issues.append(
                ContentAssemblyIssue(
                    "fixture.table_missing",
                    f"required fixture table is missing: {path}",
                    surface=table_name,
                    missing=(path.name,),
                )
            )
            continue
        actual_headers = _csv_headers(path)
        missing_headers = tuple(sorted(set(required_headers) - actual_headers))
        if missing_headers:
            issues.append(
                ContentAssemblyIssue(
                    "fixture.header_missing",
                    "fixture table is missing required header(s): " + ", ".join(missing_headers),
                    surface=table_name,
                    missing=missing_headers,
                )
            )
    return issues


def load_content_assembly_fixtures(fixtures_dir: Path) -> ContentAssemblyFixtures:
    schema_issues = inspect_content_assembly_fixture_schema(fixtures_dir)
    if schema_issues:
        raise RuntimeError(render_content_assembly_report(ContentAssemblyValidationResult(tuple(schema_issues))))

    return ContentAssemblyFixtures(
        page_assembly=_read_fixture_rows(fixtures_dir, "page_assembly"),
        content_blocks=_read_fixture_rows(fixtures_dir, "content_blocks"),
        block_fields=_read_fixture_rows(fixtures_dir, "block_fields"),
        asset_registry=_read_fixture_rows(fixtures_dir, "asset_registry"),
        block_rules=_read_fixture_rows(fixtures_dir, "block_rules"),
    )


def load_assembly_contract(contract_path: Path) -> AssemblyContract:
    data = _load_yaml(contract_path)

    page_id = str(data.get("page_id", "")).strip()
    if not page_id:
        raise RuntimeError(f"page_id is required in assembly contract: {contract_path}")
    product_family = str(data.get("product_family", "")).strip()
    if not product_family:
        raise RuntimeError(f"product_family is required in assembly contract: {contract_path}")

    fallback_raw = data.get("fallback", {})
    if fallback_raw is None:
        fallback_raw = {}
    if not isinstance(fallback_raw, dict):
        raise RuntimeError(f"fallback must be a mapping in assembly contract: {contract_path}")
    fallback_lang = str(fallback_raw.get("lang", "")).strip().lower() or None

    return AssemblyContract(
        page_id=page_id,
        product_family=product_family,
        regions=_string_list(data.get("regions"), field_name="regions"),
        langs=_lower_string_list(data.get("langs"), field_name="langs"),
        fallback_lang=fallback_lang,
        blocks=_lower_string_list(data.get("blocks"), field_name="blocks"),
        required_fields=_string_list(data.get("required_fields"), field_name="required_fields"),
    )


def _recipe_row_keys(repo_root: Path, page_id: str) -> set[str]:
    recipe_root = repo_root / "docs" / "templates" / "recipes"
    if not recipe_root.exists():
        return set()

    row_keys: set[str] = set()
    for recipe_path in recipe_root.glob(f"**/{page_id}.yaml"):
        data = _load_yaml(recipe_path)
        required_raw = data.get("required_row_keys", [])
        if isinstance(required_raw, list):
            row_keys.update(str(item).strip() for item in required_raw if str(item).strip())
        field_map_raw = data.get("field_map", {})
        if isinstance(field_map_raw, dict):
            for selector in field_map_raw.values():
                if isinstance(selector, dict):
                    row_key = str(selector.get("row_key", "")).strip()
                    if row_key:
                        row_keys.add(row_key)
    return row_keys


def _page_rows(fixtures: ContentAssemblyFixtures, contract: AssemblyContract) -> tuple[dict[str, str], ...]:
    return tuple(
        row
        for row in fixtures.page_assembly
        if _row_value(row, "page_id") == contract.page_id
        and _row_value(row, "product_family") == contract.product_family
        and _is_truthy(row.get("enabled", ""))
    )


def _block_ids(rows: Iterable[dict[str, str]]) -> set[str]:
    return {_row_value(row, "block_id") for row in rows if _row_value(row, "block_id")}


def _content_rows_for_blocks(
    fixtures: ContentAssemblyFixtures,
    block_ids: set[str],
) -> tuple[dict[str, str], ...]:
    return tuple(row for row in fixtures.content_blocks if _row_value(row, "block_id") in block_ids)


def _fixture_row_keys(fixtures: ContentAssemblyFixtures, block_ids: set[str]) -> set[str]:
    return {
        _row_value(row, "row_key")
        for row in fixtures.block_fields
        if _row_value(row, "block_id") in block_ids and _row_value(row, "row_key")
    }


def _validate_contract_blocks(contract: AssemblyContract) -> list[ContentAssemblyIssue]:
    issues: list[ContentAssemblyIssue] = []
    unknown_blocks = tuple(sorted(set(contract.blocks) - set(ALLOWED_BLOCK_TYPES)))
    if unknown_blocks:
        issues.append(
            ContentAssemblyIssue(
                "contract.unknown_block_type",
                "contract declares unknown block type(s): " + ", ".join(unknown_blocks),
                surface="blocks",
                missing=unknown_blocks,
            )
        )
    return issues


def _validate_fallback(contract: AssemblyContract) -> list[ContentAssemblyIssue]:
    if len(contract.langs) <= 1:
        return []
    if not contract.fallback_lang:
        return [
            ContentAssemblyIssue(
                "contract.fallback_missing",
                "multi-language assembly contracts must declare fallback.lang",
                surface="fallback.lang",
            )
        ]
    if contract.fallback_lang not in contract.langs:
        return [
            ContentAssemblyIssue(
                "contract.fallback_unknown",
                f"fallback.lang is not listed in langs: {contract.fallback_lang}",
                surface="fallback.lang",
                missing=(contract.fallback_lang,),
            )
        ]
    return []


def _validate_page_rows(
    contract: AssemblyContract,
    page_rows: tuple[dict[str, str], ...],
) -> list[ContentAssemblyIssue]:
    issues: list[ContentAssemblyIssue] = []
    if not page_rows:
        return [
            ContentAssemblyIssue(
                "fixture.page_missing",
                f"page_assembly has no enabled rows for {contract.page_id} / {contract.product_family}",
                surface="page_assembly",
                missing=(contract.page_id,),
            )
        ]

    seen_regions = {_row_value(row, "region") for row in page_rows if not _is_wildcard(_row_value(row, "region"))}
    seen_langs = {_row_value(row, "lang").lower() for row in page_rows if not _is_wildcard(_row_value(row, "lang"))}
    missing_regions = tuple(sorted(set(contract.regions) - seen_regions))
    missing_langs = tuple(sorted(set(contract.langs) - seen_langs))
    if missing_regions:
        issues.append(
            ContentAssemblyIssue(
                "fixture.region_missing",
                "page_assembly has no enabled row for region(s): " + ", ".join(missing_regions),
                surface="page_assembly.region",
                missing=missing_regions,
            )
        )
    if missing_langs:
        issues.append(
            ContentAssemblyIssue(
                "fixture.lang_missing",
                "page_assembly has no enabled row for lang(s): " + ", ".join(missing_langs),
                surface="page_assembly.lang",
                missing=missing_langs,
            )
        )

    declared_blocks = set(contract.blocks)
    for row in page_rows:
        block_type = _row_value(row, "block_type").lower()
        if block_type not in ALLOWED_BLOCK_TYPES:
            issues.append(
                ContentAssemblyIssue(
                    "fixture.unknown_block_type",
                    f"page_assembly uses unknown block type: {block_type}",
                    surface="page_assembly.block_type",
                    missing=(block_type,),
                )
            )
        elif block_type not in declared_blocks:
            issues.append(
                ContentAssemblyIssue(
                    "fixture.block_not_declared",
                    f"page_assembly uses block type not declared by contract: {block_type}",
                    surface="page_assembly.block_type",
                    missing=(block_type,),
                )
            )
    return issues


def _validate_content_blocks(
    contract: AssemblyContract,
    page_block_ids: set[str],
    content_rows: tuple[dict[str, str], ...],
) -> list[ContentAssemblyIssue]:
    issues: list[ContentAssemblyIssue] = []
    content_block_ids = _block_ids(content_rows)
    missing_content_blocks = tuple(sorted(page_block_ids - content_block_ids))
    if missing_content_blocks:
        issues.append(
            ContentAssemblyIssue(
                "fixture.content_block_missing",
                "content_blocks is missing block metadata for block(s): " + ", ".join(missing_content_blocks),
                surface="content_blocks.block_id",
                missing=missing_content_blocks,
            )
        )

    for row in content_rows:
        block_type = _row_value(row, "block_type").lower()
        if block_type not in ALLOWED_BLOCK_TYPES:
            issues.append(
                ContentAssemblyIssue(
                    "fixture.unknown_block_type",
                    f"content_blocks uses unknown block type: {block_type}",
                    surface="content_blocks.block_type",
                    missing=(block_type,),
                )
            )
            continue
        if block_type not in contract.blocks:
            issues.append(
                ContentAssemblyIssue(
                    "fixture.block_not_declared",
                    f"content_blocks uses block type not declared by contract: {block_type}",
                    surface="content_blocks.block_type",
                    missing=(block_type,),
                )
            )
    return issues


def _validate_required_fields(
    contract: AssemblyContract,
    fixtures: ContentAssemblyFixtures,
    page_block_ids: set[str],
    repo_root: Path,
) -> list[ContentAssemblyIssue]:
    available = _fixture_row_keys(fixtures, page_block_ids) | _recipe_row_keys(repo_root, contract.page_id)
    missing_fields = tuple(sorted(set(contract.required_fields) - available))
    if not missing_fields:
        return []
    return [
        ContentAssemblyIssue(
            "contract.required_field_missing",
            "required field(s) are not available from fixtures or recipes: " + ", ".join(missing_fields),
            surface="required_fields",
            missing=missing_fields,
        )
    ]


def _validate_assets(
    fixtures: ContentAssemblyFixtures,
    content_rows: tuple[dict[str, str], ...],
    repo_root: Path,
) -> list[ContentAssemblyIssue]:
    issues: list[ContentAssemblyIssue] = []
    asset_rows = {_row_value(row, "asset_key"): row for row in fixtures.asset_registry if _row_value(row, "asset_key")}

    for row in content_rows:
        asset_key = _row_value(row, "asset_key")
        if not asset_key:
            continue
        asset_row = asset_rows.get(asset_key)
        if asset_row is None:
            issues.append(
                ContentAssemblyIssue(
                    "fixture.asset_missing",
                    f"asset_registry has no row for asset key: {asset_key}",
                    surface="asset_registry.asset_key",
                    missing=(asset_key,),
                )
            )
            continue
        asset_path = _row_value(asset_row, "path")
        if not asset_path:
            issues.append(
                ContentAssemblyIssue(
                    "fixture.asset_path_missing",
                    f"asset row has no path: {asset_key}",
                    surface="asset_registry.path",
                    missing=(asset_key,),
                )
            )
            continue
        if not _resolve_path(asset_path, root=repo_root).exists():
            issues.append(
                ContentAssemblyIssue(
                    "fixture.asset_path_missing",
                    f"asset path does not exist for {asset_key}: {asset_path}",
                    surface="asset_registry.path",
                    missing=(asset_path,),
                )
            )
    return issues


def validate_content_assembly_contract(
    *,
    contract_path: Path,
    fixtures_dir: Path,
    repo_root: Path = ROOT,
) -> ContentAssemblyValidationResult:
    issues = inspect_content_assembly_fixture_schema(fixtures_dir)
    try:
        contract = load_assembly_contract(contract_path)
    except RuntimeError as exc:
        return ContentAssemblyValidationResult((ContentAssemblyIssue("contract.invalid", str(exc)),))

    issues.extend(_validate_contract_blocks(contract))
    issues.extend(_validate_fallback(contract))
    if any(issue.code.startswith("fixture.") for issue in issues):
        return ContentAssemblyValidationResult(tuple(issues))

    try:
        fixtures = load_content_assembly_fixtures(fixtures_dir)
    except RuntimeError as exc:
        return ContentAssemblyValidationResult((ContentAssemblyIssue("fixture.invalid", str(exc)),))

    page_rows = _page_rows(fixtures, contract)
    page_block_ids = _block_ids(page_rows)
    content_rows = _content_rows_for_blocks(fixtures, page_block_ids)
    issues.extend(_validate_page_rows(contract, page_rows))
    issues.extend(_validate_content_blocks(contract, page_block_ids, content_rows))
    issues.extend(_validate_required_fields(contract, fixtures, page_block_ids, repo_root))
    issues.extend(_validate_assets(fixtures, content_rows, repo_root))

    return ContentAssemblyValidationResult(tuple(issues))


def render_content_assembly_report(result: ContentAssemblyValidationResult) -> str:
    if result.valid:
        return "[content-assembly-contract] OK"
    return "\n".join(f"[content-assembly-contract] ERROR {issue.format()}" for issue in result.issues)


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate fixture-backed content assembly contracts.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="Validate one assembly contract against fixture tables.")
    validate_parser.add_argument("--contract", required=True, help="Assembly contract YAML path.")
    validate_parser.add_argument("--fixtures", required=True, help="Directory containing content assembly CSV fixtures.")
    args = parser.parse_args(argv)

    contract_path = _resolve_path(args.contract)
    fixtures_dir = _resolve_path(args.fixtures)
    result = validate_content_assembly_contract(contract_path=contract_path, fixtures_dir=fixtures_dir)
    print(render_content_assembly_report(result), file=sys.stderr if not result.valid else sys.stdout)
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(run())
