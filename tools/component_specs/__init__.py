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

__all__ = [
    "ComponentAsset",
    "ComponentSlot",
    "ComponentSpec",
    "ComponentSpecError",
    "adapter_binding",
    "callout_component_spec",
    "callout_spec_from_legacy_notice",
    "load_component_registry",
    "require_valid_component_spec",
    "validate_component_registry",
    "validate_component_spec",
]
