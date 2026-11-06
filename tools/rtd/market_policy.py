"""Read a local business-content snapshot for the market and policy primer.

The 2026-11 layout groups the records by theme (``market_policy_themes.yaml``: a record joins the first theme that
lists one of its tags, else 其他) and shows a card per theme with a chip per country, then each record as one row
that opens to 政策变化 → 原理 → 对产品的影响, the boundary, the scope, the knowledge links and the sources.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

PAGE = "market/policy"
TEMPLATE = "market_policy.html"
CONTENT_DIR = "market-policy"
ASSETS = Path(__file__).resolve().parents[1] / "rtd_portal_assets"
THEMES = "market_policy_themes.yaml"
THEMES_SCHEMA = "hello-docs-market-themes/v1"
STATUS_ORDER = ("verified", "unverified", "demand")
STATUS_LABELS = {"verified": "已核实", "unverified": "待核实", "demand": "业务需求"}
OTHER = {"id": "other", "title": "其他", "blurb": "", "icon": "other"}
_ICONS = {"language", "energy"}
_ID = re.compile(r"[a-z][a-z0-9-]*")


def _validate_record(record: dict, ids: set[str]) -> None:
    key = record["id"]
    if not _ID.fullmatch(key) or key in ids:
        raise ValueError("market policy record ids must be unique lower-case ids")
    ids.add(key)
    if record["status"] not in {"verified", "unverified", "demand"}:
        raise ValueError(f"unknown policy verification status: {key}")
    for field in ("title", "country", "region", "timeline", "change", "mechanism",
                  "impact", "reviewed"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"market policy record {key} needs {field}")
    if not isinstance(record.get("boundary", ""), str):
        raise ValueError(f"market policy record {key} needs a text boundary")


def _validate_evidence(record: dict, source: Path) -> None:
    key = record["id"]
    note = record.get("evidence_note", "")
    if not isinstance(note, str):
        raise ValueError(f"market policy record {key} needs a text evidence note")
    recorded_basis = record["status"] != "verified" and bool(note.strip())
    if not record["tags"] or not (record["sources"] or record.get("image") or recorded_basis):
        raise ValueError(f"market policy record {key} needs tags and evidence")
    if image := record.get("image"):
        asset = source.parent / "_assets" / image
        if Path(image).name != image or asset.is_symlink() or not asset.is_file():
            raise ValueError(f"missing or unsafe policy source image: {key}")
    for ref in record["sources"]:
        parts = urlsplit(ref["url"])
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            raise ValueError(f"market policy source must be a public HTTPS URL: {key}")
    if record["status"] == "verified" and not any(
        ref["kind"] == "official" for ref in record["sources"]
    ):
        raise ValueError(f"verified policy record {key} needs an official source")


def load_themes(assets: Path = ASSETS) -> dict[str, Any]:
    """The theme config; a malformed file raises ValueError (the build fails, as for a malformed snapshot)."""
    data = yaml.safe_load((assets / THEMES).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != THEMES_SCHEMA:
        raise ValueError(f"{THEMES}: schema must be {THEMES_SCHEMA}")
    themes = data.get("themes")
    if not isinstance(themes, list) or not themes:
        raise ValueError(f"{THEMES}: needs a themes list")
    ids: set[str] = set()
    for theme in themes:
        if not isinstance(theme, dict):
            raise ValueError(f"{THEMES}: each theme must be a mapping")
        key = str(theme.get("id"))
        if not _ID.fullmatch(key) or key in ids or key == OTHER["id"]:
            raise ValueError(f"{THEMES}: theme ids must be unique lower-case ids other than {OTHER['id']!r}: {key!r}")
        ids.add(key)
        if not all(isinstance(theme.get(field), str) and theme[field].strip() for field in ("title", "blurb")):
            raise ValueError(f"{THEMES}: theme {key} needs a title and a blurb")
        if theme.get("icon") not in _ICONS:
            raise ValueError(f"{THEMES}: theme {key} needs an icon from {sorted(_ICONS)}")
        tags = theme.get("tags")
        if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag for tag in tags):
            raise ValueError(f"{THEMES}: theme {key} needs a list of tags")
    return {"cross_region": str(data.get("cross_region") or ""), "themes": themes}


def _countries(records: list[dict]) -> list[dict[str, Any]]:
    """One chip per country in record order: how many records, their statuses (each once) and the first record."""
    chips: dict[str, dict[str, Any]] = {}
    for record in records:
        chip = chips.setdefault(record["country"], {"country": record["country"], "first": record["id"],
                                                    "count": 0, "statuses": []})
        chip["count"] += 1
        if record["status"] not in chip["statuses"]:
            chip["statuses"].append(record["status"])
    return list(chips.values())


def group_by_theme(records: list[dict], config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """The themes that hold records, in config order, then 其他 for records no theme claims (their ids returned)."""
    groups = [{**{key: theme[key] for key in ("id", "title", "blurb", "icon")}, "records": []}
              for theme in config["themes"]]
    other: list[dict] = []
    for record in records:
        tags = set(record["tags"])
        group = next((group for group, theme in zip(groups, config["themes"], strict=True) if tags & set(theme["tags"])),
                     None)
        (group["records"] if group is not None else other).append(record)
    if other:
        groups.append({**OTHER, "records": other})
    return ([{**group, "countries": _countries(group["records"])} for group in groups if group["records"]],
            [record["id"] for record in other])


def market_context(knowledge_root: Path, assets: Path = ASSETS) -> dict:
    """Missing content has an empty state; malformed content or theme config fails the build."""
    config = load_themes(assets)
    source = knowledge_root / CONTENT_DIR / "records.json"
    empty = {"records": [], "themes": [], "unthemed": [], "statuses": [], "status_labels": STATUS_LABELS,
             "country_count": 0, "reviewed": ""}
    if not source.is_file():
        return empty
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("market policy snapshot needs schema_version 1")
    ids = set()
    for record in data["records"]:
        _validate_record(record, ids)
        _validate_evidence(record, source)
        for link in record.get("knowledge", []):
            if not _ID.fullmatch(link["id"]):
                raise ValueError(f"invalid knowledge anchor: {record['id']}")
    records = data["records"]
    themes, unthemed = group_by_theme(records, config)
    present = {record["status"] for record in records}
    return {**empty, "records": records, "reviewed": data["reviewed"], "themes": themes, "unthemed": unthemed,
            "statuses": [status for status in STATUS_ORDER if status in present],
            "country_count": len({r["country"] for r in records} - {config["cross_region"]})}


def missing_knowledge_anchors(records: list[dict], topic_ids: set[str]) -> list[tuple[str, str]]:
    """(record id, anchor) for each ``products/knowledge#anchor`` link that names no topic."""
    return [(record["id"], link["id"]) for record in records
            for link in record.get("knowledge", []) if link["id"] not in topic_ids]
