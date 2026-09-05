"""In-memory source input for Manual IR assembly, independent of renderers.

Adapters supply decoded existing payloads and provenance. These are unversioned
construction inputs, not a second serialized IR or a component/page-plan model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourcePage:
    """One ordered source page before block identities/hashes are assembled.

    Page identities, source paths and languages are opaque to the assembler.
    Blocks use existing (kind, payload) pairs; JSON envelopes are decoded by
    the adapter, while plain text (including JSON-looking prose) stays text.
    """

    page_id: str
    source_ref: str
    source_path: str
    language: str
    source_sha256: str
    blocks: tuple[tuple[str, Any], ...]
    skipped_raw: int = 0


@dataclass(frozen=True)
class ManualSource:
    """Source pages plus the provenance already required by manual-ir/v1.

    External digests belong to the source adapter; content digests, block IDs,
    asset ordering and page/block/skipped counts belong to the IR assembler.
    No filesystem access, parser, language policy or rendering is implied.
    """

    model: str
    region: str
    language: str
    source: str
    bundle_root: str
    bundle_sha256: str
    snapshot_sha256: str | None
    layout_params_sha256: str
    style_contract_sha256: str
    pages: tuple[SourcePage, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
