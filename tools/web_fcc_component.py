"""Responsive Web adapter for the renderer-neutral FCC ComponentSpec."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from tools.component_specs.fcc import COMPONENT_ID
from tools.component_specs.fcc_adapters import web_fcc_projection
from tools.component_specs.model import ComponentSpec
from tools.component_specs.registry import require_valid_component_spec
from tools.component_specs.theme import require_component_theme_roles
from tools.manual_ir import ManualIR, build_manual_ir_from_source
from tools.manual_ir.web_fcc import decode_fcc_ir, load_web_fcc_source
from tools.web_component_carriers import validate_fcc_carrier
from tools.web_fcc_markup import append_fcc_blocks, fcc_opening_copy


def render_fcc_component(
    spec: ComponentSpec,
    *,
    mark_path: str,
    carrier_html: str | None = None,
) -> str:
    """Render one embedded FCC spec without reopening its source carrier."""

    spec = require_component_theme_roles(require_valid_component_spec(spec))
    projection = web_fcc_projection(spec)
    retained_whitespace = (
        validate_fcc_carrier(spec, carrier_html) if carrier_html is not None else ""
    )
    soup = BeautifulSoup("", "html.parser")
    composition = soup.new_tag(
        "figure",
        attrs={
            "class": projection["composition_class"],
            "aria-label": projection["accessibility_label"],
            "data-component-id": COMPONENT_ID,
        },
    )
    grid = soup.new_tag("div", attrs={"class": projection["grid_class"]})
    left = soup.new_tag(
        "div",
        attrs={
            "class": [projection["column_class"], "hb-fcc-column-left"],
        },
    )
    right = soup.new_tag(
        "div",
        attrs={
            "class": [projection["column_class"], "hb-fcc-column-right"],
        },
    )
    opening_row = soup.new_tag("div", attrs={"class": "hb-fcc-opening"})
    logo = soup.new_tag(
        "img",
        attrs={
            "class": projection["mark_class"],
            "src": mark_path,
            "alt": projection["accessibility_label"],
            "loading": "lazy",
        },
    )
    opening_copy = soup.new_tag("div", attrs={"class": "hb-fcc-opening-copy"})
    opening_copy.append(fcc_opening_copy(soup, projection["opening_copy"]))
    opening_row.append(logo)
    opening_row.append(opening_copy)
    left.append(opening_row)
    append_fcc_blocks(soup, left, projection["left_blocks"])
    append_fcc_blocks(soup, right, projection["right_blocks"])
    grid.append(left)
    grid.append(right)
    composition.append(grid)

    return str(composition) + retained_whitespace


def render_fcc_ir(ir: ManualIR) -> str:
    spec, mark_path = decode_fcc_ir(ir)
    return render_fcc_component(spec, mark_path=mark_path)


def transform_fcc(
    soup: BeautifulSoup, *, source_path: Path, config: Mapping[str, Any],
    error_type: type[Exception], language: str | None = None,
    model: str | None = None, region: str | None = None,
) -> None:
    try:
        source = load_web_fcc_source(
            str(soup), source_path=source_path, config=config,
            language=language, model=model, region=region,
        )
        rendered = render_fcc_ir(build_manual_ir_from_source(source))
    except ValueError as exc:
        raise error_type(str(exc)) from exc
    # The parser owns all following FCC siblings; mutate only after replay.
    heading = soup.find("h1")
    for node in list(heading.find_next_siblings()):
        node.decompose()
    heading.insert_after(BeautifulSoup(rendered, "html.parser").figure)


__all__ = ["render_fcc_component", "transform_fcc", "render_fcc_ir"]
