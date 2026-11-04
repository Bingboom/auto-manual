"""「网页说明书的定位与价值」: the manual-library home band and its internal page.

``tools/rtd_portal_assets/web_manual_value.yaml`` (schema
``hello-docs-web-manual-value/v1``) holds the copy for two audiences. The
public manuals project gets only :func:`band_context`'s public view, so the
internal copy never reaches public HTML; the private site gets the internal
band and the full page at :data:`PAGE`, which shows each theme's summary and
folds its facets and principle away. Each theme's tag is derived from its
facets' statuses, which use the 系统建设 page's vocabulary. A malformed file
fails the build, like the other engineering-owned portal assets.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from tools.rtd.system_workspace import STATUS_LABELS

PAGE = "workspace/positioning/index"
TEMPLATE = "web_manual_value.html"
SOURCE_NAME = "web_manual_value.yaml"
SCHEMA = "hello-docs-web-manual-value/v1"
FACET_STATUSES = ("available", "validated", "in_progress", "planned")
PARTIAL = ("partial", "部分可用")
_ID = re.compile(r"[a-z][a-z0-9-]*")
_REV = re.compile(r"REV-[0-9]+")


def _text(where: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{SOURCE_NAME}: {where} needs text")
    return value.strip()


def _mapping(where: str, value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{SOURCE_NAME}: {where} must be a mapping")
    return value


def _revs(where: str, value: object) -> list[str]:
    revs = [] if value is None else value
    if not isinstance(revs, list) or not all(isinstance(rev, str) and _REV.fullmatch(rev) for rev in revs):
        raise ValueError(f"{SOURCE_NAME}: {where}.revs must list REV-<n> ids")
    return revs


def theme_status(statuses: list[str]) -> tuple[str, str]:
    """A theme's (status, label): all available is 可用, any available or validated is 部分可用,
    all planned is 已规划, otherwise 建设中."""
    if all(status == "available" for status in statuses):
        return "available", STATUS_LABELS["available"]
    if any(status in ("available", "validated") for status in statuses):
        return PARTIAL
    if all(status == "planned" for status in statuses):
        return "planned", STATUS_LABELS["planned"]
    return "in_progress", STATUS_LABELS["in_progress"]


def _facet(where: str, raw: object) -> dict[str, Any]:
    facet = _mapping(where, raw)
    status = facet.get("status")
    if status not in FACET_STATUSES:
        raise ValueError(f"{SOURCE_NAME}: {where}.status must be one of {', '.join(FACET_STATUSES)}")
    revs = _revs(where, facet.get("revs"))
    if status == "planned" and not revs:
        raise ValueError(f"{SOURCE_NAME}: {where} is planned, so it names its REV")
    return {"label": _text(f"{where}.label", facet.get("label")), "status": status,
            "status_label": STATUS_LABELS[status], "note": _text(f"{where}.note", facet.get("note")),
            "revs": revs}


def _theme(where: str, raw: object, ids: set[str]) -> dict[str, Any]:
    theme = _mapping(where, raw)
    key = theme.get("id")
    if not isinstance(key, str) or not _ID.fullmatch(key) or key in ids:
        raise ValueError(f"{SOURCE_NAME}: {where} needs a unique lower-case id")
    ids.add(key)
    facets = theme.get("facets")
    if not isinstance(facets, list) or not facets:
        raise ValueError(f"{SOURCE_NAME}: {where} needs facets")
    views = [_facet(f"{where}.facets[{index}]", facet) for index, facet in enumerate(facets)]
    status, label = theme_status([facet["status"] for facet in views])
    return {"id": key, "theme": _text(f"{where}.theme", theme.get("theme")),
            "summary": _text(f"{where}.summary", theme.get("summary")),
            "principle": _text(f"{where}.principle", theme.get("principle")),
            "facets": views, "status": status, "status_label": label}


def _point(where: str, raw: object) -> dict[str, str]:
    point = _mapping(where, raw)
    return {"title": _text(f"{where}.title", point.get("title")), "text": _text(f"{where}.text", point.get("text"))}


def _public(raw: object) -> dict[str, Any]:
    public = _mapping("public", raw)
    points = public.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{SOURCE_NAME}: public.points needs entries")
    return {"lead": _text("public.lead", public.get("lead")),
            "points": [_point(f"public.points[{index}]", point) for index, point in enumerate(points)]}


def _internal(raw: object) -> dict[str, Any]:
    internal = _mapping("internal", raw)
    themes = internal.get("themes")
    if not isinstance(themes, list) or not themes:
        raise ValueError(f"{SOURCE_NAME}: internal.themes needs entries")
    ids: set[str] = set()
    view: dict[str, Any] = {key: _text(f"internal.{key}", internal.get(key))
                            for key in ("eyebrow", "heading", "subtitle", "tagline", "key_idea")}
    view["themes"] = [_theme(f"internal.themes[{index}]", theme, ids) for index, theme in enumerate(themes)]
    return view


def load_value(assets: Path) -> dict[str, Any]:
    """The validated copy. A missing or malformed file raises, which fails the build."""
    data = _mapping(SOURCE_NAME, yaml.safe_load((assets / SOURCE_NAME).read_text(encoding="utf-8")))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"{SOURCE_NAME}: schema must be {SCHEMA}")
    return {"title": _text("title", data.get("title")), "public": _public(data.get("public")),
            "internal": _internal(data.get("internal"))}


def band_context(value: dict[str, Any], *, internal: bool) -> dict[str, Any]:
    """The home band for one site role. The public role gets only the public copy and no page link."""
    if not internal:
        return {"internal": False, "title": value["title"], **value["public"]}
    band = value["internal"]
    return {"internal": True, "title": value["title"], "page": PAGE, "eyebrow": band["eyebrow"],
            "heading": band["heading"], "subtitle": band["subtitle"],
            "themes": [{"id": theme["id"], "theme": theme["theme"], "status": theme["status"],
                        "status_label": theme["status_label"],
                        "keywords": [facet["label"] for facet in theme["facets"]]}
                       for theme in band["themes"]]}


def page_context(value: dict[str, Any]) -> dict[str, Any]:
    """The internal page's context: the title plus the internal copy."""
    return {"title": value["title"], **value["internal"]}
