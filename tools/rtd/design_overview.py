"""概览 tab of the 设计规范 page (the 2026-11 layout): pictures first, then the written rules.

The cover, the figures, the foundation cards, the component gallery and the icon wall show what
design_system.py has already read from the repository: colour values from the live stylesheet,
the component previews, the asset gallery, plus the HB-* semantic styles of the manual style
contract. Only the Chinese copy and the choice of what to show are committed
(design_system/content.yaml). A foundation the template cannot draw, a colour the drawings need,
or a showcased component or file that no longer exists is an authoring error, like any other
drift on this page.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.render_contract import load_render_contract, style_ids
from tools.rtd.design_content import DesignSystemError, inline
from tools.utils.path_utils import Paths

# Foundation cards design_system.html draws (macro foundation_art), by content id.
FOUNDATION_ART = frozenset({"color", "type", "layout", "shape", "depth", "image", "state"})
# Colour keys (content.yaml colors[].key) the cover and the cards paint with.
PALETTE = ("dark", "text", "muted", "line", "line_soft", "paper", "surface", "surface_strong",
           "lamp_green", "lamp_glow", "status_green", "lamp_red", "lamp_off")
# The colour card's neutral swatches, in order.
NEUTRALS = ("muted", "line", "line_soft", "surface_strong", "surface", "paper")
GALLERY_FIELDS = ("id", "title", "style_id", "preview")


def semantic_style_count(root: Path) -> int:
    """HB-* style IDs in the manual style contract, the formats' shared vocabulary."""
    return len(style_ids(load_render_contract(Paths(root=root).manual_style_contract)))


def _palette(colors: list[dict]) -> dict[str, dict]:
    keyed = {color["key"]: color for color in colors if color.get("key")}
    missing = [key for key in PALETTE if key not in keyed]
    if missing:
        raise DesignSystemError(f"design_system/content.yaml colours need the keys {missing}")
    return keyed


def _titled(entries: list, what: str) -> list[dict]:
    items = []
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("title") or not entry.get("text"):
            raise DesignSystemError(f"{what}: every entry needs a title and a text")
        items.append({"title": inline(str(entry["title"])), "text": inline(str(entry["text"]))})
    return items


def _foundations(entries: list) -> list[dict]:
    seen: set[str] = set()
    cards = []
    for entry in entries:
        key = entry.get("id") if isinstance(entry, dict) else None
        if key not in FOUNDATION_ART or key in seen:
            raise DesignSystemError(f"foundation {key}: needs a unique id the page draws, one of {sorted(FOUNDATION_ART)}")
        seen.add(key)
        cards.append({"id": key, "title": entry["title"], "card": entry["card"],
                      "caption": inline(entry["caption"]), "text": inline(entry["text"]),
                      "points": _titled(entry.get("points", []), f"foundation {key} points")})
    return cards


def _gallery(ids: list, groups: list[dict]) -> list[dict]:
    components = {item["id"]: item for group in groups for item in group["items"]}
    unknown = [key for key in ids if key not in components]
    if unknown:
        raise DesignSystemError(f"showcased components {unknown} are not on the 组件 tab")
    return [{field: components[key][field] for field in GALLERY_FIELDS} for key in ids]


def _alt(item: dict) -> str:
    return item["note"].striptags() if item.get("note") else item["name"]


def _listed(library: dict, ref: str) -> dict:
    for group in library["groups"]:
        for item in group["items"]:
            if item["ref"] == ref:
                return item
    raise DesignSystemError(f"showcased file {ref} is not in the 图标与素材 gallery")


def _icon_wall(spec: list, library: dict) -> dict[str, list]:
    groups = {group["id"]: group for group in library["groups"]}
    wall = []
    for entry in spec:
        group = groups.get(entry.get("group"))
        if group is None:
            raise DesignSystemError(f"icon wall: unknown asset group {entry.get('group')}")
        items = {item["name"]: item for item in group["items"]}
        missing = [name for name in entry["files"] if name not in items]
        if missing:
            raise DesignSystemError(f"icon wall: {group['id']} no longer lists {missing}")
        wall.append({"id": group["id"], "title": group["title"], "count": len(group["items"]),
                     "note": entry.get("note", ""),
                     "icons": [{"ref": items[name]["ref"], "alt": _alt(items[name])} for name in entry["files"]]})
    shown = {group["id"] for group in wall}
    others = [{"title": group["title"], "count": len(group["items"])}
              for group in library["groups"] if group["id"] not in shown]
    return {"groups": wall, "others": others}


def _showcase(spec: dict, groups: list[dict], library: dict) -> dict[str, Any]:
    image_art = [{"ref": _listed(library, entry["file"])["ref"], "label": entry["label"]}
                 for entry in spec.get("image_art", [])]
    return {"cover_icon": _listed(library, spec["cover_icon"])["ref"], "image_art": image_art,
            "gallery": _gallery(spec["components"], groups), "icons": _icon_wall(spec["icons"], library)}


def overview_context(content: dict, *, colors: list[dict], groups: list[dict], library: dict,
                     root: Path, font_family: str) -> dict[str, Any]:
    """What the 概览 tab and the cover show."""
    keyed = _palette(colors)
    return {
        "palette": {key: keyed[key]["value"] for key in PALETTE},
        "brand": {"value": keyed["dark"]["value"], "contrast": keyed["dark"]["contrast"],
                  "is_text": keyed["text"]["value"] == keyed["dark"]["value"]},
        "neutrals": [{"name": keyed[key]["name"], "value": keyed[key]["value"]} for key in NEUTRALS],
        "fonts": [name.strip().strip("\"'") for name in font_family.split(",") if name.strip()],
        "semantic_styles": semantic_style_count(root),
        "style": [inline(text) for text in content["style"]],
        "foundations": _foundations(content["foundations"]),
        "principles": _titled(content["principles"], "principles"),
        "usage": _titled(content["usage"], "usage"),
        **_showcase(content["showcase"], groups, library),
    }


__all__ = ["FOUNDATION_ART", "NEUTRALS", "PALETTE", "overview_context", "semantic_style_count"]
