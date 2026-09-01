#!/usr/bin/env python3
"""Load and validate the renderer-neutral manual style contract.

The contract does not render output.  It binds the Web, LaTeX, IDML, and Word
projections plus the shared layout-token source so cross-renderer drift is
visible before a build reaches a designer.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - environment/setup failure
    raise RuntimeError("PyYAML is required to load the manual style contract") from exc

try:
    from tools.render_contract_schema import (
        effective_final_mile,
        validate_v2_contract,
    )
    from tools.script_bootstrap import bootstrap_repo_root
    from tools.utils.path_utils import Paths
except ImportError:  # pragma: no cover - direct script execution fallback
    from render_contract_schema import effective_final_mile, validate_v2_contract
    from script_bootstrap import bootstrap_repo_root
    from utils.path_utils import Paths


ROOT = bootstrap_repo_root(__file__, parent_count=1)
PATHS = Paths(root=ROOT)
SUPPORTED_UNITS = frozenset({"", "none", "null", "pt", "mm", "em", "ex", "ratio", "int", "cmyk"})
SUPPORTED_STATUSES = frozenset({"aligned", "partial"})
LAYOUT_PARAMS_HASH_ALGORITHM = "ordered-layout-tokens/v1"


@dataclass(frozen=True)
class LayoutToken:
    key: str
    value: str
    unit: str
    comment: str


def load_layout_tokens(csv_path: Path) -> dict[str, LayoutToken]:
    tokens: dict[str, LayoutToken] = {}
    seen_keys: set[str] = set()
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"key", "value"}.issubset(reader.fieldnames):
            raise ValueError(f"layout token CSV is missing key/value columns: {csv_path}")
        for row in reader:
            key = (row.get("key") or "").strip()
            value = (row.get("value") or "").strip()
            if not key:
                continue
            if key in seen_keys:
                raise ValueError(f"duplicate layout token: {key}")
            seen_keys.add(key)
            if not value:
                continue
            unit = (row.get("unit") or "").strip().lower()
            if unit not in SUPPORTED_UNITS:
                raise ValueError(f"unsupported layout token unit {unit!r} for {key}")
            tokens[key] = LayoutToken(
                key=key,
                value=value,
                unit=unit,
                comment=(row.get("comment") or "").strip(),
            )
    return tokens


def _language_row_prefixes() -> tuple[frozenset[str], dict[str, str]]:
    """Prefixes a build can actually look up, plus alias -> canonical hints.

    Language rows are written ``lang_<code>_<base-key>`` and every lookup path
    builds that prefix from the **canonical** code: the IDML cascade takes the
    base subtag (``pt-BR`` -> ``pt``) and ``resolve_layout_tokens`` swaps the
    hyphen (``pt_br``). The registry also carries aliases — ``ja`` is spelled
    ``jp`` for the phase2 data columns — but nothing ever builds a prefix from
    one, so an alias-spelled row is unreachable and silently falls back to the
    base value.
    """

    try:
        from tools.lang_registry import LANGUAGE_REGISTRY
    except ImportError:  # pragma: no cover - direct script execution
        from lang_registry import LANGUAGE_REGISTRY  # type: ignore[no-redef]

    prefixes: set[str] = set()
    canonical_for: dict[str, str] = {}
    for spec in LANGUAGE_REGISTRY:
        code = spec.code.casefold()
        prefixes.update({code, code.replace("-", "_"), code.split("-", 1)[0]})
        for alias in spec.aliases:
            folded = alias.casefold()
            if folded != code:
                canonical_for[folded] = spec.code
    return frozenset(prefixes), canonical_for


def _reject_unreachable_language_rows(
    tokens: dict[str, LayoutToken], source: Path,
) -> None:
    """Fail closed on a language row no lookup path can reach."""

    prefixes, canonical_for = _language_row_prefixes()
    for key in tokens:
        if not key.startswith("lang_"):
            continue
        if any(key.startswith(f"lang_{prefix}_") for prefix in prefixes):
            continue
        spelling = key[len("lang_"):].split("_", 1)[0]
        canonical = canonical_for.get(spelling.casefold())
        hint = (
            f"use the canonical code {canonical!r}, not the alias {spelling!r}"
            if canonical
            else f"{spelling!r} is not a registered language code"
        )
        raise ValueError(
            f"layout token {source} declares an unreachable language row "
            f"{key!r}: {hint}. Nothing builds a lang_ prefix from it, so the "
            "row would be silently ignored and the base value used instead."
        )


def load_layout_token_layers(
    base_csv: Path,
    overlay_csvs: tuple[Path, ...] = (),
) -> dict[str, LayoutToken]:
    """Load one baseline plus additive target-selected token overlays.

    Overlays are deliberately additive.  A target may opt into tokens owned by
    an additional composition family, but it may not silently replace an
    approved baseline value through this path.
    """

    tokens = load_layout_tokens(base_csv)
    _reject_unreachable_language_rows(tokens, base_csv)
    for overlay_csv in overlay_csvs:
        overlay = load_layout_tokens(overlay_csv)
        _reject_unreachable_language_rows(overlay, overlay_csv)
        duplicates = sorted(set(tokens).intersection(overlay))
        if duplicates:
            raise ValueError(
                f"layout token overlay {overlay_csv} redefines existing keys: "
                + ", ".join(duplicates)
            )
        tokens.update(overlay)
    return tokens


def layout_tokens_sha256(tokens: dict[str, LayoutToken]) -> str:
    """Hash ordered key/value/unit semantics, excluding CSV presentation details."""
    payload = [
        {"key": token.key, "value": token.value, "unit": token.unit}
        for token in tokens.values()
    ]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resolve_layout_tokens(tokens: dict[str, LayoutToken], lang: str | None = None) -> dict[str, LayoutToken]:
    """Resolve base tokens plus the target language override layer.

    Language rows use ``lang_<code>_<base-key>``. The resolved mapping exposes
    base keys only, which gives both renderers the same cascade contract.
    """
    resolved = {key: token for key, token in tokens.items() if not key.startswith("lang_")}
    normalized = (lang or "").strip().lower().replace("-", "_")
    if not normalized:
        return resolved
    prefix = f"lang_{normalized}_"
    for key, token in tokens.items():
        if not key.startswith(prefix):
            continue
        base_key = key[len(prefix):]
        if base_key not in resolved:
            raise ValueError(f"language override {key} has no base token {base_key}")
        resolved[base_key] = LayoutToken(
            key=base_key,
            value=token.value,
            unit=token.unit,
            comment=token.comment,
        )
    return resolved


def load_render_contract(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"render contract root must be a mapping: {path}")
    return raw


def contract_sha256(contract: dict[str, Any]) -> str:
    payload = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def style_ids(contract: dict[str, Any]) -> set[str]:
    styles = contract.get("styles") or {}
    return set(styles) if isinstance(styles, dict) else set()


def validate_render_contract(
    contract: dict[str, Any],
    tokens: dict[str, LayoutToken],
    *,
    strict: bool = False,
) -> list[str]:
    if contract.get("schema_version") == 2:
        return validate_v2_contract(contract, tokens, strict=strict)

    issues: list[str] = []
    if contract.get("schema_version") != 1:
        issues.append("schema_version must be 1 or 2")
    styles = contract.get("styles")
    if not isinstance(styles, dict) or not styles:
        return issues + ["styles must be a non-empty mapping"]

    for style_id, style in styles.items():
        prefix = f"styles.{style_id}"
        if not str(style_id).startswith("HB-"):
            issues.append(f"{prefix}: style ID must start with HB-")
        if not isinstance(style, dict):
            issues.append(f"{prefix}: style must be a mapping")
            continue
        semantics = style.get("semantic_source_kinds")
        if not isinstance(semantics, list) or not all(str(item).strip() for item in semantics):
            issues.append(f"{prefix}: semantic_source_kinds must be a non-empty list")
        for token_ref in style.get("token_refs") or []:
            if token_ref not in tokens:
                issues.append(f"{prefix}: missing layout token {token_ref}")
        latex = style.get("latex") or {}
        if not latex.get("owner") or not latex.get("entrypoints"):
            issues.append(f"{prefix}: latex owner and entrypoints are required")
        indesign = style.get("indesign") or {}
        if not indesign.get("renderer"):
            issues.append(f"{prefix}: indesign renderer is required")
        paragraph_styles = indesign.get("paragraph_styles")
        has_paragraph_styles = False
        if paragraph_styles is not None:
            if (
                not isinstance(paragraph_styles, list)
                or not paragraph_styles
                or not all(
                    isinstance(value, str) and value.strip()
                    for value in paragraph_styles
                )
            ):
                issues.append(
                    f"{prefix}: indesign paragraph_styles must be a non-empty "
                    "list of non-empty strings"
                )
            else:
                has_paragraph_styles = True
        if not (
            has_paragraph_styles
            or any(
                indesign.get(key)
                for key in ("paragraph_style", "object_style", "table_style")
            )
        ):
            issues.append(f"{prefix}: at least one InDesign style binding is required")
        final_mile = effective_final_mile(contract, style)
        if final_mile.get("content_editable") is not False:
            issues.append(f"{prefix}: InDesign content_editable must be false")
        status = style.get("status")
        if status not in SUPPORTED_STATUSES:
            issues.append(f"{prefix}: unsupported status {status!r}")
        debt = style.get("debt") or []
        if strict and (status != "aligned" or debt):
            issues.append(f"{prefix}: strict parity requires aligned status with no debt")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=PATHS.manual_style_contract)
    parser.add_argument("--tokens", type=Path, default=PATHS.layout_params_csv)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    contract = load_render_contract(args.contract)
    tokens = load_layout_tokens(args.tokens)
    issues = validate_render_contract(contract, tokens, strict=args.strict)
    for issue in issues:
        print(f"[render-contract] FAIL {issue}")
    print(
        f"[render-contract] {'OK' if not issues else f'{len(issues)} issue(s)'}: "
        f"styles={len(style_ids(contract))} sha256={contract_sha256(contract)}"
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
