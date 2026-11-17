#!/usr/bin/env python3
"""Deterministic readiness and asset-foundation preflight for Agent Web manual authoring."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.asset_registry import APPROVED_STATUS, REGISTRY_RELATIVE_PATH
from tools.component_specs.registry import load_component_registry
from tools.corpus.discover import DiscoveredIR, discover_ir_pairs, normalize_lang_key
from tools.utils.path_utils import Paths

SCHEMA_VERSION = "auto-manual-web-authoring-preflight/v1"
_SHARED_MODEL_TOKENS = frozenset({"all", "shared", "通用"})
_TOKEN_SPLIT_RE = re.compile(r"[,\s]+")


def _split_model_tokens(raw_value: str) -> list[str]:
    return [token for token in _TOKEN_SPLIT_RE.split(raw_value.strip()) if token]


def _classify_asset_scope(raw_models: str, model_norm: str) -> str | None:
    tokens = _split_model_tokens(raw_models)
    lowered = {token.casefold() for token in tokens}
    if model_norm in lowered:
        return "model"
    if lowered & _SHARED_MODEL_TOKENS:
        return "shared"
    return None


def _read_asset_rows(registry_path: Path) -> list[dict[str, str]]:
    if not registry_path.is_file():
        return []
    with registry_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {str(k): (v or "").strip() for k, v in row.items() if k is not None}
            for row in reader
        ]


def _summarize_assets(resolved_root: Path, model: str) -> dict[str, Any]:
    registry_path = resolved_root / REGISTRY_RELATIVE_PATH
    if not registry_path.is_file():
        return {
            "registry_path": REGISTRY_RELATIVE_PATH.as_posix(),
            "registry_present": False,
            "total_matched": 0,
            "model_matched": 0,
            "shared_matched": 0,
            "ready_count": 0,
            "pending_textless_count": 0,
            "by_status": {},
            "by_category": {},
            "by_language_dimension": {},
            "reusable_asset_keys": [],
        }

    model_norm = model.strip().casefold()
    status_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    dim_counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    reusable_keys: list[str] = []
    pending_textless = 0

    for row in _read_asset_rows(registry_path):
        scope = _classify_asset_scope(row.get("适用机型", ""), model_norm)
        if scope is None:
            continue
        scope_counts[scope] += 1
        status = row.get("状态", "") or "(empty)"
        category = row.get("类别", "") or "(empty)"
        lang_dim = row.get("语言维度", "") or "(empty)"
        status_counts[status] += 1
        category_counts[category] += 1
        dim_counts[lang_dim] += 1
        is_pending_textless = row.get("待无字化", "").upper() == "TRUE"
        if is_pending_textless:
            pending_textless += 1
        asset_key = row.get("asset_key", "")
        if status == APPROVED_STATUS and not is_pending_textless and asset_key:
            reusable_keys.append(asset_key)

    return {
        "registry_path": REGISTRY_RELATIVE_PATH.as_posix(),
        "registry_present": True,
        "total_matched": scope_counts["model"] + scope_counts["shared"],
        "model_matched": scope_counts["model"],
        "shared_matched": scope_counts["shared"],
        "ready_count": status_counts.get(APPROVED_STATUS, 0),
        "pending_textless_count": pending_textless,
        "by_status": dict(sorted(status_counts.items())),
        "by_category": dict(sorted(category_counts.items())),
        "by_language_dimension": dict(sorted(dim_counts.items())),
        "reusable_asset_keys": sorted(reusable_keys),
    }


def _ir_entry(ir: DiscoveredIR) -> dict[str, Any]:
    return {
        "model": ir.model,
        "region": ir.region,
        "language": ir.language,
        "publication_eligible": ir.publication_eligible,
        "rel_path": ir.rel_path,
    }


def _summarize_ir_siblings(
    resolved_root: Path,
    model: str,
    region: str,
    lang: str | None,
) -> dict[str, Any]:
    discovered, _pairs, _abstentions, skipped = discover_ir_pairs(
        repo_root=resolved_root,
        model=model.strip(),
        region=None,
    )
    region_norm = region.strip().casefold()
    ordered = sorted(discovered, key=lambda item: (item.region, item.language, item.rel_path))
    same_region = [_ir_entry(item) for item in ordered if item.region.casefold() == region_norm]
    cross_region = [_ir_entry(item) for item in ordered if item.region.casefold() != region_norm]

    target_lang_present: bool | None = None
    if lang and lang.strip():
        lang_key = normalize_lang_key(lang)
        target_lang_present = any(
            normalize_lang_key(str(item["language"])) == lang_key for item in same_region
        )

    return {
        "same_region_count": len(same_region),
        "cross_region_count": len(cross_region),
        "same_region_languages": sorted({str(item["language"]) for item in same_region}),
        "cross_region_languages": sorted(
            {f"{item['region']}:{item['language']}" for item in cross_region}
        ),
        "target_lang_present": target_lang_present,
        "same_region": same_region,
        "cross_region": cross_region,
        "skipped": skipped,
    }


def _summarize_shared_contracts(resolved_root: Path) -> dict[str, Any]:
    paths = Paths(root=resolved_root)
    contracts_dir = paths.renderer_contracts_dir
    if contracts_dir.is_dir():
        stylesheets = [
            path.relative_to(resolved_root).as_posix()
            for path in sorted(contracts_dir.glob("web_*.css"))
            if path.is_file()
        ]
    else:
        stylesheets = []

    registry_path = paths.component_registry_contract
    if registry_path.is_file():
        registry = load_component_registry(registry_path)
        registry_source = registry_path.relative_to(resolved_root).as_posix()
    else:
        registry = load_component_registry()
        registry_source = "repo-default"

    components = registry.get("components")
    component_ids = (
        sorted(str(key) for key in components.keys())
        if isinstance(components, Mapping)
        else []
    )
    return {
        "component_registry_source": registry_source,
        "component_specs": component_ids,
        "web_stylesheets": stylesheets,
    }


def build_authoring_preflight(
    repo_root: Path,
    model: str,
    region: str,
    lang: str | None = None,
) -> dict[str, Any]:
    """Build the deterministic Stage-0 authoring preflight inventory."""

    resolved_root = repo_root.resolve()
    target_lang = lang.strip() if lang and lang.strip() else None
    return {
        "schema_version": SCHEMA_VERSION,
        "target": {
            "model": model.strip(),
            "region": region.strip(),
            "lang": target_lang,
        },
        "ir_siblings": _summarize_ir_siblings(resolved_root, model, region, target_lang),
        "assets": _summarize_assets(resolved_root, model),
        "shared_contracts": _summarize_shared_contracts(resolved_root),
    }


def format_preflight_markdown(payload: Mapping[str, Any]) -> str:
    """Render a concise Markdown summary of the preflight inventory."""

    target = payload["target"]
    siblings = payload["ir_siblings"]
    assets = payload["assets"]
    contracts = payload["shared_contracts"]

    lines = [
        f"# Web Authoring Preflight: {target['model']} ({target['region']})",
        "",
        f"- Target language: `{target['lang'] or '(unspecified)'}`",
        f"- Same-region `manual-ir/v2` siblings: {siblings['same_region_count']} "
        f"({', '.join(siblings['same_region_languages']) or 'none'})",
        f"- Cross-region `manual-ir/v2` siblings: {siblings['cross_region_count']} "
        f"({', '.join(siblings['cross_region_languages']) or 'none'})",
        f"- Matched assets (`{assets['registry_path']}`): {assets['total_matched']} "
        f"(model={assets['model_matched']}, shared={assets['shared_matched']}, "
        f"ready={assets['ready_count']}, pending_textless={assets['pending_textless_count']})",
        f"- Shared Web stylesheets: {len(contracts['web_stylesheets'])}",
        f"- Registered ComponentSpecs: {len(contracts['component_specs'])}",
    ]
    if assets["reusable_asset_keys"]:
        preview = ", ".join(assets["reusable_asset_keys"][:10])
        suffix = f" (+{len(assets['reusable_asset_keys']) - 10} more)" if len(assets["reusable_asset_keys"]) > 10 else ""
        lines.append(f"- Reusable `asset_key` sample: {preview}{suffix}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for authoring_preflight."""

    parser = argparse.ArgumentParser(
        description="Inventory sibling manual-ir/v2 packages, visual assets, and shared Web contracts."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repository root to inspect.",
    )
    parser.add_argument("--model", required=True, help="Target product model (e.g. JE-1000F).")
    parser.add_argument("--region", required=True, help="Target region (e.g. US, EU, JP, KR).")
    parser.add_argument("--lang", default=None, help="Optional target language code (e.g. en, fr).")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of a Markdown summary.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for authoring_preflight."""

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    payload = build_authoring_preflight(
        repo_root=args.repo_root,
        model=args.model,
        region=args.region,
        lang=args.lang,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_preflight_markdown(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
