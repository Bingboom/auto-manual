#!/usr/bin/env python3
"""Responsive web-only composition for declared tables and governed figures.

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

from tools.manual_ir import ManualIR, build_manual_ir_from_source
from tools.manual_ir.web_callouts import load_web_callout_source
from tools.web_callout_ir import render_callout_ir
from tools.component_specs.overview_instance import resolve_overview_instance
from tools.utils.path_utils import get_paths
from tools.web_composite_manifest import WebCompositeManifest
from tools.web_composite_presentation import (
    WebCompositeContext,
    supports_figure_contract,
)
from tools.web_fcc_component import transform_fcc
from tools.web_inbox_component import transform_inbox
from tools.web_overview_component import transform_overview
from tools.web_reference_components import (
    append_reference_captions,
    prepare_reference_caption_data,
    transform_app_add_device,
)
from tools.web_spec_component import transform_specification_tables
from tools.web_symbol_components import transform_symbol_signal_table
from tools.web_stylesheets import WEB_STYLESHEET_NAME, copy_web_stylesheet
from tools.web_troubleshooting_component import transform_troubleshooting_tables
from tools.web_lcd_component import transform_lcd_icon_tables


DOCUMENT_PRESENTATION_PROFILE = "document"
WEB_PRESENTATION_PROFILE = "web"
PRESENTATION_PROFILE_ENV = "AUTO_MANUAL_PRESENTATION_PROFILE"
WEB_CONTRACT_NAME = "web_manual.json"
_WEB_FIGURE_RE = re.compile(
    r'<figure\b(?=[^>]*\bclass=["\'][^"\']*\bhb-'
    r'(?:(?:annotated|operation|reference)-figure|inbox-composition|app-(?:add-device|download)-composition|fcc-composition|lcd-table-composition|lcd-mode-composition|auto-resume-composition|symbol-(?:signal|pair)-composition|troubleshooting-composition|spec-table-composition|warranty-intro-composition|warranty-card|warranty-period-card)\b)'
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
_PREFACE_LANGUAGE_INVENTORY_RE = re.compile(
    r"[^/]{2,32}(?:\s*/\s*[^/]{2,32}){1,7}"
)
_PREFACE_REVIEW_HEADING_RE = re.compile(
    r"(?:(?:[A-Z]{2}(?:-[A-Z]{2})?)\s+)?(?:IMPORTANT|IMPORTANTE)"
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


def protect_web_callouts_for_pandoc(
    html_text: str, *, source_path: Path | None = None,
    model: str | None = None, region: str | None = None,
) -> tuple[str, dict[str, ManualIR]]:
    """Replace semantic callout tables with stable tokens before Pandoc parses HTML.

    Without this guard, Pandoc can convert plain callouts into pipe tables while
    leaving callouts with richer body markup as raw HTML. That content-dependent
    split drops the semantic classes, creates empty table headers, and can inject
    a 50/50 colgroup. Restoring the original table keeps every signal type on the
    same ``manual-callout-*`` component contract. The handoff carries public IR;
    restoration validates and consumes it without reopening the source file.
    """
    protected: dict[str, ManualIR] = {}

    def replace(match: re.Match[str]) -> str:
        token = f"AUTOMANUALWEBCALLOUT{len(protected) + 1:04d}PLACEHOLDER"
        callout_html = match.group(0)
        try:
            source = load_web_callout_source(
                callout_html, source_path=Path(f"{source_path or 'pandoc'}#{token}"),
                model=model, region=region,
            )
            ir = build_manual_ir_from_source(source)
            render_callout_ir(ir)  # Fail before invoking Pandoc on corrupt IR.
            protected[token] = ir
        except ValueError as exc:
            raise WebPresentationError(str(exc)) from exc
        return f"<p>{token}</p>"

    return _WEB_CALLOUT_TABLE_RE.sub(replace, html_text), protected


def restore_web_callouts_after_pandoc(
    markdown_text: str,
    protected: dict[str, ManualIR],
) -> str:
    """Restore each protected callout exactly once, failing closed on drift."""
    restored = markdown_text
    for token, ir in protected.items():
        try:
            callout_html = render_callout_ir(ir)
        except ValueError as exc:
            raise WebPresentationError(str(exc)) from exc
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
    # The frozen figure target owns the preface convention. Other targets keep
    # the first included page selected by their source manifest.
    if not supports_figure_contract(source_path, data):
        return should_include_web_page(source_path, contract=data)
    pattern = str(data["profiles"][WEB_PRESENTATION_PROFILE]["entry_source_pattern"])
    return fnmatch.fnmatch(source_path.stem.lower(), pattern.lower())


def _matches_source(source_path: Path, patterns: list[str]) -> bool:
    stem = source_path.stem.lower()
    return any(fnmatch.fnmatch(stem, pattern.lower()) for pattern in patterns)


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


def _append_markup(target: Tag, markup: str) -> None:
    parsed = BeautifulSoup(markup, "html.parser")
    for child in list(parsed.contents):
        target.append(child.extract())


def _transform_product_overview(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    contract: dict[str, Any],
    composites: WebCompositeContext,
) -> None:
    overview = contract["product_overview"]
    try:
        instance_id = str(overview.get("instance_id") or "").strip()
        if not instance_id:
            raise WebPresentationError(
                "product_overview.instance_id must name a versioned target instance"
            )
        instance = resolve_overview_instance(
            model=composites.model,
            region=composites.region,
            instance_id=instance_id,
        )
    except Exception as exc:
        raise WebPresentationError(f"{source_path}: {exc}") from exc
    transform_overview(
        soup,
        source_path=source_path,
        instance=instance,
        composites=composites,
        error_type=WebPresentationError,
    )


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
    composites: WebCompositeContext,
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
    composites.append_semantic(
        soup=soup,
        figure=figure,
        semantic=stage,
        component=spec,
        source_path=source_path,
        image_key=str(spec["image_key"]),
    )
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
    composites: WebCompositeContext,
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
            composites=composites,
        )


def _transform_reference_figure(
    soup: BeautifulSoup,
    *,
    image: Tag,
    spec: dict[str, Any],
    source_path: Path,
    composites: WebCompositeContext,
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
    figure = soup.new_tag(
        "figure",
        attrs={
            "class": ["hb-reference-figure"],
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
    composites.append_reference(
        soup=soup,
        figure=figure,
        semantic=semantic,
        component=spec,
        source_path=source_path,
        caption_labels=caption_labels,
    )
    image["class"] = [*image.get("class", []), "hb-composite-art"]
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
    composites: WebCompositeContext,
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
            composites=composites,
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
            f"{source_path}: web preface is missing its leading language inventory "
            "or governed IMPORTANT heading"
        )
    leading_text = first_block.get_text(" ", strip=True)
    if _PREFACE_LANGUAGE_INVENTORY_RE.fullmatch(leading_text):
        first_block.decompose()
        return

    # A reseeded review page is a valid de-templated carrier: ``only:: not
    # latex`` is flattened and its web-only language inventory may be absent,
    # while the governed bold IMPORTANT marker remains the first visible block.
    # Accept that exact shape without deleting the live marker; arbitrary prose
    # still fails closed so a real preface-order drift cannot pass silently.
    strong_children = first_block.find_all("strong", recursive=False)
    meaningful_children = [
        child
        for child in first_block.contents
        if not (isinstance(child, NavigableString) and not child.strip())
    ]
    if (
        len(strong_children) == 1
        and len(meaningful_children) == 1
        and meaningful_children[0] is strong_children[0]
        and strong_children[0].get_text(" ", strip=True) == leading_text
        and _PREFACE_REVIEW_HEADING_RE.fullmatch(leading_text)
    ):
        return

    raise WebPresentationError(
        f"{source_path}: unexpected web preface leading block: {leading_text!r}"
    )


def transform_web_fragment(
    html_fragment: str,
    *,
    source_path: Path,
    contract: dict[str, Any] | None = None,
    composite_manifest: WebCompositeManifest | None = None,
    model: str | None = None,
    region: str | None = None,
    language: str | None = None,
    declared_troubleshooting: bool = False,
    declared_lcd_icons: bool = False,
) -> str:
    """Render declared semantics, then apply target-governed figure composition."""
    soup = BeautifulSoup(html_fragment, "html.parser")
    has_specifications = transform_specification_tables(
        soup, source_path=source_path, language=language, error_type=WebPresentationError,
        model=model, region=region,
    )
    has_troubleshooting = transform_troubleshooting_tables(
        soup, source_path=source_path, declared_page=declared_troubleshooting,
        language=language, model=model, region=region,
        error_type=WebPresentationError,
    )
    has_lcd = transform_lcd_icon_tables(
        soup, source_path=source_path, declared_page=declared_lcd_icons,
        language=language, model=model, region=region,
        error_type=WebPresentationError,
    )
    semantic_fragment = str(soup) if has_specifications or has_troubleshooting or has_lcd else html_fragment
    data = contract or load_web_manual_contract()
    preface = data["preface"]
    overview = data["product_overview"]
    operations = data["operations"]
    fcc = data["fcc"]
    meaning_symbols = data["meaning_symbols"]
    warranty = data["warranty"]
    in_the_box = data["in_the_box"]
    reference_figures = data["reference_figures"]
    app_download = data["app_download"]
    app_inline_controls = data["app_inline_controls"]
    is_preface = _matches_source(source_path, list(preface["source_patterns"]))
    is_overview = _matches_source(source_path, list(overview["source_patterns"]))
    is_operations = _matches_source(source_path, list(operations["source_patterns"]))
    is_fcc = _matches_source(source_path, list(fcc["source_patterns"]))
    is_meaning_symbols = _matches_source(
        source_path,
        list(meaning_symbols["source_patterns"]),
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
        or is_meaning_symbols
        or is_warranty
        or is_in_the_box
        or is_reference_page
        or is_app_download
        or is_app_inline_controls
    ):
        return semantic_fragment
    if not supports_figure_contract(source_path, data):
        return semantic_fragment

    composites = WebCompositeContext(composite_manifest, model, region, WebPresentationError)
    if is_preface:
        _transform_preface(soup, source_path=source_path)
    if is_overview:
        _transform_product_overview(
            soup,
            source_path=source_path,
            contract=data,
            composites=composites,
        )
    if is_operations:
        _transform_operations(
            soup,
            source_path=source_path,
            contract=data,
            composites=composites,
        )
    if is_fcc:
        transform_fcc(
            soup,
            source_path=source_path,
            config=fcc,
            error_type=WebPresentationError,
            language=language,
        )
    if is_meaning_symbols:
        transform_symbol_signal_table(
            soup,
            source_path=source_path,
            expected_body_rows=int(meaning_symbols["signal_row_count"]),
            error_type=WebPresentationError,
        )
        _transform_meaning_symbols_table(soup, source_path=source_path)
    if is_warranty:
        _transform_warranty(
            soup,
            source_path=source_path,
            expected_sections=int(warranty["section_count"]),
            expected_years=[str(value) for value in warranty["period_years"]],
        )
    if is_in_the_box:
        transform_inbox(
            soup, source_path=source_path, language=language or "und",
            model=model, region=region, error_type=WebPresentationError,
        )
    if is_app_download:
        _transform_app_download(soup, source_path=source_path, contract=data)
    if is_app_inline_controls:
        _transform_app_inline_controls(soup, source_path=source_path, contract=data)
    if is_reference_page:
        _transform_reference_figures(
            soup,
            source_path=source_path,
            contract=data,
            composites=composites,
        )
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
