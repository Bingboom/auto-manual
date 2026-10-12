"""Build-time 系统数据 page: published manuals, model capabilities and assets, filterable by region and model.

``/workspace/data/`` reads, at build time and from the repository only:

- ``docs/publish/publish_manifest.json``: one row per published Web route
  (model, region, language, version, build date), as the deliverables page
  reads it;
- ``data/model_capabilities.csv``: the capability switches of every
  ``<model>_<region>`` target;
- ``data/model_languages.csv``: the languages registered for a target;
- ``docs/_review/<model>/<region>``: the review pages on this commit;
- ``data/asset_registry.csv``: category, status, model and region of every
  registered asset.

The rows travel to the browser as one JSON block; ``_static/system-data.js``
filters them by region and model and draws the charts. Without JavaScript the
whole-repository counts and the publication table still show. A missing
publish manifest shows the publication cards as 无数据; an unreadable or
malformed CSV is an authoring error that skips the page (and its sidebar entry)
with a Sphinx warning.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from tools.rtd.production_evidence import read_publications
from tools.utils.path_utils import Paths, PathSegments, repo_root

PAGE = "workspace/data/index"
TEMPLATE = "system_data.html"
CAPABILITIES_CSV = "model_capabilities.csv"
LANGUAGES_CSV = "model_languages.csv"
ASSET_REGISTRY_CSV = "asset_registry.csv"
TARGET_KEY = "Document_key"
PROJECT = "Project"
# Asset rows whose model or region is ALL apply to every model or region.
SHARED = "ALL"
SWITCH = {"TRUE": 1, "FALSE": 0}

_STATUS_MARK = re.compile(r"^\W+")


class SystemDataError(ValueError):
    """The committed data no longer has the shape this page reads."""


def _rows(path: Path, required: tuple[str, ...]) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        rows = [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]
    missing = [name for name in required if name not in header]
    if missing:
        raise SystemDataError(f"{path.name} is missing columns {missing}")
    return header, rows


def _split_target(key: str, source: str) -> tuple[str, str]:
    model, _, region = key.partition("_")
    if not model or not region:
        raise SystemDataError(f"{source}: target key {key!r} is not <model>_<region>")
    return model, region


def review_page_counts(review_dir: Path) -> Counter:
    """RST pages under ``docs/_review/<model>/<region>``, keyed ``<model>_<region>``."""
    counts: Counter = Counter()
    if not review_dir.is_dir():
        return counts
    for model_dir in sorted(p for p in review_dir.iterdir() if p.is_dir()):
        for region_dir in sorted(p for p in model_dir.iterdir() if p.is_dir()):
            pages = sum(1 for _ in region_dir.rglob("*.rst"))
            if pages:
                counts[f"{model_dir.name}_{region_dir.name}"] = pages
    return counts


def read_targets(capabilities_csv: Path, languages_csv: Path, review_dir: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Capability names and one row per target, with its languages and review pages."""
    header, rows = _rows(capabilities_csv, (TARGET_KEY, PROJECT))
    names = [name for name in header if name not in (TARGET_KEY, PROJECT)]
    if not names:
        raise SystemDataError(f"{capabilities_csv.name} names no capabilities")
    _, language_rows = _rows(languages_csv, (TARGET_KEY, "languages"))
    languages = {row[TARGET_KEY]: [code for code in row["languages"].split(";") if code] for row in language_rows}
    reviews = review_page_counts(review_dir)
    targets = []
    for row in rows:
        key = row[TARGET_KEY]
        model, region = _split_target(key, capabilities_csv.name)
        switches = []
        for name in names:
            if row.get(name) not in SWITCH:
                raise SystemDataError(f"{capabilities_csv.name}: {key} {name} is {row.get(name)!r}, not TRUE/FALSE")
            switches.append(SWITCH[row[name]])
        targets.append({
            "key": key, "model": model, "region": region, "project": row[PROJECT],
            "caps": switches, "langs": languages.get(key, []), "review_pages": reviews.get(key, 0),
        })
    return names, targets


def read_assets(registry_csv: Path) -> list[dict[str, str]]:
    """Category, status (without its leading mark), model and region of every asset."""
    columns = ("asset_key", "类别", "状态", "适用机型", "适用区域")
    _, rows = _rows(registry_csv, columns)
    assets = []
    for row in rows:
        status = _STATUS_MARK.sub("", row["状态"])
        if not row["asset_key"] or not status or not row["适用机型"] or not row["适用区域"]:
            raise SystemDataError(f"{registry_csv.name}: asset {row['asset_key']!r} lacks a status, model or region")
        assets.append({"category": row["类别"], "status": status, "model": row["适用机型"], "region": row["适用区域"]})
    return assets


def read_published(manifest: Path) -> tuple[list[dict[str, str]] | None, str]:
    """One row per published route, newest build first; None without a readable manifest."""
    targets, built_at = read_publications(manifest)
    if targets is None:
        return None, ""
    rows = [{
        "model": target["model"], "region": target["region"], "lang": target["lang"],
        "version": str(target.get("version") or ""), "built_on": str(target.get("built_at") or "")[:10],
        "docname": f"{target['route']}/{PurePosixPath(target['manual']).stem}",
    } for target in targets]
    rows.sort(key=lambda r: (r["built_on"], r["model"], r["region"], r["lang"]), reverse=True)
    return rows, built_at[:10]


def _facets(*groups: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    regions: Counter = Counter()
    models: set[str] = set()
    for rows in groups:
        for row in rows:
            if row["region"] != SHARED:
                regions[row["region"]] += 1
            if row["model"] != SHARED:
                models.add(row["model"])
    ordered = sorted(regions.items(), key=lambda item: (-item[1], item[0]))
    return [{"code": code, "rows": count} for code, count in ordered], sorted(models)


def summary(published: list[dict[str, str]] | None, targets: list[dict[str, Any]],
            assets: list[dict[str, str]]) -> dict[str, Any]:
    """The whole-repository counts the page shows before (or without) any filter."""
    ready = sum(1 for asset in assets if asset["status"] == "成品")
    return {
        "manuals": len(published) if published is not None else None,
        "models": len({row["model"] for row in published}) if published is not None else None,
        "languages": len({row["lang"] for row in published}) if published is not None else None,
        "regions": len({row["region"] for row in published}) if published is not None else None,
        "targets": len(targets),
        "review_targets": sum(1 for target in targets if target["review_pages"]),
        "assets": len(assets),
        "ready_share": f"{ready / len(assets):.1%}" if assets else None,
    }


def system_data_context(root: Path, manifest: Path, language_labels: dict[str, str]) -> dict[str, Any]:
    paths = Paths(root)
    names, targets = read_targets(
        paths.data_dir / CAPABILITIES_CSV, paths.data_dir / LANGUAGES_CSV, paths.review_dir,
    )
    assets = read_assets(paths.data_dir / ASSET_REGISTRY_CSV)
    published, built_on = read_published(manifest)
    regions, models = _facets(published or [], targets, assets)
    used_languages = sorted({row["lang"] for row in published or []} | {code for t in targets for code in t["langs"]})
    payload = {
        "capabilities": names,
        "published": [{key: row[key] for key in ("model", "region", "lang")} for row in published]
        if published is not None else None,
        "targets": targets, "assets": assets, "regions": regions, "models": models,
        "language_labels": {code: language_labels[code] for code in used_languages if code in language_labels},
    }
    return {
        "summary": summary(published, targets, assets),
        "published": published, "built_on": built_on,
        "capability_count": len(names), "regions": regions, "models": models,
        # Safe inside <script type="application/json">: no "<" survives to close the element.
        "data_json": json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c"),
    }


def system_data_page_context(app, settings: dict[str, Any]) -> dict[str, Any] | None:
    """Context for PAGE, or None (with a warning) when the committed data has drifted."""
    from sphinx.util import logging as sphinx_logging

    manifest = Path(app.srcdir).parent / PathSegments.PUBLISH_MANIFEST_JSON
    try:
        return system_data_context(repo_root(), manifest, dict(settings.get("language_labels") or {}))
    except (ValueError, OSError, KeyError, csv.Error) as exc:
        sphinx_logging.getLogger(__name__).warning("System data page skipped: %s", exc)
        return None


__all__ = [
    "PAGE", "SystemDataError", "TEMPLATE", "read_assets", "read_published", "read_targets",
    "review_page_counts", "summary", "system_data_context", "system_data_page_context",
]
