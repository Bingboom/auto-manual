"""Assemble deterministic Manual IR from public source-page inputs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.rst_inline import IMAGE

from .hashing import value_sha256
from .model import ManualBlock, ManualIR, ManualPage
from .source import ManualSource


_ASSET_KEYS = frozenset({"asset", "asset_ref", "figure", "image", "img", "src"})


def _asset_refs(value: Any, *, parent_key: str = "") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in _ASSET_KEYS and isinstance(child, str) and child.strip():
                found.append(child.strip())
            else:
                found.extend(_asset_refs(child, parent_key=key))
    elif isinstance(value, list):
        for child in value:
            found.extend(_asset_refs(child, parent_key=parent_key))
    elif parent_key.lower() in _ASSET_KEYS and isinstance(value, str) and value.strip():
        found.append(value.strip())
    elif isinstance(value, str):
        found.extend(match.group(2) for match in IMAGE.finditer(value))
    return tuple(dict.fromkeys(found))


def build_manual_ir_from_source(source: ManualSource) -> ManualIR:
    """Assemble existing v1 pages/blocks without consulting a source renderer.

    Payloads are already decoded; source identifiers/languages/digests remain
    exactly as supplied. Validation remains the shared validate_manual_ir
    boundary, with strict language/raw policies selected by each consumer.
    """
    if not source.pages:
        raise ValueError("manual source has no pages")
    pages: list[ManualPage] = []
    all_assets: list[str] = []
    all_block_hashes: list[str] = []
    for page in source.pages:
        blocks: list[ManualBlock] = []
        for block_index, (kind, payload) in enumerate(page.blocks, start=1):
            block_id = f"{page.page_id}:block-{block_index:04d}"
            assets = (payload,) if kind == "image" else _asset_refs(payload)
            block_hash = value_sha256({"kind": kind, "payload": payload})
            blocks.append(ManualBlock(
                block_id=block_id,
                source_ref=f"{page.source_ref}#block-{block_index}",
                kind=kind,
                payload=payload,
                content_sha256=block_hash,
                asset_refs=assets,
            ))
            all_assets.extend(assets)
            all_block_hashes.append(block_hash)
        pages.append(ManualPage(
            page_id=page.page_id,
            source_ref=page.source_ref,
            source_path=page.source_path,
            language=page.language,
            source_sha256=page.source_sha256,
            skipped_raw=page.skipped_raw,
            blocks=tuple(blocks),
        ))
    return ManualIR(
        model=source.model,
        region=source.region,
        language=source.language,
        source=source.source,
        bundle_root=source.bundle_root,
        bundle_sha256=source.bundle_sha256,
        snapshot_sha256=source.snapshot_sha256,
        layout_params_sha256=source.layout_params_sha256,
        style_contract_sha256=source.style_contract_sha256,
        content_sha256=value_sha256({
            "page_ids": [page.page_id for page in pages],
            "block_hashes": all_block_hashes,
        }),
        pages=tuple(pages),
        asset_refs=tuple(dict.fromkeys(all_assets)),
        metadata={
            **source.metadata,
            "page_count": len(pages),
            "block_count": sum(len(page.blocks) for page in pages),
            "skipped_raw": sum(page.skipped_raw for page in pages),
        },
    )


def build_manual_ir(
    *,
    root: Path,
    bundle_root: Path,
    model: str,
    region: str,
    lang: str,
    source: str,
    category: str | None = None,
    data_root: Path | None = None,
    layout_params_csv: Path | None = None,
    layout_param_overlays: tuple[Path, ...] = (),
    style_contract_path: Path | None = None,
) -> ManualIR:
    """Compatibility entry for prepared RST callers (including production IDML).

    New source producers call build_manual_ir_from_source directly. Import the
    legacy adapter only when this RST-specific entry is invoked, so importing
    and using the public source assembler never loads an IDML implementation.
    """
    from .prepared_rst import load_prepared_rst_source

    prepared = load_prepared_rst_source(
        root=root, bundle_root=bundle_root, model=model, region=region,
        lang=lang, source=source, category=category, data_root=data_root,
        layout_params_csv=layout_params_csv,
        layout_param_overlays=layout_param_overlays,
        style_contract_path=style_contract_path,
    )
    return build_manual_ir_from_source(prepared)
