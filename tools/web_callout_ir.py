"""Public ManualIR replay for the prepared Web callout/Pandoc handoff."""
from __future__ import annotations

from tools.component_specs.model import ComponentSpec
from tools.component_specs.registry import require_valid_component_spec
from tools.manual_ir import ManualIR, ManualIRValidationError, validate_manual_ir
from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.web_callouts import decode_callout_payload


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
    decoded = decode_callout_payload(payload["table_html"], source_ref=ir.pages[0].source_ref)
    if (spec.language != ir.pages[0].language
            or value_sha256(decoded) != value_sha256(payload)):
        raise ValueError(f"{block.source_ref}: callout semantics/assets do not match retained markup")
    return payload["table_html"]
