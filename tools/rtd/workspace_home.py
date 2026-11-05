"""知识库首页's 「现在」 block, read from the pages that own each fact.

The home page answers two questions on one screen: how things stand now, and
where to go. 「现在」 shows the 系统建设 page's current main lines and its
正在做 items (labels only, no REV ids), and three figures from 说明书工作台
(网页说明书, 语言版本, 审核中). The home page holds no numbers of its own: a
missing input shows as 无数据, and each figure links to the page that owns it.
"""
from __future__ import annotations

from typing import Any

# (overview id on 说明书工作台, label, unit)
_OVERVIEW_FIGURES = (("manuals", "网页说明书", "本"), ("variants", "语言版本", "个"))


def _lanes(system: dict[str, Any] | None) -> list[dict[str, str]]:
    focus = (system or {}).get("focus") or {}
    for group in focus.get("groups") or []:
        if group.get("horizon") == "now":
            return [{"id": lane["id"], "title": lane["title"], "goal": lane.get("goal") or ""}
                    for lane in group.get("lanes") or []]
    return []


def _figures(deliverables: dict[str, Any] | None) -> list[dict[str, Any]]:
    deliverables = deliverables or {}
    overview = {item.get("id"): item for item in (deliverables.get("production") or {}).get("overview") or []}
    figures = []
    for key, label, unit in _OVERVIEW_FIGURES:
        item = overview.get(key) or {}
        value = item.get("display") if item.get("value") is not None else None
        figures.append({"id": key, "label": label, "unit": unit, "value": value, "anchor": "deliverables"})
    reviews = ((deliverables.get("progress") or {}).get("kpis") or {}).get("reviews")
    figures.append({"id": "reviews", "label": "审核中", "unit": "本", "value": reviews,
                    "anchor": "web-progress-reviews"})
    return figures


def now_view(system: dict[str, Any] | None, deliverables: dict[str, Any] | None) -> dict[str, Any]:
    """Main lines, 正在做 labels and the three figures; empty parts are left out by the template."""
    doing = [item["label"] for item in (system or {}).get("now") or [] if item.get("label")]
    return {"lanes": _lanes(system), "doing": doing, "figures": _figures(deliverables),
            "system": system is not None}
