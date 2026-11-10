"""Read-only 设计规范 page: the live Web stylesheet, asset library and print tokens.

Colours, type and component previews are read from the web_manual.css that
tools/web/stylesheets.py assembles, the 图标与素材 gallery from the shared asset
folders and manifests (design_assets.py), the 印刷规格 tab from
data/layout_params.csv (design_print.py), and the 概览 tab and cover from all of
these (design_overview.py), all at build time; only the Chinese notes and the
preview markup are committed data
(tools/rtd_portal_assets/design_system/). A selector, class, asset or token the
page relies on that no longer exists is an authoring error: the page is skipped
with a warning rather than showing stale rules, and the unit tests fail first.
"""
from __future__ import annotations

import hashlib
from html import escape
from pathlib import Path
import re
import shutil
from typing import Any

import yaml

from tools.rtd.design_assets import GROUNDS, asset_gallery, asset_source, check_not_withdrawn, withdrawn_hashes
from tools.rtd.design_content import CONTENT_DIR, DesignSystemError, inline, load_content
from tools.rtd.design_overview import overview_context
from tools.rtd.design_print import print_page_document, print_spec
from tools.rtd.design_system_css import class_names, declared, live_stylesheet_text, parse_css
from tools.utils.path_utils import Paths, repo_root

PAGE = "workspace/design/index"
TEMPLATE = "design_system.html"
OUTPUT_DIR = "workspace/design"
MOBILE = "@media (max-width: 760px)"
TYPE_PROPERTIES = ("font-size", "line-height", "font-weight", "text-transform", "letter-spacing")
# Portal stylesheets (tools/rtd_portal_assets/_static) a preview may add.
PORTAL_STYLESHEETS = frozenset({"manual-locales.css"})
# A component's 样式定义 link opens its HB-* entry in the manual style contract here.
ENGINEERING = "https://github.com/Bingboom/auto-manual"
# The WCAG mark a colour row carries, strongest first: (minimum contrast on paper, id, label).
CONTRAST_GRADES = ((7.0, "aaa", "AAA"), (4.5, "aa", "AA"), (3.0, "large", "大字 AA"), (0.0, "decor", "装饰"))

_ASSET = re.compile(r'src="asset:([a-z]+)/([A-Za-z0-9][A-Za-z0-9._-]*)"')
_SLOT = re.compile(r'src="slot:(\d{2,4}):(\d{2,4}):([^"<>&]+)"')
_HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_ID = re.compile(r"[a-z][a-z0-9-]*")
_FIRST_CLASS = re.compile(r"\.[a-z][a-z0-9-]*")
_STYLE_ID = re.compile(r"HB-[A-Z0-9-]+")
_STYLE_LINE = re.compile(r"  (HB-[A-Z0-9-]+):\s*")


def _luminance(hex_color: str) -> float:
    digits = hex_color[1:]
    if len(digits) == 3:
        digits = "".join(char * 2 for char in digits)
    channels = [int(digits[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(color: str, ground: str) -> float | None:
    """WCAG contrast of two opaque hex colours; None for a translucent colour."""
    if len(color) == 9 or len(ground) == 9:
        return None
    lighter, darker = sorted((_luminance(color), _luminance(ground)), reverse=True)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def contrast_grade(ratio: float | None) -> dict[str, str]:
    """AAA, AA, 大字 AA, 装饰 below 3:1, or 半透明 for a translucent colour without a ratio."""
    if ratio is None:
        return {"id": "alpha", "label": "半透明"}
    return next({"id": key, "label": label} for floor, key, label in CONTRAST_GRADES if ratio >= floor)


def _color_label(selector: str, prop: str) -> str:
    """What a colour row names: its custom property, else `property · first class` of its selector."""
    match = _FIRST_CLASS.search(selector)
    return prop if prop.startswith("--") or match is None else f"{prop} · {match.group(0)}"


def _root_color(rules: list, token: str) -> str:
    match = _HEX.search(declared(rules, ":root", token) or "")
    if match is None:
        raise DesignSystemError(f"the live stylesheet no longer declares {token}")
    return match.group(0).lower()


def _colors(content: dict, rules: list, paper: str) -> list[dict]:
    colors = []
    for index, entry in enumerate(content["colors"], start=1):
        if "token" in entry:
            selector, prop = ":root", entry["token"]
        else:
            selector, prop = entry["selector"], entry["property"]
        raw = declared(rules, selector, prop)
        match = _HEX.search(raw or "")
        if match is None:
            raise DesignSystemError(f"colour {entry['name']}: {selector} no longer declares {prop}")
        if entry.get("group") not in content["color_groups"]:
            raise DesignSystemError(f"colour {entry['name']}: group must be one of {sorted(content['color_groups'])}")
        value = match.group(0).lower()
        contrast = contrast_ratio(value, paper)
        # The paper is what every ratio is measured against, not a colour on it.
        grade = {"id": "ground", "label": "底色"} if value == paper else contrast_grade(contrast)
        colors.append({
            "name": entry["name"], "key": entry.get("key"), "token": prop, "selector": selector, "declared": raw,
            "value": value, "contrast": contrast, "grade": grade, "note": inline(entry["note"]),
            "group": entry["group"], "index": index, "label": _color_label(selector, prop),
        })
    return colors


def color_groups(content: dict, colors: list[dict], print_colors: list[dict]) -> list[dict]:
    """The 颜色 tables in content order; each colour lists the print swatches whose screen colour it is."""
    inks: dict[str, list[dict]] = {}
    for ink in print_colors:
        if ink["screen"]:
            inks.setdefault(ink["screen"], []).append(ink)
    groups = []
    for key, title in content["color_groups"].items():
        members = [{**color, "inks": inks.get(color["token"], [])} for color in colors if color["group"] == key]
        if not members:
            raise DesignSystemError(f"colour group {key} lists no colour")
        groups.append({"id": key, "title": title, "colors": members})
    return groups


def _type_styles(content: dict, rules: list) -> list[dict]:
    styles = []
    for entry in content["type_styles"]:
        desktop = {prop: declared(rules, entry["selector"], prop) for prop in TYPE_PROPERTIES}
        if desktop["font-size"] is None and desktop["font-weight"] is None:
            raise DesignSystemError(f"type style {entry['name']}: {entry['selector']} sets no font size or weight")
        mobile = {prop: declared(rules, entry["selector"], prop, context=MOBILE)
                  for prop in ("font-size", "line-height")}
        sample_style = ";".join(f"{prop}:{value}" for prop, value in desktop.items() if value)
        styles.append({
            "name": entry["name"], "label": entry["label"], "selector": entry["selector"],
            "sample": entry["sample"], "note": inline(entry["note"]),
            "desktop": desktop, "mobile": {k: v for k, v in mobile.items() if v},
            "sample_style": sample_style,
        })
    return styles


def _slot_svg(width: int, height: int, label: str) -> str:
    size = max(11, min(width, height) // 22)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="#f4f3f3" '
        'stroke="#a7a5a6" stroke-width="1.5" stroke-dasharray="6 5"/>'
        f'<text x="{width / 2:g}" y="{height / 2 + 5:g}" font-family="sans-serif" font-size="{size}" '
        f'text-anchor="middle" fill="#666264">{escape(label)}</text></svg>\n'
    )


def _resolve_markup(fragment: str, root: Path, used_assets: dict, slots: dict) -> str:
    def asset(match: re.Match) -> str:
        group, name = match.groups()
        used_assets[f"{group}/{name}"] = asset_source(root, group, name)
        return f'src="../assets/{group}/{name}"'

    def slot(match: re.Match) -> str:
        width, height, label = int(match.group(1)), int(match.group(2)), match.group(3)
        svg = _slot_svg(width, height, label)
        name = "slot-" + hashlib.sha256(svg.encode("utf-8")).hexdigest()[:12] + ".svg"
        slots[name] = svg
        return f'src="../slots/{name}"'

    resolved = _SLOT.sub(slot, _ASSET.sub(asset, fragment))
    if re.search(r'(?:src|href)="(?:asset:|slot:|https?:|//|data:)', resolved):
        raise DesignSystemError("preview markup may only use repository assets and placeholders")
    return resolved


def _components(content: dict, assets: Path, root: Path, styled: set[str], selectors: set[str],
                used_assets: dict, slots: dict) -> list[dict]:
    groups = {group["id"]: {"id": group["id"], "title": group["title"], "items": []}
              for group in content["component_groups"]}
    seen = set()
    for entry in content["components"]:
        key = entry["id"]
        if not _ID.fullmatch(key) or key in seen or entry["group"] not in groups:
            raise DesignSystemError(f"component {key}: needs a unique id and a known group")
        seen.add(key)
        for requirement in entry["requires"]:
            present = (requirement[1:] in styled) if requirement.startswith(".") else (requirement in selectors)
            if not present:
                raise DesignSystemError(f"component {key}: the live stylesheet no longer styles {requirement}")
        unknown = set(entry.get("stylesheets", [])) - PORTAL_STYLESHEETS
        if unknown:
            raise DesignSystemError(f"component {key}: unknown preview stylesheets {sorted(unknown)}")
        source = assets / CONTENT_DIR / "previews" / f"{key}.html"
        refs: dict[str, Path] = {}
        markup = _resolve_markup(source.read_text(encoding="utf-8"), root, refs, slots)
        used_assets.update(refs)
        groups[entry["group"]]["items"].append({
            "id": key, "group": entry["group"], "title": entry["title"], "style_id": entry["style_id"],
            "refs": sorted(refs),
            "height": int(entry["height"]), "stage": entry.get("stage", "stage"),
            "stylesheets": list(entry.get("stylesheets", [])), "markup": markup,
            "preview": f"previews/{key}.html",
            "notes": [(label, inline(entry[field])) for field, label in
                      (("use", "用法"), ("provide", "需要提供"), ("avoid", "不要"))
                      if entry.get(field)],
            "summary": inline(entry["summary"]),
        })
    return [group for group in groups.values() if group["items"]]


def _link_styles(groups: list[dict], root: Path) -> None:
    """Point each component's 样式定义 link at its first HB-* ID's entry in the manual style contract.

    A component named by a role (页面容器, 来源状态表) has no link; an HB-* ID the contract
    no longer defines is drift.
    """
    contract = Paths(root=root).manual_style_contract
    lines: dict[str, int] = {}
    for number, line in enumerate(contract.read_text(encoding="utf-8").splitlines(), start=1):
        match = _STYLE_LINE.fullmatch(line)
        if match:
            lines.setdefault(match.group(1), number)
    page = f"{ENGINEERING}/blob/main/{contract.relative_to(root).as_posix()}"
    for item in (item for group in groups for item in group["items"]):
        match = _STYLE_ID.match(item["style_id"])
        if match and match.group(0) not in lines:
            raise DesignSystemError(f"component {item['id']}: {match.group(0)} is not in the manual style contract")
        item["style_href"] = f"{page}#L{lines[match.group(0)]}" if match else None


def _mark_uses(library: dict, groups: list[dict]) -> None:
    """Give each asset tile the components whose previews show it (用在)."""
    users: dict[str, list[str]] = {}
    for item in (item for group in groups for item in group["items"]):
        for ref in item["refs"]:
            users.setdefault(ref, []).append(item["title"])
    for asset in (asset for group in library["groups"] for asset in group["items"]):
        asset["used_in"] = users.get(asset["ref"], [])


def design_system_context(assets: Path) -> dict[str, Any]:
    """Build the page context from committed notes and the live repository files."""
    content = load_content(assets)
    root = repo_root()
    css = live_stylesheet_text()
    rules = parse_css(css)
    portal_rules = parse_css((assets / "_static" / "manual-locales.css").read_text(encoding="utf-8"))
    styled = class_names(rules) | class_names(portal_rules)
    selectors = {selector for rule in rules + portal_rules for selector in rule.selectors}
    grounds = {name: _root_color(rules, token) for name, token in GROUNDS.items()}
    paper = grounds["paper"]
    used_assets: dict[str, Path] = {}
    slots: dict[str, str] = {}
    groups = _components(content, assets, root, styled, selectors, used_assets, slots)
    _link_styles(groups, root)
    library = asset_gallery(content, root, used_assets)
    _mark_uses(library, groups)
    check_not_withdrawn(used_assets, withdrawn_hashes(root))
    colors = _colors(content, rules, paper)
    type_styles = _type_styles(content, rules)
    font_family = declared(rules, ":root", "--hb-font-family") or ""
    screen_tokens = {prop for rule in rules if ":root" in rule.selectors for prop in rule.declarations}
    printed = print_spec(content, assets, root, font_family=font_family, screen_tokens=screen_tokens)
    overview = overview_context(content, colors=colors, groups=groups, library=library, root=root,
                                font_family=font_family)
    return {
        "lead": content["lead"], "overview": overview,
        "colors": colors, "color_groups": color_groups(content, colors, printed["colors"]),
        "type_styles": type_styles, "component_groups": groups, "paper": paper, "grounds": grounds,
        "component_count": sum(len(group["items"]) for group in groups),
        "font_family": font_family, "asset_library": library, "print": printed,
        "stylesheet": {"sha256": hashlib.sha256(css.encode("utf-8")).hexdigest(), "text": css},
        "assets": used_assets, "slots": slots,
    }


def template_context(context: dict[str, Any]) -> dict[str, Any]:
    """What the page template reads: no file paths, no stylesheet or preview text."""
    page = {key: value for key, value in context.items() if key not in {"assets", "slots", "stylesheet"}}
    page["stylesheet_sha256"] = context["stylesheet"]["sha256"]
    page["print"] = {key: value for key, value in context["print"].items() if key not in {"tokens_css", "preview"}}
    return page


def design_page_context(app, assets: Path) -> dict[str, Any] | None:
    """Context for PAGE, or None (with a warning) when the data has drifted."""
    from sphinx.util import logging as sphinx_logging

    # DesignSystemError is a ValueError; the others are malformed notes or unreadable files.
    try:
        return design_system_context(assets)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, yaml.YAMLError) as exc:
        sphinx_logging.getLogger(__name__).warning("Design system page skipped: %s", exc)
        return None


def preview_document(item: dict) -> str:
    links = ['<link rel="stylesheet" href="../web_manual.css">']
    links += [f'<link rel="stylesheet" href="../../../_static/{name}">' for name in item["stylesheets"]]
    links.append('<link rel="stylesheet" href="../preview.css">')
    stage = ' class="ds-stage"' if item["stage"] == "stage" else ""
    body = "ds-preview ds-preview-sheet" if item["stage"] == "sheet" else "ds-preview"
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="robots" content="noindex,nofollow">\n'
        f'<title>{escape(item["title"])} · 设计规范预览</title>\n' + "\n".join(links) + "\n</head>\n"
        f'<body class="{body}">\n<main id="furo-main-content"{stage}>\n{item["markup"]}</main>\n</body>\n</html>\n'
    )


def write_design_system(output_root: Path, assets: Path, context: dict[str, Any]) -> Path:
    """Write the previews, the live stylesheet, the print preview and the art beside the page."""
    target = output_root / OUTPUT_DIR
    (target / "previews").mkdir(parents=True, exist_ok=True)
    (target / "web_manual.css").write_text(context["stylesheet"]["text"], encoding="utf-8")
    shutil.copyfile(assets / CONTENT_DIR / "preview.css", target / "preview.css")
    for group in context["component_groups"]:
        for item in group["items"]:
            (target / item["preview"]).write_text(preview_document(item), encoding="utf-8")
    for relative, source in context["assets"].items():
        destination = target / "assets" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    if context["slots"]:
        (target / "slots").mkdir(exist_ok=True)
        for name, svg in context["slots"].items():
            (target / "slots" / name).write_text(svg, encoding="utf-8")
    printed, preview = target / "print", context["print"]["preview"]
    printed.mkdir(exist_ok=True)
    (printed / "tokens.css").write_text(context["print"]["tokens_css"], encoding="utf-8")
    (printed / "page.css").write_text(preview["css"], encoding="utf-8")
    (printed / "page.html").write_text(print_page_document(preview["markup"]), encoding="utf-8")
    return target


__all__ = [
    "DesignSystemError", "OUTPUT_DIR", "PAGE", "TEMPLATE", "color_groups", "contrast_grade", "contrast_ratio",
    "design_page_context", "design_system_context", "inline", "preview_document", "template_context",
    "write_design_system",
]
