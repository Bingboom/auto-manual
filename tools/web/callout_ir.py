"""Public ManualIR replay for the prepared Web callout/Pandoc handoff."""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from tools.component_specs.adapters import web_callout_classes
from tools.component_specs.model import ComponentSpec
from tools.component_specs.registry import require_valid_component_spec
from tools.manual_ir import ManualIR, ManualIRValidationError, validate_manual_ir
from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.web_callouts import decode_callout_payload


def render_callout_component(spec: ComponentSpec, carrier_html: str) -> str:
    """Return one embedded rich callout after direct semantic agreement checks."""

    spec = require_valid_component_spec(spec)
    soup = BeautifulSoup(carrier_html, "html.parser")
    roots = [node for node in soup.contents if isinstance(node, Tag) or str(node).strip()]
    table = soup.select_one("table.manual-callout-table")
    if len(roots) != 1 or roots[0] is not table or table is None:
        raise ValueError(f"{spec.source_ref}: invalid embedded callout carrier")
    rows = table.find_all("tr")
    cells = rows[0].find_all(["th", "td"], recursive=False) if len(rows) == 1 else []
    if (
        len(cells) != 2
        or "manual-callout-label" not in cells[0].get("class", [])
        or "manual-callout-body" not in cells[1].get("class", [])
    ):
        raise ValueError(f"{spec.source_ref}: embedded callout carrier geometry changed")
    expected_items = (
        [str(value) for value in spec.slot("items").content]
        if any(slot.role == "items" for slot in spec.slots)
        else []
    )
    if (
        cells[0].get_text(" ", strip=True) != str(spec.slot("label").content)
        or cells[1].get_text("\n", strip=True) != str(spec.slot("body").content)
        or [item.get_text(" ", strip=True) for item in cells[1].select("li")]
        != expected_items
        or web_callout_classes(spec)["table"] not in table.get("class", [])
    ):
        raise ValueError(f"{spec.source_ref}: embedded callout semantics changed")
    return str(table)


def render_callout_ir(ir: ManualIR) -> str:
    """Consume serialized or in-memory IR without reopening source HTML/RST.

    Envelope integrity does not prove an extension's semantics agree with its
    markup. Validate both before returning the original authored bytes.
    """
    if not isinstance(ir, ManualIR):
        raise ValueError("expected public ManualIR for Web callout replay")
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    if (ir.metadata.get("projection") != "web-callout" or len(ir.pages) != 1
            or len(ir.pages[0].blocks) != 1):
        raise ValueError("expected a single-block web-callout projection")
    block = ir.pages[0].blocks[0]
    payload = block.payload
    if (block.kind != "web_callout" or not isinstance(payload, dict)
            or not isinstance(payload.get("table_html"), str)
            or not isinstance(payload.get("component_spec"), dict)):
        raise ValueError(f"{block.source_ref}: incomplete Web callout payload")
    spec = require_valid_component_spec(ComponentSpec.from_dict(payload["component_spec"]))
    decoded = decode_callout_payload(
        payload["table_html"], source_ref=ir.pages[0].source_ref,
        declaration=payload.get("declaration"),
    )
    if (spec.language != ir.pages[0].language
            or value_sha256(decoded) != value_sha256(payload)):
        raise ValueError(f"{block.source_ref}: callout semantics/assets do not match retained markup")
    return payload["table_html"]


__all__ = [
    "render_callout_component",
    "render_callout_ir",
]
