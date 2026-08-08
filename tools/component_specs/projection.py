"""Project eligible Manual IR blocks into renderer-neutral ComponentSpecs."""
from __future__ import annotations

import fnmatch
from typing import Iterable

from tools.component_specs.callout import callout_spec_from_legacy_notice
from tools.component_specs.fcc import fcc_spec_from_legacy_payload
from tools.component_specs.inbox import inbox_spec_from_legacy_payload
from tools.component_specs.model import ComponentSpec
from tools.component_specs.model import ComponentSpecError
from tools.component_specs.overview import overview_spec_from_blocks
from tools.component_specs.overview_instance import resolve_overview_instance
from tools.component_specs.spec_table import spec_table_component_spec
from tools.manual_ir import ManualIR


def project_manual_ir_components(ir: ManualIR) -> tuple[ComponentSpec, ...]:
    projected: list[ComponentSpec] = []
    try:
        overview_instance = resolve_overview_instance(model=ir.model, region=ir.region)
    except ComponentSpecError:
        overview_instance = None
    for page in ir.pages:
        if overview_instance is not None and any(
            fnmatch.fnmatch(
                page.source_path.rsplit("/", 1)[-1].rsplit(".", 1)[0].casefold(),
                str(pattern).casefold(),
            )
            for pattern in overview_instance["source_patterns"]
        ):
            projected.append(
                overview_spec_from_blocks(
                    tuple((block.kind, block.payload) for block in page.blocks),
                    instance=overview_instance,
                    source_ref=page.source_ref,
                    language=page.language,
                )
            )
        for block_index, block in enumerate(page.blocks):
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
            elif block.kind == "component" and block.payload.get("kind") == "fcc":
                projected.append(
                    fcc_spec_from_legacy_payload(
                        block.payload,
                        source_ref=block.source_ref,
                        language=page.language,
                    )
                )
            elif block.kind == "component" and block.payload.get("kind") == "inbox":
                heading = next(
                    (
                        str(candidate.payload)
                        for candidate in reversed(page.blocks[:block_index])
                        if candidate.kind == "h1" and str(candidate.payload).strip()
                    ),
                    "What's in the Box",
                )
                tip_payload = next(
                    (
                        candidate.payload
                        for candidate in page.blocks[block_index + 1 :]
                        if candidate.kind == "component"
                        and isinstance(candidate.payload, dict)
                        and candidate.payload.get("kind") == "notice"
                    ),
                    {},
                )
                projected.append(
                    inbox_spec_from_legacy_payload(
                        block.payload,
                        source_ref=block.source_ref,
                        language=page.language,
                        accessibility_label=heading,
                        tip_label=str(tip_payload.get("label") or "TIP"),
                        tip_body="\n".join(
                            str(value) for value in tip_payload.get("texts") or []
                        )
                        or "See the source-authored tip copy.",
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
