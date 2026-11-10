"""Small technical primer, linked only to products in the frozen manual catalog.

The 2026-11 layout opens on an energy-flow map and a theme map (`themes`: each tag with its topics' short
labels), then shows each topic as a card whose figure is a typical teaching circuit (a topic's optional
`circuit`, one of the portal's circuit-*.svg files), a hand-drawn diagram or the chain of its nodes, and ends
with worked product cases.

The content is business-owned: Hello-Docs `docs/knowledge/product-knowledge/` holds `topics.json` (tags and
topics) and `cases.json` (the product cases). This module, the page template and the circuits stay here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from tools.rtd.product_matrix import ProductMatrixError, positioning_groups

PAGE = "products/knowledge"
TEMPLATE = "product_knowledge.html"
CONTENT_DIR = "product-knowledge"
TOPICS = "topics.json"
CASES = "cases.json"
SCHEMA_VERSION = 1
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


def _load(knowledge_root: Path, name: str) -> dict | None:
    """One content file of the knowledge directory; None when absent, an error when malformed."""
    path = knowledge_root / CONTENT_DIR / name
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"product knowledge {name} needs schema_version {SCHEMA_VERSION}")
    return data


def load_topics(knowledge_root: Path) -> dict | None:
    """Tags and topics from the business knowledge directory, or None while it has none."""
    return _load(knowledge_root, TOPICS)


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_lesson(key: str, lesson: dict, static: Path) -> None:
    paragraphs = lesson.get("paragraphs")
    if not _text(lesson.get("title")) or not isinstance(paragraphs, list) or not paragraphs \
            or not all(_text(text) for text in paragraphs):
        raise ValueError(f"product case {key} has a lesson without a title or text")
    circuit = lesson.get("circuit")
    if circuit is not None:
        known = isinstance(circuit, dict) and _CIRCUIT.fullmatch(str(circuit.get("file"))) \
            and (static / circuit["file"]).is_file()
        if not known or not _text(circuit.get("alt")) or not _text(circuit.get("caption")):
            raise ValueError(f"product case {key} names an unknown circuit or lacks its alt or caption")
    stats = lesson.get("stats", [])
    complete = isinstance(stats, list) and all(
        isinstance(stat, dict) and all(_text(stat.get(field)) for field in ("label", "value", "note")) for stat in stats)
    if not complete:
        raise ValueError(f"product case {key} has an incomplete figure")


def _validate_case(case: dict, ids: set[str], static: Path) -> None:
    key = case.get("id")
    if not isinstance(key, str) or key in ids or not _ID.fullmatch(key):
        raise ValueError("product knowledge cases need unique lower-case ids")
    ids.add(key)
    missing = [field for field in ("model", "region", "eyebrow", "title", "source_label") if not _text(case.get(field))]
    if missing:
        raise ValueError(f"product case {key} needs {', '.join(missing)}")
    if not isinstance(case.get("intro"), str) or not isinstance(case.get("lessons"), list) or not case["lessons"]:
        raise ValueError(f"product case {key} needs intro and lessons")
    for lesson in case["lessons"]:
        _validate_lesson(key, lesson, static)


def _cases(knowledge_root: Path, static: Path, products: list[dict]) -> list[dict]:
    """The worked product cases; a case shows only while the catalog holds the manual it quotes."""
    cases, ids = [], set()
    for case in (_load(knowledge_root, CASES) or {"cases": []})["cases"]:
        _validate_case(case, ids, static)
        reference = next((ref for ref in _references(products, {case["model"]}) if ref["region"] == case["region"]),
                         None)
        if reference:
            cases.append({**case, "reference": reference})
    return cases


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


def learning_context(knowledge_root: Path, assets: Path, settings: dict, products: list[dict]) -> dict:
    """The page context. Missing content renders an empty page (``content_missing``) instead of failing;
    malformed content fails the build."""
    loaded = load_topics(knowledge_root)
    curriculum = loaded or {"tags": [], "topics": []}
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
    cases = _cases(knowledge_root, assets / "_static", products)
    placed = set().union(*groups.values()) if groups else set()
    # The selector offers only products some topic covers, so choosing one never empties the list.
    themes = _themes(tags, topics)
    added = [str(topic["added"]) for topic in topics if topic.get("added")]
    return {"topics": topics, "tags": tags, "themes": themes,
            "tag_counts": {theme["id"]: len(theme["topics"]) for theme in themes},
            "tag_titles": {tag["id"]: tag["title"] for tag in tags},
            "latest_added": max(added) if added else None, "portal": settings, "cases": cases,
            "content_missing": loaded is None, "uncovered_models": sorted(placed - covered),
            "learning_products": [product for product in products if product["model"] in covered]}
