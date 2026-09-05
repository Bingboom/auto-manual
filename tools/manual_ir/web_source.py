"""Shared provenance envelope for explicitly scoped prepared-HTML projections."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tools.manual_ir.hashing import value_sha256
from tools.manual_ir.source import ManualSource, SourcePage


def make_web_source(
    html_fragment: str,
    *,
    source_path: Path,
    blocks: tuple[tuple[str, Any], ...],
    projection: str,
    style_contract_sha256: str,
    language: str | None = None,
    model: str | None = None,
    region: str | None = None,
) -> ManualSource:
    """Record actual fragment/style identity; snapshot and layout are unavailable."""
    digest = hashlib.sha256(html_fragment.encode("utf-8")).hexdigest()
    return ManualSource(
        model=model or "unspecified",
        region=region or "unspecified",
        language=language or "und",
        source="prepared-html",
        bundle_root=str(source_path.parent),
        bundle_sha256=digest,
        snapshot_sha256=None,
        layout_params_sha256=value_sha256({"layout_params": "not-used"}),
        style_contract_sha256=style_contract_sha256,
        pages=(
            SourcePage(
                page_id=str(source_path),
                source_ref=str(source_path),
                source_path=str(source_path),
                language=language or "und",
                source_sha256=digest,
                blocks=tuple(blocks),
            ),
        ),
        metadata={
            "projection": projection,
            "source_format": "prepared-html",
            "layout_params": "not-used",
        },
    )
