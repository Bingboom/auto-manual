"""Renderer-neutral component instances and adapter contracts."""

from .callout import callout_component_spec, callout_spec_from_legacy_notice
from .fcc import fcc_component_spec, fcc_spec_from_legacy_payload
from .fcc_adapters import (
    idml_fcc_payload,
    latex_fcc_projection,
    web_fcc_projection,
    word_fcc_projection,
)
from .inbox import inbox_component_spec, inbox_spec_from_legacy_payload
from .inbox_adapters import (
    idml_inbox_payload,
    latex_inbox_projection,
    web_inbox_projection,
    word_inbox_projection,
)
from .model import ComponentAsset, ComponentSlot, ComponentSpec, ComponentSpecError
from .overview import overview_component_spec, overview_spec_from_blocks
from .overview_adapters import (
    idml_overview_projection,
    latex_overview_projection,
    web_overview_projection,
    word_overview_projection,
)
from .overview_instance import (
    load_overview_instance_registry,
    resolve_overview_instance,
)
from .registry import (
    adapter_binding,
    load_component_registry,
    require_valid_component_spec,
    validate_component_registry,
    validate_component_spec,
)
from .spec_table import spec_table_component_spec
from .theme import load_manual_theme, validate_manual_theme

__all__ = [
    "ComponentAsset",
    "ComponentSlot",
    "ComponentSpec",
    "ComponentSpecError",
    "adapter_binding",
    "callout_component_spec",
    "callout_spec_from_legacy_notice",
    "fcc_component_spec",
    "fcc_spec_from_legacy_payload",
    "idml_fcc_payload",
    "idml_inbox_payload",
    "idml_overview_projection",
    "inbox_component_spec",
    "inbox_spec_from_legacy_payload",
    "latex_fcc_projection",
    "latex_inbox_projection",
    "latex_overview_projection",
    "load_component_registry",
    "load_manual_theme",
    "load_overview_instance_registry",
    "overview_component_spec",
    "overview_spec_from_blocks",
    "require_valid_component_spec",
    "resolve_overview_instance",
    "spec_table_component_spec",
    "validate_component_registry",
    "validate_component_spec",
    "validate_manual_theme",
    "web_fcc_projection",
    "web_inbox_projection",
    "web_overview_projection",
    "word_fcc_projection",
    "word_inbox_projection",
    "word_overview_projection",
]
