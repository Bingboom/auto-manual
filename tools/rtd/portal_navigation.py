"""Homepage navigation: published manuals grouped by the power need they serve.

The grouping is product positioning curated in ``settings.json`` under
``navigation``; this module never infers it. Each published product lands in
exactly one group. A model the table does not list yet goes to a visible
"other" group instead of disappearing, and a listed model that has no published
manual in a region simply leaves that group smaller there.
"""
from __future__ import annotations

import re

OTHER = {"id": "other", "title": "其他说明书", "note": "尚未归入以上分组的产品", "models": []}
_ID = re.compile(r"[a-z][a-z0-9_-]*")


def _groups(rows: object, field: str, *, with_note: bool) -> list[dict]:
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"navigation.{field} must be a non-empty list")
    groups = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"navigation.{field} rows must be objects")
        keys = ("id", "title", "note") if with_note else ("id", "title")
        values = {key: row.get(key) for key in keys}
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise ValueError(f"navigation.{field} rows need {', '.join(keys)}")
        if not _ID.fullmatch(values["id"]):
            raise ValueError(f"navigation id must be lower-case: {values['id']}")
        models = row.get("models")
        if not isinstance(models, list) or not models or any(
                not isinstance(model, str) or not model.strip() for model in models):
            raise ValueError(f"navigation group {values['id']} needs models")
        groups.append({**values, "note": values.get("note", ""), "models": list(models)})
    return groups


def navigation_view(settings: dict, products: list[dict]) -> dict | None:
    """Assign every product to one need or ecosystem group; None when not configured."""
    config = settings.get("navigation")
    if config is None:
        return None
    if not isinstance(config, dict):
        raise ValueError("navigation must be an object")
    needs = _groups(config.get("needs"), "needs", with_note=True)
    ecosystem = _groups(config.get("ecosystem"), "ecosystem", with_note=False)
    owner: dict[str, str] = {}
    rank: dict[str, int] = {}
    ids = set()
    for group in needs + ecosystem + [OTHER]:
        if group["id"] in ids:
            raise ValueError(f"duplicate navigation id: {group['id']}")
        ids.add(group["id"])
        for model in group["models"]:
            if model in owner:
                raise ValueError(f"model listed in two navigation groups: {model}")
            owner[model] = group["id"]
            rank[model] = len(rank)
    for product in products:
        product["nav"] = owner.get(product["model"], OTHER["id"])
        product["nav_rank"] = rank.get(product["model"], len(rank))
    other = {**OTHER, "models": sorted({p["model"] for p in products if p["nav"] == OTHER["id"]})}
    return {"needs": needs, "ecosystem": ecosystem, "other": other if other["models"] else None}
