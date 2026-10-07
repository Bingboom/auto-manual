"""Small technical primer, linked only to products in the frozen manual catalog."""
from __future__ import annotations

import json
import re
from pathlib import Path

PAGE = "products/knowledge"
TEMPLATE = "product_knowledge.html"
_ID = re.compile(r"[a-z][a-z0-9-]*")


def _validate_topic(topic: dict, ids: set[str], tag_ids: list[str], groups: dict) -> None:
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


def learning_context(assets: Path, settings: dict, products: list[dict]) -> dict:
    curriculum = json.loads((assets / "product_knowledge.json").read_text(encoding="utf-8"))
    groups = {row["id"]: set(row["models"])
              for rows in settings.get("navigation", {}).values() for row in rows}
    tags = curriculum["tags"]
    tag_ids = [tag["id"] for tag in tags]
    if len(set(tag_ids)) != len(tag_ids) or any(not _ID.fullmatch(key) for key in tag_ids):
        raise ValueError("product knowledge tags need unique lower-case ids")
    ids = set()
    topics = []
    for topic in curriculum["topics"]:
        _validate_topic(topic, ids, tag_ids, groups)
        models = set().union(*(groups[group] for group in topic["groups"]))
        topics.append({**topic, "models": sorted(models), "references": _references(products, models)})
    return {"topics": topics, "tags": tags, "learning_products": products, "portal": settings}
