#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.utils.spec_master import canonicalize_model_token, read_spec_master_rows, source_language_for_row


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
    # Mirror the build's Is_Latest semantics (spec_master_row_helpers._is_truthy):
    # a blank cell counts as latest (the row IS rendered), and only explicit
    # 1/true/yes/y are truthy. The drift gate must see exactly the rows the build
    # renders — the old "not in a blocklist" form treated a blank cell as NOT
    # latest, so foreign identities in blank-Is_Latest rows were never forbidden
    # and slipped through the gate (a false negative during new-line onboarding
    # when the column is incomplete).
    token = value.strip().lower()
    if not token:
        return True
    return token in {"1", "true", "yes", "y"}


def _pick_lang_value(row: dict[str, str], lang: str) -> str:
    lang_key = lang.strip()
    source_lang = source_language_for_row(row)
    if lang_key.lower() == "en" or (source_lang and lang_key.lower() == source_lang):
        keys = ("Value_source", "value_source", "Value", "value")
    else:
        keys = (
            f"Value_{lang_key}",
            f"value_{lang_key}",
            f"Value_{lang_key.lower()}",
            f"value_{lang_key.lower()}",
            "Value_source",
            "value_source",
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
    region = _first_non_empty(row, ("Region", "region")) or None
    model = canonicalize_model_token(_first_non_empty(row, ("Model", "model")), region=region) or None
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
    target = (canonicalize_model_token(model, region=region), region)
    current_values = identities.get(target, {"product_name": set(), "model_no": set()})
    allowed_literals = {value for value in current_values.get("product_name", set()) if value}
    allowed_literals.update(value for value in current_values.get("model_no", set()) if value)
    for product_name in current_values.get("product_name", set()):
        short_name = _derive_short_product_name(product_name)
        if short_name:
            allowed_literals.add(short_name)
    allowed_literals.add(model)
    normalized_target_model = canonicalize_model_token(model, region=region)
    if normalized_target_model:
        allowed_literals.add(normalized_target_model)
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

    # Longest first so a longer allowed name is masked before a shorter one it
    # contains. Masking the current target's own identity out of each line before
    # searching for foreign literals prevents a foreign literal that is a
    # substring of an allowed one (e.g. "Explorer 1000" inside the current
    # "Explorer 1000 Plus") from firing on every line — the N vs N-Plus/Pro
    # naming pattern is the norm for this catalog.
    allowed_sorted = sorted((literal for literal in allowed_literals if literal), key=len, reverse=True)

    matches: list[IdentityDriftMatch] = []
    seen: set[tuple[Path, int, str]] = set()
    for rst_path in sorted(path for path in bundle_dir.rglob("*.rst") if path.is_file()):
        for line_no, line in enumerate(rst_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not _scannable_line(line):
                continue
            masked_line = line
            for allowed in allowed_sorted:
                if allowed in masked_line:
                    masked_line = masked_line.replace(allowed, " " * len(allowed))
            for literal in sorted(forbidden_literals, key=len, reverse=True):
                if literal not in masked_line:
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
