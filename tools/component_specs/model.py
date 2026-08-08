"""Immutable renderer-neutral component instance model."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


SCHEMA_VERSION = "component-spec/v1"


class ComponentSpecError(ValueError):
    """Raised when a component instance or registry binding is invalid."""


@dataclass(frozen=True)
class ComponentSlot:
    role: str
    content_kind: str
    content: Any

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ComponentSlot":
        return cls(
            role=str(payload.get("role") or ""),
            content_kind=str(payload.get("content_kind") or ""),
            content=payload.get("content"),
        )


@dataclass(frozen=True)
class ComponentAsset:
    role: str
    asset_ref: str
    locale_policy: str

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ComponentAsset":
        return cls(
            role=str(payload.get("role") or ""),
            asset_ref=str(payload.get("asset_ref") or ""),
            locale_policy=str(payload.get("locale_policy") or ""),
        )


@dataclass(frozen=True)
class ComponentSpec:
    component_id: str
    variant: str
    source_ref: str
    language: str
    slots: tuple[ComponentSlot, ...]
    assets: tuple[ComponentAsset, ...]
    token_roles: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ComponentSpec":
        raw_slots = payload.get("slots")
        raw_assets = payload.get("assets")
        raw_tokens = payload.get("token_roles")
        raw_metadata = payload.get("metadata")
        if not isinstance(raw_slots, (list, tuple)):
            raise ComponentSpecError("ComponentSpec.slots must be a list")
        if not all(isinstance(item, Mapping) for item in raw_slots):
            raise ComponentSpecError("ComponentSpec.slots entries must be mappings")
        if not isinstance(raw_assets, (list, tuple)):
            raise ComponentSpecError("ComponentSpec.assets must be a list")
        if not all(isinstance(item, Mapping) for item in raw_assets):
            raise ComponentSpecError("ComponentSpec.assets entries must be mappings")
        if not isinstance(raw_tokens, (list, tuple)) or not all(
            isinstance(item, str) for item in raw_tokens
        ):
            raise ComponentSpecError("ComponentSpec.token_roles must be a string list")
        if not isinstance(raw_metadata, Mapping):
            raise ComponentSpecError("ComponentSpec.metadata must be a mapping")
        return cls(
            schema_version=str(payload.get("schema_version") or ""),
            component_id=str(payload.get("component_id") or ""),
            variant=str(payload.get("variant") or ""),
            source_ref=str(payload.get("source_ref") or ""),
            language=str(payload.get("language") or ""),
            slots=tuple(
                ComponentSlot.from_dict(item)
                for item in raw_slots
            ),
            assets=tuple(
                ComponentAsset.from_dict(item)
                for item in raw_assets
            ),
            token_roles=tuple(raw_tokens),
            metadata=dict(raw_metadata),
        )

    def slot(self, role: str) -> ComponentSlot:
        matches = [slot for slot in self.slots if slot.role == role]
        if len(matches) != 1:
            raise ComponentSpecError(
                f"{self.component_id}: expected exactly one {role!r} slot; "
                f"found {len(matches)}"
            )
        return matches[0]


__all__ = [
    "SCHEMA_VERSION",
    "ComponentAsset",
    "ComponentSlot",
    "ComponentSpec",
    "ComponentSpecError",
]
