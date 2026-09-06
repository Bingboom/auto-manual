"""Direct Web dispatch for ComponentSpecs embedded in whole-document flow."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping

from tools.component_specs.fcc import COMPONENT_ID as FCC_ID
from tools.component_specs.inbox import COMPONENT_ID as INBOX_ID
from tools.component_specs.lcd_mode import LCD_MODE_COMPONENT_ID
from tools.component_specs.manual_tables import (
    LCD_ICON_COMPONENT_ID,
    SYMBOL_ICON_COMPONENT_ID,
    SYMBOL_SIGNAL_COMPONENT_ID,
    TROUBLESHOOTING_COMPONENT_ID,
)
from tools.component_specs.operation import OPERATION_COMPONENT_ID
from tools.component_specs.overview import COMPONENT_ID as OVERVIEW_ID
from tools.component_specs.overview_instance import resolve_overview_instance
from tools.component_specs.spec_table import COMPONENT_ID as SPEC_ID
from tools.component_specs.callout import COMPONENT_ID as CALLOUT_ID
from tools.component_specs.warranty import (
    WARRANTY_LEAD_COMPONENT_ID,
    WARRANTY_SECTION_COMPONENT_ID,
    WARRANTY_YEARS_COMPONENT_ID,
)
from tools.manual_ir.components import component_spec_from_flow_node
from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION, flow_nodes_to_html
from tools.web_callout_ir import render_callout_component
from tools.web_composite_manifest import WebCompositeManifest
from tools.web_composite_presentation import WebCompositeContext
from tools.web_composite_presentation import supports_figure_contract
from tools.web_fcc_component import render_fcc_component
from tools.web_inbox_component import render_inbox_component
from tools.web_lcd_mode_component import render_lcd_mode_component
from tools.web_manual_table_components import render_manual_table_component
from tools.web_operation_component import render_operation_component
from tools.web_overview_component import render_overview_component
from tools.web_presentation import WebPresentationError
from tools.web_spec_component import render_specification_component
from tools.web_warranty_component import render_warranty_component


def _carrier_html(node: Mapping[str, object]) -> str:
    raw = node.get("carrier_flow")
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError("embedded Web component requires carrier_flow")
    roots = []
    for candidate in raw:
        if not isinstance(candidate, Mapping):
            raise ValueError("embedded Web component carrier must contain mappings")
        root = deepcopy(dict(candidate))
        root["schema_version"] = FLOW_V2_SCHEMA_VERSION
        roots.append(root)
    return flow_nodes_to_html(roots)


def render_embedded_web_component(
    node: Mapping[str, object],
    *,
    source_path: Path,
    model: str,
    region: str,
    language: str,
    composite_manifest: WebCompositeManifest | None,
    contract: Mapping[str, object],
) -> str:
    """Dispatch one validated component without a source-projector round trip."""

    spec = component_spec_from_flow_node(node)
    if spec.component_id == CALLOUT_ID:
        return render_callout_component(spec, _carrier_html(node))
    if spec.component_id == SPEC_ID:
        return render_specification_component(spec, _carrier_html(node))
    if spec.component_id == INBOX_ID:
        return render_inbox_component(spec, _carrier_html(node))
    if spec.component_id == FCC_ID:
        if len(spec.assets) != 1:
            raise ValueError(f"{spec.source_ref}: FCC requires one bound mark")
        return render_fcc_component(
            spec,
            mark_path=spec.assets[0].asset_ref,
            carrier_html=_carrier_html(node),
        )
    if spec.component_id == OVERVIEW_ID:
        instance = resolve_overview_instance(model=model, region=region)
        context = WebCompositeContext(
            composite_manifest,
            model,
            region,
            language,
            WebPresentationError,
        )
        return render_overview_component(
            spec,
            _carrier_html(node),
            source_path=source_path,
            instance=instance,
            composites=context,
        )
    if spec.component_id == LCD_MODE_COMPONENT_ID:
        return render_lcd_mode_component(spec)
    if spec.component_id in {
        LCD_ICON_COMPONENT_ID,
        TROUBLESHOOTING_COMPONENT_ID,
        SYMBOL_SIGNAL_COMPONENT_ID,
        SYMBOL_ICON_COMPONENT_ID,
    }:
        return render_manual_table_component(spec)
    if spec.component_id in {
        WARRANTY_LEAD_COMPONENT_ID,
        WARRANTY_SECTION_COMPONENT_ID,
        WARRANTY_YEARS_COMPONENT_ID,
    }:
        return render_warranty_component(spec)
    if spec.component_id == OPERATION_COMPONENT_ID:
        carrier = _carrier_html(node)
        if not supports_figure_contract(source_path, dict(contract)):
            return carrier
        operations = contract.get("operations")
        figures = operations.get("figures") if isinstance(operations, Mapping) else None
        candidates = [
            candidate
            for candidate in figures or []
            if isinstance(candidate, Mapping)
            and str(candidate.get("id") or "") == str(spec.slot("operation_id").content)
        ]
        if len(candidates) != 1:
            raise ValueError(
                f"{spec.source_ref}: expected one Web operation presentation; "
                f"found {len(candidates)}"
            )
        context = WebCompositeContext(
            composite_manifest,
            model,
            region,
            language,
            WebPresentationError,
        )
        return render_operation_component(
            spec,
            carrier,
            source_path=source_path,
            presentation=candidates[0],
            composites=context,
        )
    raise ValueError(f"unregistered embedded Web component: {spec.component_id}")


__all__ = ["render_embedded_web_component"]
