"""Data model for the deterministic renderer-neutral manual IR."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


V1_SCHEMA_VERSION = "manual-ir/v1"
V2_SCHEMA_VERSION = "manual-ir/v2"
SUPPORTED_SCHEMA_VERSIONS = frozenset({V1_SCHEMA_VERSION, V2_SCHEMA_VERSION})

# Existing prepared-RST/IDML and scoped component producers stay byte-stable
# until their own migration cuts. New neutral-flow producers opt into v2.
SCHEMA_VERSION = V1_SCHEMA_VERSION
CURRENT_SCHEMA_VERSION = V2_SCHEMA_VERSION


@dataclass(frozen=True)
class ManualBlock:
    block_id: str
    source_ref: str
    kind: str
    payload: Any
    content_sha256: str
    asset_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManualPage:
    page_id: str
    source_ref: str
    source_path: str
    language: str
    source_sha256: str
    skipped_raw: int
    blocks: tuple[ManualBlock, ...]


@dataclass(frozen=True)
class ManualIR:
    model: str
    region: str
    language: str
    source: str
    bundle_root: str
    bundle_sha256: str
    snapshot_sha256: str | None
    layout_params_sha256: str
    style_contract_sha256: str
    content_sha256: str
    pages: tuple[ManualPage, ...]
    asset_refs: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
