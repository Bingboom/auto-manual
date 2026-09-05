"""Render the validated public ManualIR Web specification projection."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec, ComponentSpecError
from tools.component_specs.registry import require_valid_component_spec
from tools.component_specs.spec_table import web_spec_table_projection
from tools.component_specs.theme import require_component_theme_roles
from tools.component_specs.web_source import superscript_circled_references
from tools.manual_ir import (
    ManualIR,
    ManualIRValidationError,
    build_manual_ir_from_source,
    validate_manual_ir,
)
from tools.manual_ir.web_specs import load_web_spec_source


def _add_classes(tag: Tag, classes: str) -> None:
    tag["class"] = list(dict.fromkeys([*tag.get("class", []), *classes.split()]))


def render_specification_ir(ir: ManualIR) -> list[str]:
    """Replay the scoped projection without reopening or reparsing source RST.

    Validate the envelope and each owned component before returning any output.
    The original inline HTML is a presentation payload, not a second source read.
    """
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if ir.metadata.get("projection") != "web-specifications" or len(ir.pages) != 1:
        raise ValueError("expected a single-page web-specifications projection")
    rendered = []
    for block in ir.pages[0].blocks:
        payload = block.payload
        if block.kind != "web_specification" or not isinstance(payload, dict):
            raise ValueError(f"{block.source_ref}: unsupported Web specification block")
        if not isinstance(payload.get("component_spec"), dict) or not all(
            isinstance(payload.get(key), str) for key in ("heading_html", "table_html")
        ):
            raise ValueError(
                f"{block.source_ref}: incomplete Web specification payload"
            )
        spec = require_component_theme_roles(
            require_valid_component_spec(
                ComponentSpec.from_dict(payload["component_spec"])
            )
        )
        projection = web_spec_table_projection(spec)
        soup = BeautifulSoup(
            payload["heading_html"] + payload["table_html"], "html.parser"
        )
        heading = soup.select_one("h2.hb-spec-section")
        table = soup.find("table")
        title = heading.select_one(".hb-spec-section-text") if heading else None
        if heading is None or table is None or title is None:
            raise ValueError(
                f"{block.source_ref}: missing declared heading or table markup"
            )
        source_rows = [
            row.find_all(["th", "td"], recursive=False)
            for row in table.select("tbody > tr")
        ]
        # Semantic groups were decoded by the source adapter. Check that the
        # retained markup still corresponds to them before any presentation.
        _validate_markup(spec, source_rows, title, block.source_ref)
        # Only the declared decorative marker goes away. Links/emphasis and
        # any other authored heading content stay in the document outline.
        for bullet in heading.select(".hb-spec-bullet"):
            bullet.decompose()
        title.unwrap()
        heading["class"] = [
            value for value in heading.get("class", []) if value != "hb-spec-section"
        ]
        if not heading["class"]:
            del heading["class"]

        for colgroup in table.find_all("colgroup", recursive=False):
            colgroup.decompose()
        colgroup = soup.new_tag("colgroup")
        for role in ("label", "value"):
            colgroup.append(soup.new_tag("col", attrs={"class": f"hb-spec-col-{role}"}))
        table.insert(0, colgroup)
        table.attrs.pop("style", None)
        _add_classes(table, projection["table_classes"])

        row_index = 0
        for group in projection["groups"]:
            label = source_rows[row_index][0]
            label.name = "th"
            label["scope"] = "row"
            label.attrs.pop("style", None)
            _add_classes(label, projection["label_classes"])
            span = group["label_rowspan"]
            if span > 1:
                label["rowspan"] = str(span)
            superscript_circled_references(soup, label)
            for offset, _value in enumerate(group["values"]):
                cells = source_rows[row_index + offset]
                if offset and len(cells) == 2:
                    # The registered blank-label continuation now has a real
                    # rowspan; only its empty placeholder cell is removed.
                    cells[0].decompose()
                value = cells[-1]
                value.name = "td"
                value.attrs.pop("style", None)
                _add_classes(value, projection["value_classes"])
                superscript_circled_references(soup, value)
            row_index += span

        composition = soup.new_tag(
            "figure",
            attrs={
                "class": projection["composition_class"],
                "aria-label": str(spec.slot("section_title").content),
            },
        )
        table.replace_with(composition)
        composition.append(table)
        rendered.append(str(soup))
    return rendered


def _validate_markup(
    spec: ComponentSpec, rows: list[list[Tag]], title: Tag, source_ref: str
) -> None:
    groups = spec.slot("rows").content
    expected = [
        (str(group["label"]) if index == 0 else "", str(value["text"]))
        for group in groups
        for index, value in enumerate(group["values"])
    ]
    actual = [
        (
            cells[0].get_text("\n", strip=True) if len(cells) == 2 else "",
            cells[-1].get_text("\n", strip=True),
        )
        for cells in rows
        if cells
    ]
    if (
        any(len(cells) not in (1, 2) for cells in rows)
        or actual != expected
        or title.get_text(" ", strip=True) != spec.slot("section_title").content
    ):
        raise ValueError(
            f"{source_ref}: component semantics do not match retained markup"
        )


def transform_specification_tables(
    soup: BeautifulSoup,
    *,
    source_path: Path,
    language: str | None,
    error_type: type[Exception],
    model: str | None = None,
    region: str | None = None,
) -> bool:
    """Actual Web entry: assemble and consume IR, then apply the complete result."""
    try:
        source = load_web_spec_source(
            str(soup),
            source_path=source_path,
            language=language,
            model=model,
            region=region,
        )
        if source is None:
            return False
        rendered = render_specification_ir(build_manual_ir_from_source(source))
    except (ValueError, ComponentSpecError) as exc:
        raise error_type(f"{source_path}: {exc}") from exc
    headings = soup.select("h2.hb-spec-section")
    for heading, fragment in zip(headings, rendered, strict=True):
        table = heading.find_next_sibling()
        replacement = BeautifulSoup(fragment, "html.parser")
        heading.replace_with(replacement)
        table.decompose()
    return True
