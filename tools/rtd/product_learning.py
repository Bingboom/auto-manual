"""Small technical primer, linked only to products in the frozen manual catalog.

The 2026-11 layout opens on an energy-flow map and a theme map (`themes`: each tag with its topics' short
labels), then shows each topic as a card whose figure is a typical teaching circuit (a topic's optional
`circuit`, one of the portal's circuit-*.svg files), a hand-drawn diagram or the chain of its nodes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from tools.rtd.product_matrix import ProductMatrixError, positioning_groups

PAGE = "products/knowledge"
TEMPLATE = "product_knowledge.html"
# The HomePower case in TEMPLATE quotes this manual; it is left out while the catalog lacks it.
BACKUP_CASE = ("JHP-3600C", "US")
_ID = re.compile(r"[a-z][a-z0-9-]*")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_CIRCUIT = re.compile(r"circuit-[a-z0-9-]+\.svg")


def _validate_topic(topic: dict, ids: set[str], tag_ids: list[str], groups: dict, static: Path) -> None:
    key = topic["id"]
    if key in ids or not _ID.fullmatch(key):
        raise ValueError("product knowledge topics need unique lower-case ids")
    ids.add(key)
    if not topic["tags"] or not set(topic["tags"]) <= set(tag_ids):
        raise ValueError(f"unknown or empty knowledge tags: {key}")
    if not topic["groups"] or not set(topic["groups"]) <= groups.keys():
        raise ValueError(f"unknown or empty product groups: {key}")
    for field in ("title", "answer", "application", "boundary", "read"):
        if not isinstance(topic[field], str) or not topic[field].strip():
            raise ValueError(f"knowledge topic {key} needs {field}")
    # `added` (first published, YYYY-MM-DD) feeds 知识库首页's growth line; optional, but checked when present.
    if "added" in topic and not _DATE.fullmatch(str(topic["added"])):
        raise ValueError(f"knowledge topic {key} has an invalid added date: {topic['added']!r}")
    circuit = topic.get("circuit")
    if circuit is not None and (not _CIRCUIT.fullmatch(str(circuit)) or not (static / circuit).is_file()):
        raise ValueError(f"knowledge topic {key} names an unknown circuit: {circuit!r}")


def short_label(title: str) -> str:
    """A topic's name on the theme map: its title up to the full-width colon, else the whole title."""
    return title.split("：", 1)[0].strip()


def _themes(tags: list[dict], topics: list[dict]) -> list[dict]:
    """Each tag with the topics that carry it, in page order; a topic may sit under several tags."""
    return [{"id": tag["id"], "title": tag["title"],
             "topics": [{"id": topic["id"], "label": short_label(topic["title"])}
                        for topic in topics if tag["id"] in topic["tags"]]}
            for tag in tags]


def _references(products: list[dict], models: set[str]) -> list[dict]:
    references = []
    for product in products:
        if product["model"] not in models:
            continue
        options = [item for item in product["language_options"] if item.get("url")]
        preferred = next((item for item in options if item["code"] == "en"), None)
        preferred = preferred or (options[0] if options else None)
        references.append({
            "model": product["model"], "region": product["region"], "name": product["name"],
            "url": preferred["url"] if preferred else product["url"],
            "language": preferred["label"] if preferred else "当前发布页",
        })
    return references


def _groups(assets: Path, settings: dict, topics: list[dict]) -> dict[str, set[str]]:
    """Group id -> models as the product matrix places them; the navigation alone if its config is unusable."""
    try:
        return positioning_groups(assets, settings)
    except ProductMatrixError as exc:
        groups = {row["id"]: set(row["models"])
                  for rows in settings.get("navigation", {}).values() for row in rows}
        # A topic group the navigation lacks (homebackup comes from the matrix config) is empty, not a failed build.
        named = {group for topic in topics if isinstance(topic.get("groups"), list) for group in topic["groups"]}
        missing = sorted(named - groups.keys())
        from sphinx.util import logging as sphinx_logging

        sphinx_logging.getLogger(__name__).warning(
            "Product knowledge uses the navigation groups only (%s); groups left empty: %s",
            exc, ", ".join(missing) or "none")
        return {**groups, **{group: set() for group in missing}}


def learning_context(assets: Path, settings: dict, products: list[dict]) -> dict:
    curriculum = json.loads((assets / "product_knowledge.json").read_text(encoding="utf-8"))
    groups = _groups(assets, settings, curriculum["topics"])
    tags = curriculum["tags"]
    tag_ids = [tag["id"] for tag in tags]
    if len(set(tag_ids)) != len(tag_ids) or any(not _ID.fullmatch(key) for key in tag_ids):
        raise ValueError("product knowledge tags need unique lower-case ids")
    ids: set[str] = set()
    topics = []
    for topic in curriculum["topics"]:
        _validate_topic(topic, ids, tag_ids, groups, assets / "_static")
        models = set().union(*(groups[group] for group in topic["groups"]))
        topics.append({**topic, "models": sorted(models), "references": _references(products, models)})
    covered = {model for topic in topics for model in topic["models"]}
    model, region = BACKUP_CASE
    case = next((ref for ref in _references(products, {model}) if ref["region"] == region), None)
    # The selector offers only products some topic covers, so choosing one never empties the list.
    themes = _themes(tags, topics)
    added = [str(topic["added"]) for topic in topics if topic.get("added")]
    return {"topics": topics, "tags": tags, "themes": themes,
            "tag_counts": {theme["id"]: len(theme["topics"]) for theme in themes},
            "tag_titles": {tag["id"]: tag["title"] for tag in tags},
            "latest_added": max(added) if added else None, "portal": settings, "backup_case": case,
            "learning_products": [product for product in products if product["model"] in covered]}
