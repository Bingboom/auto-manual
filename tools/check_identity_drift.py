#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.utils.spec_master import read_spec_master_rows


@dataclass(frozen=True)
class IdentityDriftMatch:
    path: Path
    line_no: int
    literal: str
    source_model: str | None
    source_region: str | None


def _first_non_empty(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return ""


def _is_truthy(value: str) -> bool:
    return value.strip().lower() not in {"", "0", "false", "no", "n"}


def _pick_lang_value(row: dict[str, str], lang: str) -> str:
    lang_key = lang.strip()
    keys = (
        f"Value_{lang_key}",
        f"value_{lang_key}",
        f"Value_{lang_key.lower()}",
        f"value_{lang_key.lower()}",
        "Value",
        "value",
    )
    return _first_non_empty(row, keys)


def _derive_short_product_name(name: str) -> str:
    text = name.strip()
    prefix = "Jackery "
    if text.startswith(prefix):
        return text[len(prefix) :].strip()
    return ""


def _target_key(row: dict[str, str]) -> tuple[str | None, str | None]:
    model = _first_non_empty(row, ("Model", "model")) or None
    region = _first_non_empty(row, ("Region", "region")) or None
    return model, region


def _collect_latest_identity_literals(
    spec_master_csv: Path,
    *,
    langs: list[str],
) -> dict[tuple[str | None, str | None], dict[str, set[str]]]:
    rows = read_spec_master_rows(spec_master_csv)
    identities: dict[tuple[str | None, str | None], dict[str, set[str]]] = {}

    for row in rows:
        row_key = _first_non_empty(row, ("Row_key", "row_key"))
        if row_key not in {"product_name", "model_no"}:
            continue
        if not _is_truthy(_first_non_empty(row, ("Is_Latest", "is_latest"))):
            continue

        target = _target_key(row)
        values_by_key = identities.setdefault(target, {"product_name": set(), "model_no": set()})
        for lang in langs:
            value = _pick_lang_value(row, lang)
            if not value:
                continue
            values_by_key[row_key].add(value)
    return identities


def _scannable_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(".. "):
        return False
    if stripped.startswith(":"):
        return False
    return True


def find_identity_drift_matches(
    *,
    bundle_dir: Path,
    spec_master_csv: Path,
    model: str | None,
    region: str | None,
    langs: list[str],
    allowlist: tuple[str, ...] = (),
) -> tuple[IdentityDriftMatch, ...]:
    if not bundle_dir.exists() or not model:
        return ()

    identities = _collect_latest_identity_literals(spec_master_csv, langs=langs)
    target = (model, region)
    current_values = identities.get(target, {"product_name": set(), "model_no": set()})
    allowed_literals = {value for value in current_values.get("product_name", set()) if value}
    allowed_literals.update(value for value in current_values.get("model_no", set()) if value)
    for product_name in current_values.get("product_name", set()):
        short_name = _derive_short_product_name(product_name)
        if short_name:
            allowed_literals.add(short_name)
    allowed_literals.add(model)
    allowed_literals.update(value.strip() for value in allowlist if value.strip())

    forbidden_literals: dict[str, tuple[str | None, str | None]] = {}
    for source_target, values_by_key in identities.items():
        if source_target == target:
            continue
        for value in [*values_by_key.get("product_name", set()), *values_by_key.get("model_no", set())]:
            literal = value.strip()
            if not literal or literal in allowed_literals:
                continue
            forbidden_literals.setdefault(literal, source_target)

    matches: list[IdentityDriftMatch] = []
    seen: set[tuple[Path, int, str]] = set()
    for rst_path in sorted(path for path in bundle_dir.rglob("*.rst") if path.is_file()):
        for line_no, line in enumerate(rst_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not _scannable_line(line):
                continue
            for literal in sorted(forbidden_literals, key=len, reverse=True):
                if literal not in line:
                    continue
                key = (rst_path, line_no, literal)
                if key in seen:
                    continue
                seen.add(key)
                source_model, source_region = forbidden_literals[literal]
                matches.append(
                    IdentityDriftMatch(
                        path=rst_path,
                        line_no=line_no,
                        literal=literal,
                        source_model=source_model,
                        source_region=source_region,
                    )
                )
    return tuple(matches)
