"""Project eligible Manual IR blocks into renderer-neutral ComponentSpecs."""
from __future__ import annotations

from typing import Iterable

from tools.component_specs.callout import callout_spec_from_legacy_notice
from tools.component_specs.model import ComponentSpec
from tools.manual_ir import ManualIR


def project_manual_ir_components(ir: ManualIR) -> tuple[ComponentSpec, ...]:
    projected: list[ComponentSpec] = []
    for page in ir.pages:
        for block in page.blocks:
            if block.kind != "component" or not isinstance(block.payload, dict):
                continue
            if block.payload.get("kind") != "notice":
                continue
            projected.append(
                callout_spec_from_legacy_notice(
                    block.payload,
                    source_ref=block.source_ref,
                    language=page.language,
                )
            )
    return tuple(projected)


def component_ids(specs: Iterable[ComponentSpec]) -> tuple[str, ...]:
    return tuple(spec.component_id for spec in specs)


__all__ = ["component_ids", "project_manual_ir_components"]
