#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.content_assembly_contract import (  # noqa: E402
    AssemblyContract,
    ContentAssemblyFixtures,
    load_assembly_contract,
    load_content_assembly_fixtures,
    render_content_assembly_report,
    row_applies,
    validate_content_assembly_contract,
)


FORBIDDEN_OUTPUT_DIRS = (
    Path("docs/templates"),
    Path("docs/_review"),
    Path("docs/_build"),
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


def _sort_key(row: dict[str, str]) -> tuple[int, str]:
    raw_order = _row_value(row, "order")
    try:
        order = int(raw_order)
    except ValueError:
        order = 0
    return order, _row_value(row, "block_id")


def _fallback_lang(contract: AssemblyContract, target_lang: str) -> str:
    return contract.fallback_lang or target_lang


def _page_rows_for_target(
    fixtures: ContentAssemblyFixtures,
    contract: AssemblyContract,
    *,
    region: str,
    lang: str,
) -> list[dict[str, str]]:
    return sorted(
        [
            row
            for row in fixtures.page_assembly
            if _row_value(row, "page_id") == contract.page_id
            and _row_value(row, "product_family") == contract.product_family
            and _is_truthy(row.get("enabled", ""))
            and row_applies(row, region=region, lang=lang)
        ],
        key=_sort_key,
    )


def _rank_content_row(row: dict[str, str], *, region: str, lang: str, fallback_lang: str) -> int | None:
    row_region = _row_value(row, "region")
    row_lang = _row_value(row, "lang").lower()
    region_exact = row_region == region
    region_wildcard = row_region in {"", "*"}
    lang_exact = row_lang == lang.lower()
    lang_fallback = row_lang == fallback_lang.lower()
    lang_wildcard = row_lang in {"", "*"}

    if region_exact and lang_exact:
        return 0
    if region_wildcard and lang_exact:
        return 1
    if region_exact and lang_fallback:
        return 2
    if region_wildcard and lang_fallback:
        return 3
    if region_exact and lang_wildcard:
        return 4
    if region_wildcard and lang_wildcard:
        return 5
    return None


def _content_row_for_block(
    fixtures: ContentAssemblyFixtures,
    block_id: str,
    *,
    region: str,
    lang: str,
    fallback_lang: str,
) -> dict[str, str]:
    candidates: list[tuple[int, dict[str, str]]] = []
    for row in fixtures.content_blocks:
        if _row_value(row, "block_id") != block_id:
            continue
        rank = _rank_content_row(row, region=region, lang=lang, fallback_lang=fallback_lang)
        if rank is not None:
            candidates.append((rank, row))
    if not candidates:
        raise RuntimeError(f"No content block metadata applies to {block_id} for {region}/{lang}")
    return sorted(candidates, key=lambda item: item[0])[0][1]


def _asset_row(fixtures: ContentAssemblyFixtures, asset_key: str) -> dict[str, str] | None:
    for row in fixtures.asset_registry:
        if _row_value(row, "asset_key") == asset_key:
            return row
    return None


def _field_rows(fixtures: ContentAssemblyFixtures, block_id: str) -> list[dict[str, str]]:
    return [row for row in fixtures.block_fields if _row_value(row, "block_id") == block_id]


def _render_field(row: dict[str, str]) -> str:
    parts = [
        f"row_key={_row_value(row, 'row_key')}",
        f"role={_row_value(row, 'value_role')}",
    ]
    placement = _row_value(row, "placement_key")
    variant = _row_value(row, "variant_key")
    fallback_policy = _row_value(row, "fallback_policy")
    required = _row_value(row, "required")
    if placement:
        parts.append(f"placement={placement}")
    if variant:
        parts.append(f"variant={variant}")
    if required:
        parts.append(f"required={required}")
    if fallback_policy:
        parts.append(f"fallback={fallback_policy}")
    return f"   - {_row_value(row, 'field_key')}: " + ", ".join(parts)


def render_content_assembly(
    *,
    contract_path: Path,
    fixtures_dir: Path,
    region: str,
    lang: str,
    repo_root: Path = ROOT,
) -> str:
    result = validate_content_assembly_contract(
        contract_path=contract_path,
        fixtures_dir=fixtures_dir,
        repo_root=repo_root,
    )
    if not result.valid:
        raise RuntimeError(render_content_assembly_report(result))

    contract = load_assembly_contract(contract_path)
    fixtures = load_content_assembly_fixtures(fixtures_dir)
    fallback_lang = _fallback_lang(contract, lang)
    page_rows = _page_rows_for_target(fixtures, contract, region=region, lang=lang)
    if not page_rows:
        raise RuntimeError(f"No enabled page assembly rows apply to {contract.page_id} for {region}/{lang}")

    lines = [
        f".. content-assembly:: {contract.page_id}",
        f"   :product-family: {contract.product_family}",
        f"   :region: {region}",
        f"   :lang: {lang}",
        f"   :fallback-lang: {fallback_lang}",
        "   :source: fixture",
        "",
    ]

    for page_row in page_rows:
        block_id = _row_value(page_row, "block_id")
        content_row = _content_row_for_block(
            fixtures,
            block_id,
            region=region,
            lang=lang,
            fallback_lang=fallback_lang,
        )
        lines.extend(
            [
                f".. content-block:: {block_id}",
                f"   :type: {_row_value(content_row, 'block_type')}",
                f"   :title-key: {_row_value(content_row, 'title_key')}",
                "",
            ]
        )

        asset_key = _row_value(content_row, "asset_key")
        if asset_key:
            asset = _asset_row(fixtures, asset_key)
            if asset is None:
                raise RuntimeError(f"No asset_registry row for {asset_key}")
            lines.extend(
                [
                    f"   .. image:: {_row_value(asset, 'path')}",
                    f"      :alt: {_row_value(asset, 'alt_key')}",
                    "",
                ]
            )

        fields = _field_rows(fixtures, block_id)
        if fields:
            lines.append("   Fields:")
            lines.extend(_render_field(row) for row in fields)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _ensure_safe_output_path(output_path: Path, *, repo_root: Path = ROOT) -> None:
    resolved = output_path.resolve()
    for relative_dir in FORBIDDEN_OUTPUT_DIRS:
        forbidden = (repo_root / relative_dir).resolve()
        try:
            resolved.relative_to(forbidden)
        except ValueError:
            continue
        raise RuntimeError(f"content assembly no-op output must not write under {relative_dir}")


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render fixture-backed no-op content assembly output.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_parser = subparsers.add_parser("render", help="Render one no-op assembly RST file.")
    render_parser.add_argument("--contract", required=True, help="Assembly contract YAML path.")
    render_parser.add_argument("--fixtures", required=True, help="Directory containing content assembly CSV fixtures.")
    render_parser.add_argument("--region", required=True, help="Target region.")
    render_parser.add_argument("--lang", required=True, help="Target language.")
    render_parser.add_argument("--output", required=True, help="Output RST path.")
    args = parser.parse_args(argv)

    contract_path = _resolve_path(args.contract)
    fixtures_dir = _resolve_path(args.fixtures)
    output_path = _resolve_path(args.output)

    try:
        rendered = render_content_assembly(
            contract_path=contract_path,
            fixtures_dir=fixtures_dir,
            region=args.region,
            lang=args.lang,
        )
        _ensure_safe_output_path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    except RuntimeError as exc:
        print(f"[content-assembly] ERROR {exc}", file=sys.stderr)
        return 1

    print(f"[content-assembly] wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
