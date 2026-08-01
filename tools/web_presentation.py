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
from functools import lru_cache
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from tools.utils.path_utils import PathSegments, get_paths
from tools.web_reference_components import (
    append_reference_captions,
    prepare_reference_caption_data,
    transform_app_add_device,
)
from tools.web_stylesheets import WEB_STYLESHEET_NAME, copy_web_stylesheet


DOCUMENT_PRESENTATION_PROFILE = "document"
WEB_PRESENTATION_PROFILE = "web"
PRESENTATION_PROFILE_ENV = "AUTO_MANUAL_PRESENTATION_PROFILE"
WEB_CONTRACT_NAME = "web_manual.json"
_WEB_FIGURE_RE = re.compile(
    r'<figure\b(?=[^>]*\bclass=["\'][^"\']*\bhb-'
    r'(?:(?:annotated|operation|reference)-figure|inbox-composition|app-(?:add-device|download)-composition|fcc-composition|lcd-table-composition|lcd-mode-composition|auto-resume-composition|symbol-pair-composition|troubleshooting-composition|spec-table-composition|warranty-intro-composition|warranty-card|warranty-period-card)\b)'
    r"[^>]*>.*?</figure>",
    re.IGNORECASE | re.DOTALL,
)
_WEB_CALLOUT_TABLE_RE = re.compile(
    r'<table\b(?=[^>]*\bclass=["\'][^"\']*\bmanual-callout-table\b)'
    r"[^>]*>.*?</table>",
    re.IGNORECASE | re.DOTALL,
)
_WEB_INLINE_CONTROL_RE = re.compile(
    r"(?:"
    r'<span\b(?=[^>]*\bclass=["\'][^"\']*\bhb-inline-add-device-icon\b)'
    r"[^>]*>.*?</span>"
    r"|<sub\b[^>]*>.*?</sub>"
    r"|<sup\b[^>]*>.*?</sup>"
    r")",
    re.IGNORECASE | re.DOTALL,
)
_CIRCLED_REFERENCE_RE = re.compile(r"[\u2460-\u2473]")


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


def protect_web_callouts_for_pandoc(html_text: str) -> tuple[str, dict[str, str]]:
    """Replace semantic callout tables with stable tokens before Pandoc parses HTML.

    Without this guard, Pandoc can convert plain callouts into pipe tables while
    leaving callouts with richer body markup as raw HTML. That content-dependent
    split drops the semantic classes, creates empty table headers, and can inject
    a 50/50 colgroup. Restoring the original table keeps every signal type on the
    same ``manual-callout-*`` component contract.
    """
    protected: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        token = f"AUTOMANUALWEBCALLOUT{len(protected) + 1:04d}PLACEHOLDER"
        protected[token] = match.group(0)
        return f"<p>{token}</p>"

    return _WEB_CALLOUT_TABLE_RE.sub(replace, html_text), protected


def restore_web_callouts_after_pandoc(
    markdown_text: str,
    protected: dict[str, str],
) -> str:
    """Restore each protected callout exactly once, failing closed on drift."""
    restored = markdown_text
    for token, callout_html in protected.items():
        occurrences = restored.count(token)
        if occurrences != 1:
            raise WebPresentationError(
                f"Pandoc web callout placeholder {token} occurred {occurrences} times; "
                "expected once"
            )
        restored = restored.replace(token, f"\n\n{callout_html}\n\n")
    return restored


def protect_web_inline_controls_for_pandoc(html_text: str) -> tuple[str, dict[str, str]]:
    """Protect inline UI glyphs and semantic sub/superscripts from Pandoc flattening."""
    protected: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        token = f"AUTOMANUALWEBINLINE{len(protected) + 1:04d}PLACEHOLDER"
        protected[token] = match.group(0)
        return token

    return _WEB_INLINE_CONTROL_RE.sub(replace, html_text), protected


def restore_web_inline_controls_after_pandoc(
    markdown_text: str,
    protected: dict[str, str],
) -> str:
    """Restore each protected inline semantic at its original sentence position."""
    restored = markdown_text
    for token, control_html in protected.items():
        occurrences = restored.count(token)
        if occurrences != 1:
            raise WebPresentationError(
                f"Pandoc web inline placeholder {token} occurred {occurrences} times; "
                "expected once"
            )
        restored = restored.replace(token, control_html)
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


def _composite_artwork_path(component: dict[str, Any], source_path: Path) -> str | None:
    if shared_artwork := str(component.get("composite_artwork", "")).strip():
        return shared_artwork
    for override in component.get("composite_artwork_overrides", []):
        if _matches_source(source_path, [str(value) for value in override["source_patterns"]]):
            return str(override["path"])
    return None


def _composite_stage(soup: BeautifulSoup, artwork_path: str) -> Tag:
    stage = soup.new_tag(
        "div",
        attrs={
            "class": "hb-composite-stage",
            "aria-hidden": "true",
        },
    )
    image = soup.new_tag(
        "img",
        attrs={
            "class": "hb-composite-art",
            "src": artwork_path,
            "alt": "",
            "loading": "lazy",
        },
    )
    stage.append(image)
    return stage


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
    composite_artwork = _composite_artwork_path(view, source_path)
    if composite_artwork:
        figure["class"] = [*figure.get("class", []), "hb-has-composite-art"]
        figure.append(_composite_stage(soup, composite_artwork))
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

    supporting_lines: list[Tag] = []
    supporting_line_block: Tag | None = None
    supporting_line_count = int(spec.get("capture_following_lines", 0))
    if supporting_line_count:
        remaining_step_lines = steps.find_all(class_="line", recursive=False)
        if remaining_step_lines:
            supporting_line_block = steps
            direct_lines = remaining_step_lines
        else:
            candidate = _next_tag_sibling(figure)
            if not isinstance(candidate, Tag) or "line-block" not in candidate.get("class", []):
                raise WebPresentationError(
                    f"{source_path}: operation {operation_id} is missing governed supporting copy"
                )
            supporting_line_block = candidate
            direct_lines = candidate.find_all(class_="line", recursive=False)
        if len(direct_lines) < supporting_line_count:
            raise WebPresentationError(
                f"{source_path}: operation {operation_id} has only {len(direct_lines)} "
                f"supporting lines; expected at least {supporting_line_count}"
            )
        supporting_lines = direct_lines[:supporting_line_count]

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

    supporting_copy: Tag | None = None
    if supporting_lines:
        supporting_copy = soup.new_tag(
            "div",
            attrs={
                "class": "hb-operation-supporting-copy",
                "data-callout-id": f"operation.{operation_id}.supporting-copy",
            },
        )
        for line in supporting_lines:
            supporting_copy.append(line.extract())
        if supporting_line_block is not None and not supporting_line_block.find(
            class_="line", recursive=False
        ):
            supporting_line_block.decompose()

    steps_style = _position_style(spec.get("steps_rect"))
    if steps_style:
        steps_overlay["style"] = steps_style
    stage.append(steps_overlay)
    if supporting_copy is not None:
        stage.append(supporting_copy)
    composite_artwork = _composite_artwork_path(spec, source_path)
    if composite_artwork:
        figure["class"] = [*figure.get("class", []), "hb-has-composite-art"]
        figure.append(_composite_stage(soup, composite_artwork))
    figure.append(stage)


def _transform_auto_resume_table(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    expected_body_rows: int,
) -> None:
    candidates: list[tuple[Tag, list[Tag], list[Tag]]] = []
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        header_rows = table.select("thead > tr")
        body_rows = table.select("tbody > tr")
        if len(header_rows) != 1 or len(body_rows) != expected_body_rows:
            continue
        headers = [
            cell
            for cell in header_rows[0].find_all("th", recursive=False)
            if isinstance(cell, Tag)
        ]
        body_cell_counts = [
            len(row.find_all("td", recursive=False)) for row in body_rows
        ]
        if (
            len(headers) == 2
            and all(header.get_text(" ", strip=True) for header in headers)
            and body_cell_counts in ([2, 2, 2, 2], [2, 2, 1, 2])
        ):
            candidates.append((table, headers, body_rows))
    if len(candidates) != 1:
        raise WebPresentationError(
            f"{source_path}: expected one governed auto-resume table, "
            f"found {len(candidates)}"
        )

    table, headers, body_rows = candidates[0]
    spanning_cells = body_rows[1].find_all("td", recursive=False)
    continuation_cells = body_rows[2].find_all("td", recursive=False)
    if len(continuation_cells) == 2:
        blank_cell = continuation_cells[0]
        if blank_cell.get_text(" ", strip=True):
            raise WebPresentationError(
                f"{source_path}: auto-resume continuation cell must remain empty"
            )
        spanning_cells[0]["rowspan"] = "2"
        blank_cell.decompose()
    elif len(continuation_cells) == 1:
        if str(spanning_cells[0].get("rowspan", "")) != "2":
            raise WebPresentationError(
                f"{source_path}: auto-resume table lost its two-row condition span"
            )
    else:
        raise WebPresentationError(
            f"{source_path}: auto-resume continuation row has unexpected geometry"
        )

    for colgroup in table.find_all("colgroup", recursive=False):
        colgroup.decompose()
    colgroup = soup.new_tag("colgroup")
    colgroup.append(soup.new_tag("col", attrs={"class": "hb-auto-resume-col"}))
    colgroup.append(soup.new_tag("col", attrs={"class": "hb-auto-resume-col"}))
    table.insert(0, colgroup)
    table["class"] = [*table.get("class", []), "hb-auto-resume-table"]
    for index, header in enumerate(headers):
        header["scope"] = "col"
        header["class"] = [
            *header.get("class", []),
            "hb-auto-resume-left" if index == 0 else "hb-auto-resume-right",
        ]

    for row_index, row in enumerate(body_rows):
        cells = row.find_all("td", recursive=False)
        if len(cells) == 2:
            left, right = cells
            left["class"] = [*left.get("class", []), "hb-auto-resume-left"]
            right["class"] = [*right.get("class", []), "hb-auto-resume-right"]
        elif row_index == 2 and len(cells) == 1:
            cells[0]["class"] = [
                *cells[0].get("class", []),
                "hb-auto-resume-right",
            ]
        else:
            raise WebPresentationError(
                f"{source_path}: auto-resume row {row_index + 1} lost its column geometry"
            )

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-auto-resume-composition",
            "aria-label": " / ".join(
                header.get_text(" ", strip=True) for header in headers
            ),
        },
    )
    table.replace_with(composition)
    composition.append(table)


def _transform_lcd_mode_table(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    image_key: str,
    expected_body_rows: int,
) -> None:
    image = next(
        (
            candidate
            for candidate in soup.find_all("img")
            if _src_matches_key(str(candidate.get("src", "")), image_key)
        ),
        None,
    )
    if not isinstance(image, Tag):
        raise WebPresentationError(
            f"{source_path}: LCD mode composition is missing governed image {image_key}"
        )
    table = image.find_parent("table")
    if not isinstance(table, Tag):
        raise WebPresentationError(f"{source_path}: LCD mode image has no table")

    rows = [row for row in table.find_all("tr") if isinstance(row, Tag)]
    cell_counts = [len(row.find_all("td", recursive=False)) for row in rows]
    if len(rows) != expected_body_rows or cell_counts != [4, 2, 2, 3, 2, 2]:
        raise WebPresentationError(
            f"{source_path}: LCD mode table geometry changed: {cell_counts}"
        )

    first_cells = rows[0].find_all("td", recursive=False)
    art_cell = first_cells[0]
    if str(art_cell.get("rowspan", "")) != str(expected_body_rows):
        raise WebPresentationError(
            f"{source_path}: LCD mode artwork must span all {expected_body_rows} rows"
        )
    if str(first_cells[1].get("rowspan", "")) != "3":
        raise WebPresentationError(f"{source_path}: LCD mode first group lost its row span")
    second_group = rows[3].find_all("td", recursive=False)[0]
    if str(second_group.get("rowspan", "")) != "3":
        raise WebPresentationError(f"{source_path}: LCD mode second group lost its row span")

    image.extract()
    art_cell.decompose()
    for attribute in ("style", "width", "height"):
        image.attrs.pop(attribute, None)
    image["class"] = [*image.get("class", []), "hb-lcd-mode-art"]

    table.attrs.pop("style", None)
    table["class"] = [*table.get("class", []), "hb-lcd-mode-table"]
    colgroup = soup.new_tag("colgroup")
    for css_class in (
        "hb-lcd-mode-col-state",
        "hb-lcd-mode-col-action",
        "hb-lcd-mode-col-copy",
    ):
        colgroup.append(soup.new_tag("col", attrs={"class": css_class}))
    table.insert(0, colgroup)

    for row in rows:
        cells = row.find_all("td", recursive=False)
        for cell in cells:
            cell.attrs.pop("style", None)
        if len(cells) == 3:
            state, action, copy = cells
            state["class"] = [*state.get("class", []), "hb-lcd-mode-state"]
        elif len(cells) == 2:
            action, copy = cells
        else:
            raise WebPresentationError(f"{source_path}: LCD mode row lost its columns")
        action["class"] = [*action.get("class", []), "hb-lcd-mode-action"]
        copy["class"] = [*copy.get("class", []), "hb-lcd-mode-copy"]

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-lcd-mode-composition",
            "aria-label": str(image.get("alt", "LCD display mode")),
        },
    )
    art_panel = soup.new_tag("div", attrs={"class": "hb-lcd-mode-art-panel"})
    art_panel.append(image)
    table_panel = soup.new_tag("div", attrs={"class": "hb-lcd-mode-table-panel"})
    table.replace_with(composition)
    table_panel.append(table)
    composition.append(art_panel)
    composition.append(table_panel)


def _transform_operations(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
) -> None:
    operation_contract = contract["operations"]
    _transform_auto_resume_table(
        soup,
        source_path=source_path,
        expected_body_rows=int(operation_contract["auto_resume_table"]["body_rows"]),
    )
    _transform_lcd_mode_table(
        soup,
        source_path=source_path,
        image_key=str(operation_contract["lcd_mode_table"]["image_key"]),
        expected_body_rows=int(operation_contract["lcd_mode_table"]["body_rows"]),
    )
    figures = operation_contract["figures"]
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


def _transform_reference_figure(
    soup: BeautifulSoup,
    *,
    image: Tag,
    spec: dict[str, Any],
    source_path: Path,
) -> None:
    reference_id = str(spec["id"])
    if spec.get("presentation") == "shared-art-live-labels":
        transform_app_add_device(
            soup,
            image=image,
            spec=spec,
            source_path=source_path,
            error_type=WebPresentationError,
        )
        return
    label_block, caption_labels = prepare_reference_caption_data(
        image=image,
        spec=spec,
        source_path=source_path,
        error_type=WebPresentationError,
    )
    composite_artwork = _composite_artwork_path(spec, source_path)
    if not composite_artwork:
        raise WebPresentationError(
            f"{source_path}: reference figure {reference_id} has no composite artwork override"
        )

    figure = soup.new_tag(
        "figure",
        attrs={
            "class": ["hb-reference-figure", "hb-has-composite-art"],
            "data-reference-id": reference_id,
        },
    )
    if spec.get("captions_embedded"):
        figure["data-step-captions"] = "embedded"
    semantic = soup.new_tag(
        "div",
        attrs={
            "class": "hb-reference-semantic",
            "data-reference-id": f"{reference_id}.semantic",
        },
    )
    image["class"] = [*image.get("class", []), "hb-reference-art"]
    image.replace_with(figure)
    semantic.append(image)
    if label_block is not None:
        label_block["class"] = [*label_block.get("class", []), "hb-reference-labels"]
        semantic.append(label_block.extract())
    figure.append(_composite_stage(soup, composite_artwork))
    append_reference_captions(
        soup,
        figure,
        labels=caption_labels,
        layout=str(spec.get("caption_layout", "equal")),
    )
    figure.append(semantic)


def _transform_reference_figures(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
) -> None:
    for spec in contract["reference_figures"]["figures"]:
        spec_patterns = [str(value) for value in spec["source_patterns"]]
        if not _matches_source(source_path, spec_patterns):
            continue
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
                f"{source_path}: reference page is missing governed image {spec['image_key']}"
            )
        _transform_reference_figure(
            soup,
            image=image,
            spec=spec,
            source_path=source_path,
        )


def _transform_app_download(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
) -> None:
    spec = contract["app_download"]
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
            f"{source_path}: App download section is missing governed image {spec['image_key']}"
        )
    section = image.find_parent("section")
    if not isinstance(section, Tag):
        raise WebPresentationError(f"{source_path}: App download image has no section")
    heading = section.find("h2", recursive=False)
    if not isinstance(heading, Tag):
        raise WebPresentationError(f"{source_path}: App download section is missing its H2")

    paragraphs = [
        paragraph
        for paragraph in section.find_all("p", recursive=False)
        if isinstance(paragraph, Tag)
    ]
    copy_markup: list[str]
    if len(paragraphs) == 2:
        copy_markup = [paragraph.decode_contents().strip() for paragraph in paragraphs]
    elif len(paragraphs) == 1:
        parts = re.split(r"\s*\n+\s*", paragraphs[0].decode_contents().strip(), maxsplit=1)
        if len(parts) != 2:
            raise WebPresentationError(
                f"{source_path}: App download copy must provide left and right columns"
            )
        copy_markup = [part.strip() for part in parts]
    else:
        raise WebPresentationError(
            f"{source_path}: App download section has {len(paragraphs)} direct paragraphs; "
            "expected one split paragraph or two column paragraphs"
        )
    if any(not BeautifulSoup(markup, "html.parser").get_text(" ", strip=True) for markup in copy_markup):
        raise WebPresentationError(f"{source_path}: App download column copy is incomplete")

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-app-download-composition",
            "aria-label": heading.get_text(" ", strip=True),
        },
    )
    image["class"] = [*image.get("class", []), "hb-app-download-semantic-art"]
    image.replace_with(composition)

    copy_grid = soup.new_tag("div", attrs={"class": "hb-app-download-grid"})
    for column_id, markup in zip(("store", "qr"), copy_markup, strict=True):
        column = soup.new_tag(
            "div",
            attrs={
                "class": ["hb-app-download-column", f"hb-app-download-column-{column_id}"],
            },
        )
        art_frame = soup.new_tag("div", attrs={"class": "hb-app-download-art-frame"})
        art = soup.new_tag(
            "img",
            attrs={
                "class": ["hb-app-download-art", f"hb-app-download-art-{column_id}"],
                "src": str(spec["artwork"][column_id]),
                "alt": "",
                "aria-hidden": "true",
                "loading": "lazy",
            },
        )
        art_frame.append(art)
        column.append(art_frame)
        copy = soup.new_tag(
            "div",
            attrs={"class": ["hb-app-download-copy", f"hb-app-download-copy-{column_id}"]},
        )
        paragraph = soup.new_tag("p")
        _append_markup(paragraph, markup)
        copy.append(paragraph)
        column.append(copy)
        copy_grid.append(column)
    composition.append(copy_grid)
    semantic = soup.new_tag("div", attrs={"class": "hb-app-download-semantic"})
    semantic.append(image)
    composition.append(semantic)
    for paragraph in paragraphs:
        paragraph.decompose()


def _transform_app_inline_controls(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
) -> None:
    spec = contract["app_inline_controls"]
    paragraph_prefix = str(spec["add_device_paragraph_prefix"])
    paragraph = next(
        (
            candidate
            for candidate in soup.find_all("p")
            if candidate.get_text(" ", strip=True).startswith(paragraph_prefix)
        ),
        None,
    )
    if not isinstance(paragraph, Tag):
        raise WebPresentationError(
            f"{source_path}: App setup is missing its {paragraph_prefix} add-device paragraph"
        )

    icon = soup.new_tag(
        "span",
        attrs={
            "class": "hb-inline-add-device-icon",
            "role": "img",
            "aria-label": str(spec["accessible_label"]),
        },
    )
    icon.string = "+"

    button_terms = [str(term) for term in spec["button_terms"]]
    button_pattern = rf"\b(?:{'|'.join(re.escape(term) for term in button_terms)})\b"
    if not re.search(button_pattern, paragraph.get_text(" ", strip=True), flags=re.IGNORECASE):
        raise WebPresentationError(
            f"{source_path}: App setup {paragraph_prefix} paragraph has no localized button term"
        )

    visible_labels = paragraph.find_all("strong")
    if len(visible_labels) != 1:
        raise WebPresentationError(
            f"{source_path}: App setup {paragraph_prefix} paragraph must contain exactly one "
            "visible add-device label"
        )
    visible_label = visible_labels[0]
    localized_label = visible_label.get_text(" ", strip=True)
    if not localized_label:
        raise WebPresentationError(
            f"{source_path}: App setup {paragraph_prefix} add-device label is empty"
        )
    icon["aria-label"] = localized_label
    visible_label.replace_with(icon)


def _transform_in_the_box(soup: BeautifulSoup, *, source_path: Path) -> None:
    heading = soup.find("h1")
    if not isinstance(heading, Tag):
        raise WebPresentationError(f"{source_path}: in-the-box page is missing its H1")
    inbox_table = _next_tag_sibling(heading)
    if not isinstance(inbox_table, Tag) or inbox_table.name != "table":
        raise WebPresentationError(f"{source_path}: in-the-box H1 must be followed by a table")
    inbox_rows = _table_rows(inbox_table)
    if len(inbox_rows) != 1 or len(inbox_rows[0]) != 3:
        raise WebPresentationError(
            f"{source_path}: in-the-box table must contain one row with three items"
        )

    tip_table = _next_tag_sibling(inbox_table)
    if not isinstance(tip_table, Tag) or tip_table.name != "table":
        raise WebPresentationError(f"{source_path}: in-the-box grid is missing its tip table")
    tip_rows = _table_rows(tip_table)
    if len(tip_rows) != 1 or len(tip_rows[0]) != 2:
        raise WebPresentationError(
            f"{source_path}: in-the-box tip must contain one label cell and one body cell"
        )

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-inbox-composition",
            "aria-label": heading.get_text(" ", strip=True),
        },
    )
    grid = soup.new_tag("ol", attrs={"class": "hb-inbox-grid"})
    for index, cell in enumerate(inbox_rows[0], start=1):
        image = cell.find("img")
        if not isinstance(image, Tag):
            raise WebPresentationError(
                f"{source_path}: in-the-box item {index} is missing its image"
            )
        image.extract()
        image["class"] = [*image.get("class", []), "hb-inbox-art"]
        for attribute in ("style", "width", "height"):
            image.attrs.pop(attribute, None)

        card = soup.new_tag(
            "li",
            attrs={
                "class": "hb-inbox-card",
                "data-item-number": str(index),
            },
        )
        label = soup.new_tag("div", attrs={"class": "hb-inbox-label"})
        for child in list(cell.contents):
            label.append(child.extract())
        if not label.get_text(" ", strip=True):
            raise WebPresentationError(
                f"{source_path}: in-the-box item {index} is missing its label"
            )
        card.append(image)
        card.append(label)
        grid.append(card)

    tip_label_cell, tip_body_cell = tip_rows[0]
    tip = soup.new_tag("div", attrs={"class": "hb-inbox-tip", "role": "note"})
    tip_label = soup.new_tag("div", attrs={"class": "hb-inbox-tip-label"})
    tip_body = soup.new_tag("div", attrs={"class": "hb-inbox-tip-body"})
    for child in list(tip_label_cell.contents):
        tip_label.append(child.extract())
    for child in list(tip_body_cell.contents):
        tip_body.append(child.extract())
    if not tip_label.get_text(" ", strip=True) or not tip_body.get_text(" ", strip=True):
        raise WebPresentationError(f"{source_path}: in-the-box tip copy is incomplete")
    tip.append(tip_label)
    tip.append(tip_body)

    inbox_table.replace_with(composition)
    composition.append(grid)
    composition.append(tip)
    tip_table.decompose()


def _fcc_right_column_marker(spec: dict[str, Any], source_path: Path) -> str | None:
    for override in spec["right_column_markers"]:
        if _matches_source(
            source_path,
            [str(pattern) for pattern in override["source_patterns"]],
        ):
            return str(override["marker"])
    return None


def _fcc_copy_before_bullets(
    heading: Tag,
    *,
    source_path: Path,
) -> tuple[Tag, list[Tag], Tag]:
    opening = _next_tag_sibling(heading)
    if not isinstance(opening, Tag) or "line-block" not in opening.get("class", []):
        raise WebPresentationError(f"{source_path}: FCC page is missing its opening line block")

    copy_blocks: list[Tag] = []
    sibling = _next_tag_sibling(opening)
    while isinstance(sibling, Tag) and sibling.name != "ul":
        if sibling.name not in {"p", "div"}:
            raise WebPresentationError(
                f"{source_path}: FCC pre-list copy must remain paragraph-based"
            )
        copy_blocks.append(sibling)
        sibling = _next_tag_sibling(sibling)
    if not copy_blocks or not isinstance(sibling, Tag) or sibling.name != "ul":
        raise WebPresentationError(f"{source_path}: FCC page is missing its body or measure list")
    return opening, copy_blocks, sibling


def _fcc_normalized_copy(blocks: list[Tag]) -> str:
    copy = " ".join(block.get_text(" ", strip=True) for block in blocks)
    # A legacy French RST page contains two literal line-block markers inside a
    # paragraph. They are source punctuation artifacts, not FCC copy.
    return re.sub(r"\s*\|\s*", " ", copy).strip()


def _append_fcc_copy(soup: BeautifulSoup, parent: Tag, text: str) -> None:
    paragraph = soup.new_tag("p")
    label_match = re.match(r"^([^:]{2,20}\s*:)(.*)$", text, flags=re.DOTALL)
    if label_match:
        label = soup.new_tag("strong")
        label.string = label_match.group(1).strip()
        paragraph.append(label)
        remainder = label_match.group(2).strip()
        if remainder:
            paragraph.append(NavigableString(f" {remainder}"))
    else:
        paragraph.string = text
    parent.append(paragraph)


def _transform_fcc(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
) -> None:
    spec = contract["fcc"]
    heading = soup.find("h1")
    if not isinstance(heading, Tag) or heading.get_text(" ", strip=True).casefold() != "fcc":
        raise WebPresentationError(f"{source_path}: FCC page is missing its H1")

    opening, copy_blocks, bullets = _fcc_copy_before_bullets(
        heading,
        source_path=source_path,
    )

    marker = _fcc_right_column_marker(spec, source_path)
    body_text = _fcc_normalized_copy(copy_blocks)
    marker_index = body_text.find(marker) if marker else -1
    if marker_index <= 0:
        raise WebPresentationError(
            f"{source_path}: FCC body is missing its governed right-column marker"
        )
    left_body_text = body_text[:marker_index].strip()
    right_body_text = body_text[marker_index:].strip()

    trailing: list[Tag] = []
    sibling = _next_tag_sibling(bullets)
    while isinstance(sibling, Tag):
        if sibling.name != "p":
            raise WebPresentationError(
                f"{source_path}: FCC trailing content must remain paragraph-based"
            )
        trailing.append(sibling)
        sibling = _next_tag_sibling(sibling)
    if not trailing:
        raise WebPresentationError(f"{source_path}: FCC page is missing modification copy")

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-fcc-composition",
            "aria-label": heading.get_text(" ", strip=True),
        },
    )
    grid = soup.new_tag("div", attrs={"class": "hb-fcc-grid"})
    left = soup.new_tag("div", attrs={"class": ["hb-fcc-column", "hb-fcc-column-left"]})
    right = soup.new_tag("div", attrs={"class": ["hb-fcc-column", "hb-fcc-column-right"]})
    opening_row = soup.new_tag("div", attrs={"class": "hb-fcc-opening"})
    logo = soup.new_tag(
        "img",
        attrs={
            "class": "hb-fcc-mark",
            "src": str(spec["mark_path"]),
            "alt": "FCC",
            "loading": "lazy",
        },
    )
    opening_copy = soup.new_tag("div", attrs={"class": "hb-fcc-opening-copy"})
    opening_copy.append(opening.extract())
    opening_row.append(logo)
    opening_row.append(opening_copy)
    left.append(opening_row)
    _append_fcc_copy(soup, left, left_body_text)
    _append_fcc_copy(soup, right, right_body_text)
    right.append(bullets.extract())
    for paragraph in trailing:
        right.append(paragraph.extract())

    for block in copy_blocks:
        block.decompose()
    grid.append(left)
    grid.append(right)
    composition.append(grid)
    heading.insert_after(composition)


def _transform_lcd_icon_table(
    soup: BeautifulSoup,
    *,
    source_path: Path,
) -> None:
    candidates = [
        table
        for table in soup.find_all("table")
        if isinstance(table, Tag)
        and (rows := _table_rows(table))
        and all(len(row) == 4 for row in rows)
    ]
    if len(candidates) != 1:
        raise WebPresentationError(
            f"{source_path}: expected one four-column LCD icon table, found {len(candidates)}"
        )

    table = candidates[0]
    rows = _table_rows(table)
    if not all(row[1].find("img") and row[2].get_text(" ", strip=True) for row in rows):
        raise WebPresentationError(f"{source_path}: LCD icon table rows are incomplete")

    for colgroup in table.find_all("colgroup", recursive=False):
        colgroup.decompose()
    colgroup = soup.new_tag("colgroup")
    for css_class in (
        "hb-lcd-col-number",
        "hb-lcd-col-icon",
        "hb-lcd-col-name",
        "hb-lcd-col-description",
    ):
        colgroup.append(soup.new_tag("col", attrs={"class": css_class}))
    table.insert(0, colgroup)
    table["class"] = [*table.get("class", []), "hb-lcd-icon-table"]

    for row in rows:
        row[0]["class"] = [*row[0].get("class", []), "hb-lcd-number"]
        row[1]["class"] = [*row[1].get("class", []), "hb-lcd-icon"]
        row[2]["class"] = [*row[2].get("class", []), "hb-lcd-name"]
        row[3]["class"] = [*row[3].get("class", []), "hb-lcd-description"]
        image = row[1].find("img")
        if isinstance(image, Tag):
            image["class"] = [*image.get("class", []), "hb-lcd-icon-art"]
            for attribute in ("style", "width", "height"):
                image.attrs.pop(attribute, None)

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-lcd-table-composition",
            "aria-label": "LCD icon meanings",
        },
    )
    table.replace_with(composition)
    composition.append(table)


def _transform_troubleshooting_table(
    soup: BeautifulSoup,
    *,
    source_path: Path,
) -> None:
    expected_codes = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FE"]
    candidates: list[tuple[Tag, list[Tag], list[Tag]]] = []
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        header_rows = table.select("thead > tr")
        body_rows = table.select("tbody > tr")
        if len(header_rows) != 1 or len(body_rows) != len(expected_codes):
            continue
        headers = [
            cell
            for cell in header_rows[0].find_all("th", recursive=False)
            if isinstance(cell, Tag)
        ]
        if len(headers) != 2 or not all(
            header.get_text(" ", strip=True) for header in headers
        ):
            continue
        if not all(len(row.find_all("td", recursive=False)) == 2 for row in body_rows):
            continue
        codes = [
            row.find_all("td", recursive=False)[0].get_text(" ", strip=True)
            for row in body_rows
        ]
        if codes == expected_codes:
            candidates.append((table, headers, body_rows))

    if len(candidates) != 1:
        raise WebPresentationError(
            f"{source_path}: expected one governed troubleshooting table with codes "
            f"{expected_codes}, found {len(candidates)}"
        )

    table, headers, body_rows = candidates[0]
    for colgroup in table.find_all("colgroup", recursive=False):
        colgroup.decompose()
    colgroup = soup.new_tag("colgroup")
    colgroup.append(
        soup.new_tag("col", attrs={"class": "hb-troubleshooting-col-code"})
    )
    colgroup.append(
        soup.new_tag("col", attrs={"class": "hb-troubleshooting-col-measures"})
    )
    table.insert(0, colgroup)
    table.attrs.pop("style", None)
    table["class"] = [*table.get("class", []), "hb-troubleshooting-table"]

    for index, header in enumerate(headers):
        header.attrs.pop("style", None)
        header["scope"] = "col"
        header["class"] = [
            *header.get("class", []),
            "hb-troubleshooting-code"
            if index == 0
            else "hb-troubleshooting-measures",
        ]

    for row in body_rows:
        code, measures = row.find_all("td", recursive=False)
        code.attrs.pop("style", None)
        measures.attrs.pop("style", None)
        code["class"] = [*code.get("class", []), "hb-troubleshooting-code"]
        measures["class"] = [
            *measures.get("class", []),
            "hb-troubleshooting-measures",
        ]

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-troubleshooting-composition",
            "aria-label": " / ".join(
                header.get_text(" ", strip=True) for header in headers
            ),
        },
    )
    table.replace_with(composition)
    composition.append(table)


def _superscript_circled_references(soup: BeautifulSoup, cell: Tag) -> int:
    replacements = 0
    for text_node in list(cell.find_all(string=_CIRCLED_REFERENCE_RE)):
        if text_node.find_parent("sup"):
            continue
        text = str(text_node)
        fragments: list[NavigableString | Tag] = []
        cursor = 0
        for match in _CIRCLED_REFERENCE_RE.finditer(text):
            if match.start() > cursor:
                fragments.append(NavigableString(text[cursor : match.start()]))
            reference = soup.new_tag(
                "sup",
                attrs={"class": "hb-spec-reference"},
            )
            reference.string = match.group(0)
            fragments.append(reference)
            replacements += 1
            cursor = match.end()
        if cursor < len(text):
            fragments.append(NavigableString(text[cursor:]))
        text_node.replace_with(*fragments)
    return replacements


def _transform_specification_tables(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    expected_sections: int,
    expected_circled_references: int,
) -> None:
    headings = [
        heading
        for heading in soup.select("h2.hb-spec-section")
        if isinstance(heading, Tag)
    ]
    if len(headings) != expected_sections:
        raise WebPresentationError(
            f"{source_path}: expected {expected_sections} governed specification "
            f"sections, found {len(headings)}"
        )

    observed_circled_references = 0
    for heading in headings:
        heading_text_node = heading.select_one(".hb-spec-section-text")
        if not isinstance(heading_text_node, Tag):
            raise WebPresentationError(
                f"{source_path}: specification heading lost its localized title span"
            )
        heading_text = heading_text_node.get_text(" ", strip=True)
        table = _next_tag_sibling(heading)
        table_classes = table.get("class", []) if isinstance(table, Tag) else []
        if (
            not isinstance(table, Tag)
            or table.name != "table"
            or not ({"hb-spec-table", "manual-spec-table"} & set(table_classes))
        ):
            raise WebPresentationError(
                f"{source_path}: specification section {heading_text!r} must be "
                "followed by its governed table"
            )
        rows = table.select("tbody > tr")
        if not rows:
            raise WebPresentationError(
                f"{source_path}: specification section {heading_text!r} lost its "
                "two-column rows"
            )

        heading.clear()
        heading.string = heading_text
        heading.attrs.pop("class", None)

        for colgroup in table.find_all("colgroup", recursive=False):
            colgroup.decompose()
        colgroup = soup.new_tag("colgroup")
        colgroup.append(soup.new_tag("col", attrs={"class": "hb-spec-col-label"}))
        colgroup.append(soup.new_tag("col", attrs={"class": "hb-spec-col-value"}))
        table.insert(0, colgroup)
        table.attrs.pop("style", None)
        table["class"] = [*table.get("class", []), "hb-spec-table"]
        active_label_rows = 0
        for row in rows:
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) == 2 and active_label_rows == 0:
                label, value = cells
                try:
                    rowspan = int(str(label.get("rowspan", "1")))
                except ValueError as exc:
                    raise WebPresentationError(
                        f"{source_path}: specification section {heading_text!r} has "
                        "an invalid label rowspan"
                    ) from exc
                if rowspan < 1:
                    raise WebPresentationError(
                        f"{source_path}: specification section {heading_text!r} has "
                        "a non-positive label rowspan"
                    )
                active_label_rows = rowspan - 1
                label.name = "th"
                label["scope"] = "row"
                label.attrs.pop("style", None)
                label["class"] = [*label.get("class", []), "hb-spec-label"]
            elif len(cells) == 1 and active_label_rows > 0:
                value = cells[0]
                active_label_rows -= 1
            else:
                raise WebPresentationError(
                    f"{source_path}: specification section {heading_text!r} lost its "
                    "two-column row geometry"
                )
            value.attrs.pop("style", None)
            value["class"] = [*value.get("class", []), "hb-spec-value"]
        if active_label_rows:
            raise WebPresentationError(
                f"{source_path}: specification section {heading_text!r} ended inside "
                "a row-spanning label"
            )

        for cell in table.select("th.hb-spec-label, td.hb-spec-value"):
            observed_circled_references += _superscript_circled_references(soup, cell)

        composition = soup.new_tag(
            "figure",
            attrs={
                "class": "hb-spec-table-composition",
                "aria-label": heading_text,
            },
        )
        table.replace_with(composition)
        composition.append(table)

    if observed_circled_references != expected_circled_references:
        raise WebPresentationError(
            f"{source_path}: expected {expected_circled_references} circled "
            f"specification references, found {observed_circled_references}"
        )


def _warranty_period_title(cell: Tag, *, source_path: Path) -> tuple[str, str, str]:
    strong_tags = [tag for tag in cell.find_all("strong") if isinstance(tag, Tag)]
    if not strong_tags:
        raise WebPresentationError(
            f"{source_path}: warranty period column has no duration heading"
        )
    first_text = strong_tags[0].get_text(" ", strip=True)
    match = re.fullmatch(r"([23])\s+(\S+)(?:\s+(.+))?", first_text)
    if not match:
        raise WebPresentationError(
            f"{source_path}: unexpected warranty duration heading {first_text!r}"
        )
    years, unit, inline_label = match.groups()
    label = (inline_label or "").strip()
    title_paragraphs = [strong_tags[0].find_parent("p")]
    if not label:
        if len(strong_tags) < 2:
            raise WebPresentationError(
                f"{source_path}: warranty period {years} {unit} is missing its label"
            )
        label = strong_tags[1].get_text(" ", strip=True)
        title_paragraphs.append(strong_tags[1].find_parent("p"))
    if not label:
        raise WebPresentationError(
            f"{source_path}: warranty period {years} {unit} has an empty label"
        )
    for paragraph in title_paragraphs:
        if isinstance(paragraph, Tag) and paragraph.parent is not None:
            paragraph.decompose()
    return years, unit, label


def _transform_warranty_period(
    soup: BeautifulSoup,
    *,
    section: Tag,
    heading: Tag,
    table: Tag,
    source_path: Path,
    expected_years: list[str],
) -> None:
    rows = _table_rows(table)
    if len(rows) != 1 or len(rows[0]) != len(expected_years):
        raise WebPresentationError(
            f"{source_path}: warranty period must contain one row with "
            f"{len(expected_years)} columns"
        )
    direct_blocks = [child for child in section.contents if isinstance(child, Tag)]
    if direct_blocks != [heading, table]:
        raise WebPresentationError(
            f"{source_path}: warranty period section contains unexpected blocks"
        )

    heading_text = heading.get_text(" ", strip=True)
    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-warranty-period-card",
            "aria-label": heading_text,
        },
    )
    grid = soup.new_tag("div", attrs={"class": "hb-warranty-period-grid"})
    observed_years: list[str] = []
    for cell in rows[0]:
        years, unit, label = _warranty_period_title(cell, source_path=source_path)
        observed_years.append(years)
        item = soup.new_tag(
            "div",
            attrs={
                "class": "hb-warranty-period-item",
                "aria-label": f"{years} {unit} {label}",
            },
        )
        title = soup.new_tag("div", attrs={"class": "hb-warranty-period-heading"})
        badge = soup.new_tag("span", attrs={"class": "hb-warranty-year-badge"})
        badge.string = years
        title_copy = soup.new_tag("div", attrs={"class": "hb-warranty-period-title"})
        unit_tag = soup.new_tag("strong", attrs={"class": "hb-warranty-years-unit"})
        unit_tag.string = unit
        label_tag = soup.new_tag(
            "strong", attrs={"class": "hb-warranty-period-label"}
        )
        label_tag.string = label
        title_copy.append(unit_tag)
        title_copy.append(label_tag)
        title.append(badge)
        title.append(title_copy)
        item.append(title)

        copy = soup.new_tag("div", attrs={"class": "hb-warranty-period-copy"})
        for child in list(cell.contents):
            copy.append(child.extract())
        if not copy.get_text(" ", strip=True):
            raise WebPresentationError(
                f"{source_path}: warranty period {years} {unit} has no explanatory copy"
            )
        item.append(copy)
        grid.append(item)

    if observed_years != expected_years:
        raise WebPresentationError(
            f"{source_path}: warranty period order changed: {observed_years}"
        )
    table.replace_with(composition)
    composition.append(grid)


def _transform_warranty(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    expected_sections: int,
    expected_years: list[str],
) -> None:
    heading = soup.find("h1", recursive=False)
    if not isinstance(heading, Tag):
        raise WebPresentationError(f"{source_path}: warranty page is missing its H1")
    intro_paragraphs = [
        paragraph
        for paragraph in soup.find_all("p", recursive=False)
        if isinstance(paragraph, Tag)
    ]
    if len(intro_paragraphs) != 2 or not intro_paragraphs[0].find("strong"):
        raise WebPresentationError(
            f"{source_path}: warranty page must begin with its governed notice and local note"
        )
    sections = [
        section
        for section in soup.find_all("section", recursive=False)
        if isinstance(section, Tag)
    ]
    if len(sections) != expected_sections:
        raise WebPresentationError(
            f"{source_path}: expected {expected_sections} warranty sections, "
            f"found {len(sections)}"
        )

    intro = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-warranty-intro-composition",
            "aria-label": heading.get_text(" ", strip=True),
        },
    )
    intro_panel = soup.new_tag("div", attrs={"class": "hb-warranty-intro-panel"})
    local_note = soup.new_tag("div", attrs={"class": "hb-warranty-local-note"})
    intro_paragraphs[0].replace_with(intro)
    intro_panel.append(intro_paragraphs[0])
    local_note.append(intro_paragraphs[1].extract())
    intro.append(intro_panel)
    intro.append(local_note)

    period_sections = [
        section
        for section in sections
        if isinstance(section.find("table", recursive=False), Tag)
    ]
    if len(period_sections) != 1:
        raise WebPresentationError(
            f"{source_path}: expected one warranty period table section, "
            f"found {len(period_sections)}"
        )

    for index, section in enumerate(sections, start=1):
        section_heading = section.find("h2", recursive=False)
        if not isinstance(section_heading, Tag):
            raise WebPresentationError(
                f"{source_path}: warranty section {index} is missing its H2"
            )
        table = section.find("table", recursive=False)
        if isinstance(table, Tag):
            _transform_warranty_period(
                soup,
                section=section,
                heading=section_heading,
                table=table,
                source_path=source_path,
                expected_years=expected_years,
            )
            continue

        content_blocks = [
            child
            for child in section.contents
            if isinstance(child, Tag) and child is not section_heading
        ]
        if not content_blocks:
            raise WebPresentationError(
                f"{source_path}: warranty section {index} has no body copy"
            )
        card = soup.new_tag(
            "figure",
            attrs={
                "class": "hb-warranty-card",
                "aria-label": section_heading.get_text(" ", strip=True),
                "data-warranty-card-index": str(index),
            },
        )
        section_heading.insert_after(card)
        for block in content_blocks:
            card.append(block.extract())


def _transform_meaning_symbols_table(
    soup: BeautifulSoup,
    *,
    source_path: Path,
) -> None:
    """Split the source four-column symbol matrix into two independent panels."""
    candidates: list[tuple[Tag, list[list[Tag]]]] = []
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        rows = _table_rows(table)
        if len(rows) != 7 or not all(len(row) == 4 for row in rows):
            continue
        header, *body_rows = rows
        if not all(cell.get_text(" ", strip=True) for cell in header):
            continue
        if not all(
            row[0].find("img")
            and row[1].get_text(" ", strip=True)
            and (
                bool(row[2].find("img"))
                == bool(row[3].get_text(" ", strip=True))
            )
            for row in body_rows
        ):
            continue
        candidates.append((table, rows))

    if len(candidates) != 1:
        raise WebPresentationError(
            f"{source_path}: expected one governed four-column symbol table, "
            f"found {len(candidates)}"
        )

    source_table, rows = candidates[0]
    header, *body_rows = rows
    populated_right_rows = [
        row for row in body_rows if row[2].find("img")
    ]
    if len(body_rows) != 6 or len(populated_right_rows) != 5:
        raise WebPresentationError(
            f"{source_path}: symbol panel row contract changed: "
            f"left={len(body_rows)}, right={len(populated_right_rows)}"
        )

    composition = soup.new_tag(
        "figure",
        attrs={
            "class": "hb-symbol-pair-composition",
            "aria-label": " / ".join(
                cell.get_text(" ", strip=True) for cell in header[:2]
            ),
        },
    )
    grid = soup.new_tag("div", attrs={"class": "hb-symbol-pair-grid"})
    composition.append(grid)

    for panel_index, column_offset in enumerate((0, 2)):
        panel = soup.new_tag(
            "div",
            attrs={
                "class": ["hb-symbol-panel", f"hb-symbol-panel-{panel_index + 1}"],
            },
        )
        table = soup.new_tag("table", attrs={"class": "hb-symbol-panel-table"})
        colgroup = soup.new_tag("colgroup")
        colgroup.append(soup.new_tag("col", attrs={"class": "hb-symbol-col-icon"}))
        colgroup.append(soup.new_tag("col", attrs={"class": "hb-symbol-col-meaning"}))
        table.append(colgroup)

        thead = soup.new_tag("thead")
        header_row = soup.new_tag("tr")
        for cell_index, source_cell in enumerate(
            header[column_offset : column_offset + 2]
        ):
            source_cell.extract()
            source_cell.name = "th"
            source_cell["scope"] = "col"
            source_cell["class"] = [
                "hb-symbol-icon-heading"
                if cell_index == 0
                else "hb-symbol-meaning-heading"
            ]
            header_row.append(source_cell)
        thead.append(header_row)
        table.append(thead)

        tbody = soup.new_tag("tbody")
        for source_row in body_rows:
            pair = source_row[column_offset : column_offset + 2]
            if not pair[0].find("img"):
                if pair[1].get_text(" ", strip=True):
                    raise WebPresentationError(
                        f"{source_path}: symbol row has meaning copy without artwork"
                    )
                continue
            row = soup.new_tag("tr")
            icon_cell, meaning_cell = pair
            icon_cell.extract()
            meaning_cell.extract()
            icon_cell["class"] = ["hb-symbol-icon"]
            meaning_cell["class"] = ["hb-symbol-meaning"]
            image = icon_cell.find("img")
            if not isinstance(image, Tag):
                raise WebPresentationError(
                    f"{source_path}: symbol row is missing its governed artwork"
                )
            for attribute in ("style", "width", "height"):
                image.attrs.pop(attribute, None)
            image["class"] = [*image.get("class", []), "hb-symbol-art"]
            row.append(icon_cell)
            row.append(meaning_cell)
            tbody.append(row)
        table.append(tbody)
        panel.append(table)
        grid.append(panel)

    source_table.replace_with(composition)


def _transform_preface(
    soup: BeautifulSoup,
    *,
    source_path: Path,
) -> None:
    first_block = next(
        (child for child in soup.contents if isinstance(child, Tag)),
        None,
    )
    if not isinstance(first_block, Tag) or first_block.name != "p":
        raise WebPresentationError(
            f"{source_path}: web preface is missing its leading language inventory"
        )
    language_inventory = first_block.get_text(" ", strip=True)
    if not re.fullmatch(r"[^/]{2,32}(?:\s*/\s*[^/]{2,32}){1,7}", language_inventory):
        raise WebPresentationError(
            f"{source_path}: unexpected web preface language inventory: "
            f"{language_inventory!r}"
        )
    first_block.decompose()


def transform_web_fragment(
    html_fragment: str,
    *,
    source_path: Path,
    contract: dict[str, Any] | None = None,
) -> str:
    """Apply web composition to governed figure pages; leave other pages byte-identical."""
    data = contract or load_web_manual_contract()
    preface = data["preface"]
    overview = data["product_overview"]
    operations = data["operations"]
    fcc = data["fcc"]
    lcd_icon_table = data["lcd_icon_table"]
    meaning_symbols = data["meaning_symbols"]
    troubleshooting_table = data["troubleshooting_table"]
    specifications = data["specifications"]
    warranty = data["warranty"]
    in_the_box = data["in_the_box"]
    reference_figures = data["reference_figures"]
    app_download = data["app_download"]
    app_inline_controls = data["app_inline_controls"]
    is_preface = _matches_source(source_path, list(preface["source_patterns"]))
    is_overview = _matches_source(source_path, list(overview["source_patterns"]))
    is_operations = _matches_source(source_path, list(operations["source_patterns"]))
    is_fcc = _matches_source(source_path, list(fcc["source_patterns"]))
    is_lcd_icon_table = _matches_source(
        source_path,
        list(lcd_icon_table["source_patterns"]),
    )
    is_meaning_symbols = _matches_source(
        source_path,
        list(meaning_symbols["source_patterns"]),
    )
    is_troubleshooting_table = _matches_source(
        source_path,
        list(troubleshooting_table["source_patterns"]),
    )
    is_specifications = _matches_source(
        source_path,
        list(specifications["source_patterns"]),
    )
    is_warranty = _matches_source(source_path, list(warranty["source_patterns"]))
    is_in_the_box = _matches_source(source_path, list(in_the_box["source_patterns"]))
    is_reference_page = _matches_source(
        source_path, list(reference_figures["source_patterns"])
    )
    is_app_download = _matches_source(source_path, list(app_download["source_patterns"]))
    is_app_inline_controls = _matches_source(
        source_path, list(app_inline_controls["source_patterns"])
    )
    if not (
        is_preface
        or is_overview
        or is_operations
        or is_fcc
        or is_lcd_icon_table
        or is_meaning_symbols
        or is_troubleshooting_table
        or is_specifications
        or is_warranty
        or is_in_the_box
        or is_reference_page
        or is_app_download
        or is_app_inline_controls
    ):
        return html_fragment
    if not _supports_figure_contract(source_path, data):
        return html_fragment

    soup = BeautifulSoup(html_fragment, "html.parser")
    if is_preface:
        _transform_preface(soup, source_path=source_path)
    if is_overview:
        _transform_product_overview(soup, source_path=source_path, contract=data)
    if is_operations:
        _transform_operations(soup, source_path=source_path, contract=data)
    if is_fcc:
        _transform_fcc(soup, source_path=source_path, contract=data)
    if is_lcd_icon_table:
        _transform_lcd_icon_table(soup, source_path=source_path)
    if is_meaning_symbols:
        _transform_meaning_symbols_table(soup, source_path=source_path)
    if is_troubleshooting_table:
        _transform_troubleshooting_table(soup, source_path=source_path)
    if is_specifications:
        _transform_specification_tables(
            soup,
            source_path=source_path,
            expected_sections=int(specifications["section_count"]),
            expected_circled_references=int(
                specifications["circled_reference_count"]
            ),
        )
    if is_warranty:
        _transform_warranty(
            soup,
            source_path=source_path,
            expected_sections=int(warranty["section_count"]),
            expected_years=[str(value) for value in warranty["period_years"]],
        )
    if is_in_the_box:
        _transform_in_the_box(soup, source_path=source_path)
    if is_app_download:
        _transform_app_download(soup, source_path=source_path, contract=data)
    if is_app_inline_controls:
        _transform_app_inline_controls(soup, source_path=source_path, contract=data)
    if is_reference_page:
        _transform_reference_figures(soup, source_path=source_path, contract=data)
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
    "protect_web_callouts_for_pandoc",
    "protect_web_figures_for_pandoc",
    "protect_web_inline_controls_for_pandoc",
    "restore_web_callouts_after_pandoc",
    "restore_web_figures_after_pandoc",
    "restore_web_inline_controls_after_pandoc",
    "should_include_web_page",
    "transform_web_fragment",
]
