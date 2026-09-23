"""Project eligible Manual IR blocks into renderer-neutral ComponentSpecs."""
from __future__ import annotations

import fnmatch
from typing import Iterable

from tools.component_specs.callout import callout_spec_from_legacy_notice
from tools.component_specs.fcc import fcc_spec_from_payload
from tools.component_specs.inbox import inbox_spec_from_payload
from tools.component_specs.model import ComponentSpec
from tools.component_specs.model import ComponentSpecError
from tools.component_specs.overview import overview_spec_from_blocks
from tools.component_specs.overview_target import find_overview_instance
from tools.component_specs.spec_table import spec_table_component_spec
from tools.manual_ir import ManualIR


def governed_overview_source_refs(ir: ManualIR) -> frozenset[str]:
    """Return Overview-owned source refs without parsing their page shape."""
    overview_instance = find_overview_instance(model=ir.model, region=ir.region)
    if overview_instance is None:
        return frozenset()
    governed: set[str] = set()
    for page in ir.pages:
        source_stem = page.source_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if not any(
            fnmatch.fnmatch(source_stem.casefold(), str(pattern).casefold())
            for pattern in overview_instance["source_patterns"]
        ):
            continue
        language = str(page.language or "").casefold()
        for view in overview_instance["views"]:
            locales = [
                str(mapping.get("locale") or "").casefold()
                for mapping in view["composite_locales"]
            ]
            if locales.count(language) != 1:
                raise ComponentSpecError(
                    f"{page.source_ref}: overview language {page.language!r} must be "
                    f"declared once for view {view['id']!r}; got {locales!r}"
                )
        governed.add(page.source_ref)
    return frozenset(governed)


def project_overview_components(ir: ManualIR) -> tuple[ComponentSpec, ...]:
    """Project semantic specs for governed two-view Overview source pages."""
    governed = governed_overview_source_refs(ir)
    if not governed:
        return ()
    overview_instance = find_overview_instance(model=ir.model, region=ir.region)
    if overview_instance is None:  # pragma: no cover - guarded above
        return ()
    projected: list[ComponentSpec] = []
    for page in ir.pages:
        if page.source_ref not in governed:
            continue
        projected.append(
            overview_spec_from_blocks(
                tuple((block.kind, block.payload) for block in page.blocks),
                instance=overview_instance,
                source_ref=page.source_ref,
                language=page.language,
            )
        )
    return tuple(projected)


def project_manual_ir_components(ir: ManualIR) -> tuple[ComponentSpec, ...]:
    if ir.metadata.get("projection") == "whole-document-components/v1":
        from tools.manual_ir.components import component_specs_in_flow

        component_registry = ir.metadata.get("component_registry")
        return component_specs_in_flow(
            tuple(
                block.payload
                for page in ir.pages
                for block in page.blocks
                if block.kind == "flow"
            ),
            component_registry=(
                component_registry
                if isinstance(component_registry, dict)
                else None
            ),
        )

    projected: list[ComponentSpec] = []
    overview_by_source = {
        spec.source_ref: spec
        for spec in project_overview_components(ir)
    }
    for page in ir.pages:
        overview = overview_by_source.get(page.source_ref)
        if overview is not None:
            projected.append(overview)
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
                    fcc_spec_from_payload(
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
                    None,
                )
                tip_payload = next(
                    (
                        candidate.payload
                        for candidate in page.blocks[block_index + 1 :]
                        if candidate.kind == "component"
                        and isinstance(candidate.payload, dict)
                        and candidate.payload.get("kind") == "notice"
                    ),
                    None,
                )
                if heading is None or tip_payload is None:
                    raise ComponentSpecError(
                        f"{block.source_ref}: inbox requires its source-authored H1 "
                        "and adjacent notice"
                    )
                tip_label = str(tip_payload.get("label") or "").strip()
                tip_body = "\n".join(
                    str(value).strip()
                    for value in tip_payload.get("texts") or []
                    if str(value).strip()
                )
                if not tip_label or not tip_body:
                    raise ComponentSpecError(
                        f"{block.source_ref}: inbox notice requires a label and body"
                    )
                projected.append(
                    inbox_spec_from_payload(
                        block.payload,
                        source_ref=block.source_ref,
                        language=page.language,
                        accessibility_label=heading,
                        tip_label=tip_label,
                        tip_body=tip_body,
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
