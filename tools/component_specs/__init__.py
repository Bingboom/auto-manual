"""Renderer-neutral component instances and adapter contracts."""

from .callout import callout_component_spec, callout_spec_from_legacy_notice
from .model import ComponentAsset, ComponentSlot, ComponentSpec, ComponentSpecError
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
    "load_component_registry",
    "load_manual_theme",
    "require_valid_component_spec",
    "spec_table_component_spec",
    "validate_component_registry",
    "validate_component_spec",
    "validate_manual_theme",
]
