#!/usr/bin/env python3
"""Responsive web-only composition for governed manual figures.

The source RST remains authoritative for every image and localized string.
This module consumes the generated HTML structure and applies only web
geometry: editable/searchable callouts, SVG leaders, and responsive fallbacks.
"""

from __future__ import annotations

import fnmatch
import json
import re
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from tools.utils.path_utils import PathSegments, get_paths


DOCUMENT_PRESENTATION_PROFILE = "document"
WEB_PRESENTATION_PROFILE = "web"
PRESENTATION_PROFILE_ENV = "AUTO_MANUAL_PRESENTATION_PROFILE"
WEB_CONTRACT_NAME = "web_manual.json"
WEB_STYLESHEET_NAME = "web_manual.css"
_WEB_FIGURE_RE = re.compile(
    r'<figure\b(?=[^>]*\bclass=["\'][^"\']*\bhb-(?:annotated|operation)-figure\b)'
    r"[^>]*>.*?</figure>",
    re.IGNORECASE | re.DOTALL,
)


class WebPresentationError(RuntimeError):
    """The source structure no longer satisfies the web presentation contract."""


def normalize_presentation_profile(value: str | None) -> str:
    profile = (value or DOCUMENT_PRESENTATION_PROFILE).strip().lower()
    if not profile:
        profile = DOCUMENT_PRESENTATION_PROFILE
    if profile not in {DOCUMENT_PRESENTATION_PROFILE, WEB_PRESENTATION_PROFILE}:
        raise ValueError(
            f"unsupported manual presentation profile: {value!r}; "
            f"expected {DOCUMENT_PRESENTATION_PROFILE!r} or {WEB_PRESENTATION_PROFILE!r}"
        )
    return profile


def _contract_path() -> Path:
    return get_paths().renderer_contracts_dir / WEB_CONTRACT_NAME


def _stylesheet_path() -> Path:
    return get_paths().renderer_contracts_dir / WEB_STYLESHEET_NAME


@lru_cache(maxsize=4)
def _load_contract_cached(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WebPresentationError(f"cannot load web manual contract {path}: {exc}") from exc
    if data.get("schema_version") != "web-manual-presentation/v1":
        raise WebPresentationError(f"unsupported web manual contract schema in {path}")
    return data


def load_web_manual_contract(path: Path | None = None) -> dict[str, Any]:
    contract_path = (path or _contract_path()).resolve(strict=False)
    return _load_contract_cached(str(contract_path))


def copy_web_stylesheet(destination_dir: Path) -> Path:
    source = _stylesheet_path()
    if not source.is_file():
        raise WebPresentationError(f"web manual stylesheet is missing: {source}")
    static_dir = destination_dir / PathSegments.STATIC
    static_dir.mkdir(parents=True, exist_ok=True)
    destination = static_dir / WEB_STYLESHEET_NAME
    shutil.copy2(source, destination)
    return destination


def protect_web_figures_for_pandoc(html_text: str) -> tuple[str, dict[str, str]]:
    """Replace governed figures with stable tokens before Pandoc parses HTML.

    Pandoc otherwise flattens nested callout divs and converts inline SVG into
    an image data URI. Restoring the raw figure blocks in Markdown preserves
    editable HTML copy, data attributes, and native SVG leaders for MyST.
    """
    protected: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        token = f"AUTOMANUALWEBFIGURE{len(protected) + 1:04d}PLACEHOLDER"
        protected[token] = match.group(0)
        return f"<p>{token}</p>"

    return _WEB_FIGURE_RE.sub(replace, html_text), protected


def restore_web_figures_after_pandoc(
    markdown_text: str,
    protected: dict[str, str],
) -> str:
    restored = markdown_text
    for token, figure_html in protected.items():
        occurrences = restored.count(token)
        if occurrences != 1:
            raise WebPresentationError(
                f"Pandoc web figure placeholder {token} occurred {occurrences} times; expected once"
            )
        restored = restored.replace(token, f"\n\n{figure_html}\n\n")
    return restored


def should_include_web_page(
    source_path: Path,
    *,
    contract: dict[str, Any] | None = None,
) -> bool:
    data = contract or load_web_manual_contract()
    patterns = data["profiles"][WEB_PRESENTATION_PROFILE]["excluded_source_patterns"]
    return not any(fnmatch.fnmatch(source_path.stem.lower(), str(pattern).lower()) for pattern in patterns)


def is_web_entry_page(
    source_path: Path,
    *,
    contract: dict[str, Any] | None = None,
) -> bool:
    data = contract or load_web_manual_contract()
    pattern = str(data["profiles"][WEB_PRESENTATION_PROFILE]["entry_source_pattern"])
    return fnmatch.fnmatch(source_path.stem.lower(), pattern.lower())


def _matches_source(source_path: Path, patterns: list[str]) -> bool:
    stem = source_path.stem.lower()
    return any(fnmatch.fnmatch(stem, pattern.lower()) for pattern in patterns)


def _source_target(source_path: Path) -> tuple[str, str] | None:
    parts = list(source_path.parts)
    normalized = [part.lower() for part in parts]
    for marker in (PathSegments.REVIEW, PathSegments.BUILD):
        try:
            marker_index = normalized.index(marker.lower())
        except ValueError:
            continue
        if marker_index + 2 < len(parts):
            return parts[marker_index + 1], parts[marker_index + 2]
    return None


def _supports_figure_contract(source_path: Path, contract: dict[str, Any]) -> bool:
    target = _source_target(source_path)
    if target is None:
        return False
    model, region = target
    return any(
        model.casefold() == str(selector["model"]).casefold()
        and region.casefold() == str(selector["region"]).casefold()
        for selector in contract["figure_targets"]
    )


def _src_matches_key(src: str, image_key: str) -> bool:
    normalized_src = src.replace("\\", "/").lower()
    normalized_key = image_key.replace("\\", "/").lower()
    return normalized_key in normalized_src or normalized_key.rsplit("/", 1)[-1] in normalized_src


def _table_rows(table: Tag) -> list[list[Tag]]:
    rows: list[list[Tag]] = []
    for row in table.find_all("tr"):
        cells = [cell for cell in row.find_all("td", recursive=False) if isinstance(cell, Tag)]
        if cells:
            rows.append(cells)
    return rows


def _cell_markup(cell: Tag | None) -> str:
    if cell is None or not cell.get_text(" ", strip=True):
        return ""
    return cell.decode_contents().strip()


def _front_callout_markup(section: Tag) -> dict[str, str]:
    tables = section.find_all("table", recursive=False)
    if len(tables) < 2:
        return {}
    primary = _table_rows(tables[0])
    total_rows = _table_rows(tables[1])

    def at(row: int, column: int) -> Tag | None:
        if row >= len(primary) or column >= len(primary[row]):
            return None
        return primary[row][column]

    left = [at(row, 0) for row in (0, 1, 3, 4, 5, 2)]
    right = [
        at(row, 1)
        for row in range(len(primary))
        if at(row, 1) is not None and _cell_markup(at(row, 1))
    ]
    right.extend([None] * max(0, 5 - len(right)))
    result: dict[str, str] = {}
    semantic_order = (
        ("power", left[0]),
        ("lcd", right[0]),
        ("dc12", left[1]),
        ("led_button", right[1]),
        ("usb_c_30", left[2]),
        ("led", right[2]),
        ("usb_c_100", left[3]),
        ("ac_power", right[3]),
        ("usb_a", left[4]),
        ("ac_output", right[4]),
        ("dc_usb", left[5]),
        ("total", total_rows[0][0] if total_rows and total_rows[0] else None),
    )
    for semantic_id, cell in semantic_order:
        result[semantic_id] = _cell_markup(cell)
    return result


def _right_callout_markup(section: Tag) -> dict[str, str]:
    table = section.find("table", recursive=False)
    if not isinstance(table, Tag):
        return {}
    cells = [
        cell
        for row in _table_rows(table)
        for cell in row
        if _cell_markup(cell)
    ]
    if len(cells) < 3:
        return {}
    return {
        "handle": _cell_markup(cells[0]),
        "dc_input": _cell_markup(cells[2]),
        "ac_input": _cell_markup(cells[1]),
    }


def _append_markup(target: Tag, markup: str) -> None:
    parsed = BeautifulSoup(markup, "html.parser")
    for child in list(parsed.contents):
        target.append(child.extract())


def _points_text(points: list[list[float]]) -> str:
    return " ".join(f"{float(x):g},{float(y):g}" for x, y in points)


def _leader_layer(soup: BeautifulSoup, view: dict[str, Any]) -> Tag:
    svg = soup.new_tag(
        "svg",
        attrs={
            "class": "hb-leader-layer",
            "viewBox": "0 0 100 100",
            "preserveAspectRatio": "none",
            "aria-hidden": "true",
            "focusable": "false",
        },
    )
    for callout in view["callouts"]:
        polyline = soup.new_tag(
            "polyline",
            attrs={
                "class": "hb-leader",
                "data-callout-id": f"overview.{view['id']}.{callout['id']}",
                "points": _points_text(callout["leader"]),
            },
        )
        svg.append(polyline)
    for index, points in enumerate(view.get("decorative_leaders", []), start=1):
        polyline = soup.new_tag(
            "polyline",
            attrs={
                "class": "hb-leader-decoration",
                "data-decoration-id": f"overview.{view['id']}.decoration-{index}",
                "points": _points_text(points),
            },
        )
        svg.append(polyline)
    return svg


def _overview_figure(
    soup: BeautifulSoup,
    *,
    section: Tag,
    image: Tag,
    view: dict[str, Any],
    source_path: Path,
) -> Tag:
    markup = _front_callout_markup(section) if view["id"] == "front" else _right_callout_markup(section)
    required_ids = [str(item["id"]) for item in view["callouts"]]
    missing = [semantic_id for semantic_id in required_ids if not markup.get(semantic_id)]
    if missing:
        raise WebPresentationError(
            f"{source_path}: product overview {view['id']} is missing semantic callouts: "
            + ", ".join(missing)
        )

    figure = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-annotated-figure",
            "data-figure-id": f"product-overview-{view['id']}",
        },
    )
    stage = soup.new_tag(
        "div",
        attrs={
            "class": "hb-annotated-stage",
            "style": f"--hb-aspect-ratio:{float(view['aspect_ratio']):g}",
        },
    )
    image["class"] = [*image.get("class", []), "hb-annotated-art"]
    image.replace_with(figure)
    stage.append(image)
    stage.append(_leader_layer(soup, view))

    for item in view["callouts"]:
        semantic_id = str(item["id"])
        x, y, width, height = (float(value) for value in item["rect"])
        align = str(item["align"])
        callout = soup.new_tag(
            "div",
            attrs={
                "class": ["hb-figure-callout", f"hb-align-{align}"],
                "data-callout-id": f"overview.{view['id']}.{semantic_id}",
                "style": (
                    f"--hb-x:{x:g}%;--hb-y:{y:g}%;--hb-width:{width:g}%;"
                    f"--hb-height:{height:g}%;--hb-align:{align}"
                ),
            },
        )
        _append_markup(callout, markup[semantic_id])
        stage.append(callout)
    figure.append(stage)
    return figure


def _transform_product_overview(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
) -> None:
    overview = contract["product_overview"]
    transformed: list[str] = []
    for view in overview["views"]:
        image = next(
            (
                candidate
                for candidate in soup.find_all("img")
                if _src_matches_key(str(candidate.get("src", "")), str(view["image_key"]))
            ),
            None,
        )
        if not isinstance(image, Tag):
            raise WebPresentationError(
                f"{source_path}: product overview is missing governed image {view['image_key']}"
            )
        section = image.find_parent("section")
        if not isinstance(section, Tag):
            raise WebPresentationError(f"{source_path}: overview image is not contained by a section")
        _overview_figure(
            soup,
            section=section,
            image=image,
            view=view,
            source_path=source_path,
        )
        for table in list(section.find_all("table", recursive=False)):
            table.decompose()
        transformed.append(str(view["id"]))
    if len(transformed) != len(overview["views"]):
        raise WebPresentationError(f"{source_path}: incomplete product overview transformation")


def _next_tag_sibling(tag: Tag) -> Tag | None:
    sibling = tag.next_sibling
    while sibling is not None:
        if isinstance(sibling, Tag):
            return sibling
        sibling = sibling.next_sibling
    return None


def _previous_tag_sibling(tag: Tag) -> Tag | None:
    sibling = tag.previous_sibling
    while sibling is not None:
        if isinstance(sibling, Tag):
            return sibling
        sibling = sibling.previous_sibling
    return None


def _position_style(rect: list[float] | None) -> str | None:
    if not rect:
        return None
    x, y, width, height = (float(value) for value in rect)
    return (
        f"--hb-x:{x:g}%;--hb-y:{y:g}%;--hb-width:{width:g}%;"
        f"--hb-height:{height:g}%"
    )


def _is_strong_label_line(line: Tag) -> bool:
    strong = line.find("strong")
    return isinstance(strong, Tag) and line.get_text(" ", strip=True) == strong.get_text(
        " ", strip=True
    )


def _extract_semantic_steps(
    soup: BeautifulSoup,
    *,
    line_block: Tag,
    operation_id: str,
    step_ids: list[str],
    source_path: Path,
) -> Tag:
    lines = [
        line
        for line in line_block.find_all(class_="line", recursive=False)
        if isinstance(line, Tag)
    ]
    if len(lines) < len(step_ids):
        raise WebPresentationError(
            f"{source_path}: operation {operation_id} has {len(lines)} step lines; "
            f"expected at least {len(step_ids)}"
        )

    pair_count = len(step_ids) * 2
    uses_label_instruction_pairs = len(lines) >= pair_count and all(
        _is_strong_label_line(lines[index * 2]) for index in range(len(step_ids))
    )
    lines_per_step = 2 if uses_label_instruction_pairs else 1

    attrs = {key: value for key, value in line_block.attrs.items() if key != "class"}
    attrs.update(
        {
            "class": [*line_block.get("class", []), "hb-operation-steps"],
            "data-callout-id": f"operation.{operation_id}.steps",
        }
    )
    overlay = soup.new_tag(line_block.name, attrs=attrs)
    for index, semantic_id in enumerate(step_ids):
        start = index * lines_per_step
        group_lines = lines[start : start + lines_per_step]
        step = soup.new_tag(
            "div",
            attrs={
                "class": "hb-operation-step",
                "data-step-id": semantic_id,
                "data-callout-id": f"operation.{operation_id}.{semantic_id}",
            },
        )
        for part_index, line in enumerate(group_lines):
            line["data-step-id"] = semantic_id
            line["data-step-part"] = (
                ("label", "instruction")[part_index]
                if uses_label_instruction_pairs
                else "summary"
            )
            step.append(line.extract())
        overlay.append(step)

    if not line_block.find(class_="line", recursive=False) and not line_block.get_text(
        " ", strip=True
    ):
        line_block.decompose()
    return overlay


def _transform_operation_figure(
    soup: BeautifulSoup,
    *,
    image: Tag,
    spec: dict[str, Any],
    source_path: Path,
) -> None:
    operation_id = str(spec["id"])
    section = image.find_parent("section")
    if not isinstance(section, Tag):
        raise WebPresentationError(f"{source_path}: operation {operation_id} image has no section")
    steps = _next_tag_sibling(image)
    if not isinstance(steps, Tag) or "line-block" not in steps.get("class", []):
        raise WebPresentationError(
            f"{source_path}: operation {operation_id} image must be followed by a line-block"
        )
    prerequisite: Tag | None = None
    if spec.get("capture_prerequisite"):
        candidate = _previous_tag_sibling(image)
        if not isinstance(candidate, Tag) or candidate.name != "p":
            raise WebPresentationError(
                f"{source_path}: operation {operation_id} is missing its prerequisite paragraph"
            )
        prerequisite = candidate

    figure = soup.new_tag(
        "figure",
        attrs={
            "class": ["hb-operation-figure", f"hb-operation-layout-{spec['layout']}"],
            "data-operation-id": operation_id,
        },
    )
    stage = soup.new_tag("div", attrs={"class": "hb-operation-stage"})
    image["class"] = [*image.get("class", []), "hb-operation-art"]
    image.replace_with(figure)
    stage.append(image)

    step_ids = [str(step_id) for step_id in spec["step_ids"]]
    steps_overlay = _extract_semantic_steps(
        soup,
        line_block=steps,
        operation_id=operation_id,
        step_ids=step_ids,
        source_path=source_path,
    )

    if prerequisite is not None:
        prerequisite_overlay = soup.new_tag(
            "div",
            attrs={
                "class": "hb-operation-prerequisite",
                "data-callout-id": f"operation.{operation_id}.prerequisite",
            },
        )
        prereq_style = _position_style(spec.get("prerequisite_rect"))
        if prereq_style:
            prerequisite_overlay["style"] = prereq_style
        prerequisite_overlay.append(prerequisite.extract())
        stage.append(prerequisite_overlay)

    steps_style = _position_style(spec.get("steps_rect"))
    if steps_style:
        steps_overlay["style"] = steps_style
    stage.append(steps_overlay)
    figure.append(stage)


def _transform_operations(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
) -> None:
    figures = contract["operations"]["figures"]
    for spec in figures:
        image = next(
            (
                candidate
                for candidate in soup.find_all("img")
                if _src_matches_key(str(candidate.get("src", "")), str(spec["image_key"]))
            ),
            None,
        )
        if not isinstance(image, Tag):
            raise WebPresentationError(
                f"{source_path}: operation page is missing governed image {spec['image_key']}"
            )
        _transform_operation_figure(
            soup,
            image=image,
            spec=spec,
            source_path=source_path,
        )


def transform_web_fragment(
    html_fragment: str,
    *,
    source_path: Path,
    contract: dict[str, Any] | None = None,
) -> str:
    """Apply web composition to governed figure pages; leave other pages byte-identical."""
    data = contract or load_web_manual_contract()
    overview = data["product_overview"]
    operations = data["operations"]
    is_overview = _matches_source(source_path, list(overview["source_patterns"]))
    is_operations = _matches_source(source_path, list(operations["source_patterns"]))
    if not (is_overview or is_operations):
        return html_fragment
    if not _supports_figure_contract(source_path, data):
        return html_fragment

    soup = BeautifulSoup(html_fragment, "html.parser")
    if is_overview:
        _transform_product_overview(soup, source_path=source_path, contract=data)
    if is_operations:
        _transform_operations(soup, source_path=source_path, contract=data)
    return str(soup)


__all__ = [
    "DOCUMENT_PRESENTATION_PROFILE",
    "PRESENTATION_PROFILE_ENV",
    "WEB_PRESENTATION_PROFILE",
    "WEB_STYLESHEET_NAME",
    "WebPresentationError",
    "copy_web_stylesheet",
    "is_web_entry_page",
    "load_web_manual_contract",
    "normalize_presentation_profile",
    "protect_web_figures_for_pandoc",
    "restore_web_figures_after_pandoc",
    "should_include_web_page",
    "transform_web_fragment",
]
