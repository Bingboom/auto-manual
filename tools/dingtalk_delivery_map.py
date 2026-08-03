#!/usr/bin/env python3
"""Resolve a repo build target to its DingTalk delivery-row identity.

The DingTalk 「交付工作管理」 base identifies one manual deliverable by the
triple (项目代码, 安规, 文案语言) — verified against live data on 2026-08-03:
project HTE153 holds exactly 13 rows, one per 安规×语言 pair, all 文案状态
=Current with no duplicates. 文案版本 is therefore a per-row attribute (the
product stage that row currently sits at), not part of the row identity, so
this module deliberately maps no version: the repo's own document version
travels in the delivery manifest verbatim.

Mapping direction is repo -> DingTalk and the table only covers targets the
repo can actually build. Lookups are fail-closed: an unmapped target or a
duplicate row raises instead of guessing, because a wrong 安规/语言 guess would
write a deliverable onto the wrong product line's row.

DingTalk table ids and node paths are intentionally NOT recorded here. They
belong to the delivery agent's own configuration; this repo owns only the
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
    "lang",
    "project_code",
    "safety_regulation",
    "dingtalk_language",
)

_IDENTITY_COLUMNS = ("project_code", "safety_regulation", "dingtalk_language")


@dataclass(frozen=True)
class DingTalkDeliveryTarget:
    """One DingTalk delivery row identity for a repo (model, region, lang)."""

    model: str
    region: str
    lang: str
    project_code: str
    safety_regulation: str
    dingtalk_language: str

    @property
    def repo_key(self) -> tuple[str, str, str]:
        return (self.model, self.region, self.lang)

    @property
    def dingtalk_identity(self) -> tuple[str, str, str]:
        return (self.project_code, self.safety_regulation, self.dingtalk_language)

    def as_manifest_fields(self) -> dict[str, str]:
        return {
            "project_code": self.project_code,
            "safety_regulation": self.safety_regulation,
            "language": self.dingtalk_language,
        }


def default_delivery_map_path(*, root: Path | None = None) -> Path:
    base = root or ROOT
    return base / "data" / DELIVERY_MAP_FILENAME


def _clean(value: object) -> str:
    return str(value or "").strip()


def load_delivery_map(
    path: Path | None = None,
    *,
    root: Path | None = None,
) -> dict[tuple[str, str, str], DingTalkDeliveryTarget]:
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

        targets: dict[tuple[str, str, str], DingTalkDeliveryTarget] = {}
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
            target = DingTalkDeliveryTarget(**values)
            if target.repo_key in targets:
                raise RuntimeError(
                    "DingTalk delivery map has a duplicate target "
                    f"{describe_target(*target.repo_key)} at line {line_number}: {map_path}"
                )
            targets[target.repo_key] = target

    if not targets:
        raise RuntimeError(f"DingTalk delivery map has no rows: {map_path}")
    return targets


def describe_target(model: str, region: str, lang: str) -> str:
    return f"model={model} region={region} lang={lang}"


def resolve_delivery_target(
    *,
    model: str,
    region: str,
    lang: str,
    delivery_map: dict[tuple[str, str, str], DingTalkDeliveryTarget] | None = None,
    path: Path | None = None,
    root: Path | None = None,
) -> DingTalkDeliveryTarget:
    """Return the DingTalk row identity for one repo target, or raise."""

    targets = delivery_map if delivery_map is not None else load_delivery_map(path, root=root)
    key = (_clean(model), _clean(region), _clean(lang))
    target = targets.get(key)
    if target is None:
        raise RuntimeError(
            "DingTalk delivery map has no entry for "
            f"{describe_target(*key)}; add a row to data/{DELIVERY_MAP_FILENAME} "
            "after confirming the 安规 and 文案语言 values against the live base"
        )
    return target
