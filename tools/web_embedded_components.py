"""Direct Web dispatch for ComponentSpecs embedded in whole-document flow."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Mapping

from tools.component_specs.fcc import COMPONENT_ID as FCC_ID
from tools.component_specs.inbox import COMPONENT_ID as INBOX_ID
from tools.component_specs.overview import COMPONENT_ID as OVERVIEW_ID
from tools.component_specs.overview_instance import resolve_overview_instance
from tools.component_specs.spec_table import COMPONENT_ID as SPEC_ID
from tools.component_specs.callout import COMPONENT_ID as CALLOUT_ID
from tools.manual_ir.components import component_spec_from_flow_node
from tools.manual_ir.flow import FLOW_V2_SCHEMA_VERSION, flow_nodes_to_html
from tools.web_callout_ir import render_callout_component
from tools.web_composite_manifest import WebCompositeManifest
from tools.web_composite_presentation import WebCompositeContext
from tools.web_fcc_component import render_fcc_component
from tools.web_inbox_component import render_inbox_component
from tools.web_overview_component import render_overview_component
from tools.web_presentation import WebPresentationError
from tools.web_spec_component import render_specification_component


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
    raise ValueError(f"unregistered embedded Web component: {spec.component_id}")


__all__ = ["render_embedded_web_component"]
