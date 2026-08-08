"""Project eligible Manual IR blocks into renderer-neutral ComponentSpecs."""
from __future__ import annotations

from typing import Iterable

from tools.component_specs.callout import callout_spec_from_legacy_notice
from tools.component_specs.model import ComponentSpec
from tools.component_specs.spec_table import spec_table_component_spec
from tools.manual_ir import ManualIR


def project_manual_ir_components(ir: ManualIR) -> tuple[ComponentSpec, ...]:
    projected: list[ComponentSpec] = []
    for page in ir.pages:
        for block in page.blocks:
            if not isinstance(block.payload, dict):
                continue
            if block.kind == "component" and block.payload.get("kind") == "notice":
                projected.append(
                    callout_spec_from_legacy_notice(
                        block.payload,
                        source_ref=block.source_ref,
                        language=page.language,
                    )
                )
            elif block.kind == "data" and block.payload.get("kind") == "spec_section":
                projected.append(
                    spec_table_component_spec(
                        section_title=str(block.payload.get("title") or ""),
                        rows=block.payload.get("rows") or [],
                        source_ref=block.source_ref,
                        language=page.language,
                    )
                )
    return tuple(projected)


def component_ids(specs: Iterable[ComponentSpec]) -> tuple[str, ...]:
    return tuple(spec.component_id for spec in specs)


__all__ = ["component_ids", "project_manual_ir_components"]
