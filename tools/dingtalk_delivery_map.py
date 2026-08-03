#!/usr/bin/env python3
"""Resolve a published repo target to its DingTalk delivery identity.

Keyed on `(model, region)` — deliberately NOT on language. A publish queue row
must leave `Lang` blank (`tools/queue_config_resolution.py` rejects a
single-language family for publish), and the artifact it produces is one
whole-book bundle covering every language of that region's family: US carries
en/fr/es, EU carries en/fr/es/de/it/uk. One published deliverable therefore
spans several of the base's per-language 文案 rows, so a per-language key could
neither be populated nor would it describe the payload. The languages a bundle
covers travel as data (`dingtalk_languages`), letting the delivery agent hit
either the region-level 发布资料 row or the per-language 过程资料 rows without
this repo having to encode that routing. That column lists the languages the
model actually ships in that region, which is not always the whole family: the
EU family carries Ukrainian templates, but JE-1000F does not ship Ukrainian, so
its EU row lists five languages rather than six.

`文案版本` is likewise not mapped: verified against live data on 2026-08-03,
project HTE153 holds one row per 安规×语言 with 文案版本 as a per-row product
stage (`3.0 -DVT`, `4.0 PVT`, …), while repo versions are document revisions
(`0.8`, `1.7`). The repo's version travels verbatim in the delivery manifest.

Two failure modes, deliberately distinct:

- `DeliveryTargetNotMapped` — this target simply is not part of DingTalk
  delivery (AU/KR are single-language families that cannot publish today; CN
  and pt-BR belong to other models). Callers treat it as *skipped*, because a
  successful build of an undelivered target is not an error.
- `RuntimeError` — the map itself is malformed (missing column, duplicate key,
  blank field). That is fail-closed: a wrong 安规 would file a deliverable onto
  another product line's row.

DingTalk table ids and node paths are intentionally NOT recorded here; they
belong to the delivery agent's own configuration. This repo owns only the
stable business identifiers.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

DELIVERY_MAP_FILENAME = "dingtalk_delivery_map.csv"

REQUIRED_COLUMNS = (
    "model",
    "region",
    "project_code",
    "safety_regulation",
    "dingtalk_languages",
)

# Semicolon, not comma: this column is a list inside one CSV cell, and a
# half-width comma inside a field has bitten this repo's CSV contracts before.
LANGUAGE_SEPARATOR = ";"


class DeliveryTargetNotMapped(LookupError):
    """Raised when a target has no DingTalk delivery row by design."""


@dataclass(frozen=True)
class DingTalkDeliveryTarget:
    """DingTalk delivery identity for one published (model, region) bundle."""

    model: str
    region: str
    project_code: str
    safety_regulation: str
    dingtalk_languages: tuple[str, ...]

    @property
    def repo_key(self) -> tuple[str, str]:
        return (self.model, self.region)

    @property
    def dingtalk_identity(self) -> tuple[str, str]:
        return (self.project_code, self.safety_regulation)

    def as_manifest_fields(self) -> dict[str, object]:
        return {
            "project_code": self.project_code,
            "safety_regulation": self.safety_regulation,
            "languages": list(self.dingtalk_languages),
        }


def default_delivery_map_path(*, root: Path | None = None) -> Path:
    base = root or ROOT
    return base / "data" / DELIVERY_MAP_FILENAME


def _clean(value: object) -> str:
    return str(value or "").strip()


def _parse_languages(raw: str, *, line_number: int, map_path: Path) -> tuple[str, ...]:
    languages = tuple(
        part.strip() for part in raw.split(LANGUAGE_SEPARATOR) if part.strip()
    )
    if not languages:
        raise RuntimeError(
            "DingTalk delivery map row lists no dingtalk_languages at line "
            f"{line_number}: {map_path}"
        )
    if len(set(languages)) != len(languages):
        raise RuntimeError(
            "DingTalk delivery map row repeats a language at line "
            f"{line_number}: {map_path}"
        )
    return languages


def load_delivery_map(
    path: Path | None = None,
    *,
    root: Path | None = None,
) -> dict[tuple[str, str], DingTalkDeliveryTarget]:
    """Load the delivery map, rejecting malformed rows and duplicate keys."""

    map_path = path or default_delivery_map_path(root=root)
    if not map_path.is_file():
        raise RuntimeError(f"DingTalk delivery map is missing: {map_path}")

    with map_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(name.strip() for name in (reader.fieldnames or ()))
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise RuntimeError(
                "DingTalk delivery map is missing required column(s) "
                f"{', '.join(missing)}: {map_path}"
            )

        targets: dict[tuple[str, str], DingTalkDeliveryTarget] = {}
        for line_number, raw_row in enumerate(reader, start=2):
            values = {column: _clean(raw_row.get(column)) for column in REQUIRED_COLUMNS}
            if not any(values.values()):
                continue
            blank = [column for column, value in values.items() if not value]
            if blank:
                raise RuntimeError(
                    "DingTalk delivery map row has empty required field(s) "
                    f"{', '.join(blank)} at line {line_number}: {map_path}"
                )
            target = DingTalkDeliveryTarget(
                model=values["model"],
                region=values["region"],
                project_code=values["project_code"],
                safety_regulation=values["safety_regulation"],
                dingtalk_languages=_parse_languages(
                    values["dingtalk_languages"],
                    line_number=line_number,
                    map_path=map_path,
                ),
            )
            if target.repo_key in targets:
                raise RuntimeError(
                    "DingTalk delivery map has a duplicate target "
                    f"{describe_target(*target.repo_key)} at line {line_number}: {map_path}"
                )
            targets[target.repo_key] = target

    if not targets:
        raise RuntimeError(f"DingTalk delivery map has no rows: {map_path}")
    return targets


def describe_target(model: str, region: str) -> str:
    return f"model={model} region={region}"


def resolve_delivery_target(
    *,
    model: str,
    region: str,
    delivery_map: dict[tuple[str, str], DingTalkDeliveryTarget] | None = None,
    path: Path | None = None,
    root: Path | None = None,
) -> DingTalkDeliveryTarget:
    """Return the DingTalk identity for one published target.

    Raises `DeliveryTargetNotMapped` when the target is not part of DingTalk
    delivery, and `RuntimeError` when the map itself cannot be trusted.
    """

    targets = delivery_map if delivery_map is not None else load_delivery_map(path, root=root)
    key = (_clean(model), _clean(region))
    target = targets.get(key)
    if target is None:
        raise DeliveryTargetNotMapped(
            f"no DingTalk delivery row is mapped for {describe_target(*key)}; "
            f"add one to data/{DELIVERY_MAP_FILENAME} after confirming the 安规 "
            "and 文案语言 values against the live base"
        )
    return target
