"""Responsive Web adapter for the renderer-neutral Inbox ComponentSpec."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.inbox import COMPONENT_ID
from tools.component_specs.model import ComponentSpec
from tools.component_specs.registry import require_valid_component_spec
from tools.component_specs.theme import require_component_theme_roles
from tools.manual_ir import (
    ManualIR, ManualIRValidationError, build_manual_ir_from_source, validate_manual_ir,
)
from tools.manual_ir.web_inbox import decode_inbox_payload, load_web_inbox_source
from tools.web_component_carriers import validate_inbox_carrier


def render_inbox_component(
    spec: ComponentSpec,
    carrier_html: str,
    *,
    source_ref: str | None = None,
) -> str:
    """Render one embedded Inbox spec from its non-authoritative rich carrier."""
    spec = require_component_theme_roles(require_valid_component_spec(spec))
    identity = source_ref or spec.source_ref
    _carrier, projection, source_cells, tip_cells = validate_inbox_carrier(
        spec, carrier_html, source_ref=identity)

    soup = BeautifulSoup("", "html.parser")
    composition = soup.new_tag(
        "figure",
        attrs={
            "class": projection["composition_class"],
            "aria-label": projection["accessibility_label"],
            "data-component-id": COMPONENT_ID,
        },
    )
    grid = soup.new_tag("ol", attrs={"class": projection["grid_class"]})
    for card_data, cell in zip(projection["cards"], source_cells, strict=True):
        image = cell.find("img")
        if not isinstance(image, Tag):  # parser already checked; defensive adapter edge
            raise ValueError(f"{identity}: inbox image disappeared during projection")
        image.extract()
        image["src"] = card_data["image_ref"]
        image["alt"] = card_data["alt"]
        image["class"] = [*image.get("class", []), projection["art_class"]]
        for attribute in ("style", "width", "height"):
            image.attrs.pop(attribute, None)

        card = soup.new_tag(
            "li",
            attrs={
                "class": projection["card_class"],
                "data-item-number": str(card_data["number"]),
            },
        )
        label = soup.new_tag("div", attrs={"class": projection["label_class"]})
        for child in list(cell.contents):
            label.append(child.extract())
        card.append(image)
        card.append(label)
        grid.append(card)

    tip = soup.new_tag("div", attrs={"class": projection["tip_class"], "role": "note"})
    tip_label = soup.new_tag("div", attrs={"class": "hb-inbox-tip-label"})
    tip_body = soup.new_tag("div", attrs={"class": "hb-inbox-tip-body"})
    for child in list(tip_cells[0].contents):
        tip_label.append(child.extract())
    for child in list(tip_cells[1].contents):
        tip_body.append(child.extract())
    tip.append(tip_label)
    tip.append(tip_body)

    composition.append(grid)
    composition.append(tip)
    return str(composition)


def render_inbox_ir(ir: ManualIR) -> str:
    """Replay the owned composite only after envelope and markup agreement pass."""
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if (ir.metadata.get("projection") != "web-inbox" or len(ir.pages) != 1
            or len(ir.pages[0].blocks) != 1):
        raise ValueError("expected a single-block web-inbox projection")
    source_path = Path(ir.pages[0].source_ref)
    source = decode_inbox_payload(
        ir.pages[0].blocks[0], source_path=source_path, language=ir.pages[0].language,
    )
    return render_inbox_component(
        source.spec,
        str(source.inbox_table) + str(source.tip_table),
        source_ref=str(source_path),
    )


def transform_inbox(
    soup: BeautifulSoup, *, source_path: Path, language: str,
    error_type: type[Exception], model: str | None = None, region: str | None = None,
) -> None:
    """Actual Web consumer; leave caller tags untouched until full replay succeeds."""
    try:
        source = load_web_inbox_source(
            str(soup), source_path=source_path, language=language, model=model, region=region,
        )
        html = render_inbox_ir(build_manual_ir_from_source(source))
    except ValueError as exc:
        raise error_type(str(exc)) from exc
    # The validated input is unchanged; these are the exact source boundaries
    # used by parse_inbox_html, not another content/ComponentSpec read.
    inbox = soup.find("h1").find_next_sibling()
    tip = inbox.find_next_sibling()
    inbox.replace_with(BeautifulSoup(html, "html.parser").figure)
    tip.decompose()


__all__ = ["render_inbox_component", "transform_inbox", "render_inbox_ir"]
