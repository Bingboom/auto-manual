"""Build a deterministic semantic IR from one prepared RST bundle."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.idml_rst_extract import bundle_page_order, extract_page
from tools.idml.page_identity import page_language
from tools.render_contract import contract_sha256, load_render_contract
from tools.utils.path_utils import Paths

from .hashing import file_sha256, ordered_files_sha256, value_sha256
from .model import ManualBlock, ManualIR, ManualPage


_JSON_BLOCK_KINDS = frozenset({"component", "table"})
_ASSET_KEYS = frozenset({"asset", "asset_ref", "figure", "image", "img", "src"})


def _payload(kind: str, raw: str) -> Any:
    if kind not in _JSON_BLOCK_KINDS:
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


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
    return tuple(dict.fromkeys(found))


def _snapshot_sha256(data_root: Path | None) -> str | None:
    if data_root is None:
        return None
    manifest = data_root / "snapshot_manifest.json"
    if manifest.is_file():
        return file_sha256(manifest)
    return None


def build_manual_ir(
    *,
    root: Path,
    bundle_root: Path,
    model: str,
    region: str,
    lang: str,
    source: str,
    data_root: Path | None = None,
    layout_params_csv: Path | None = None,
    style_contract_path: Path | None = None,
) -> ManualIR:
    paths = Paths(root=root)
    layout_params_csv = layout_params_csv or paths.layout_params_csv
    style_contract_path = style_contract_path or paths.manual_style_contract
    ordered_pages = bundle_page_order(bundle_root)
    if not ordered_pages:
        raise ValueError(f"prepared bundle has no included page files: {bundle_root}")

    contract = load_render_contract(style_contract_path)
    base_tags = {
        "latex",
        f"region_{region.lower()}",
        "model_" + model.lower().replace("-", "_"),
    }
    pages: list[ManualPage] = []
    all_assets: list[str] = []
    all_block_hashes: list[str] = []

    for page_index, page in enumerate(ordered_pages, start=1):
        page_lang = page_language(page, lang)
        result = extract_page(page, base_tags | {f"lang_{page_lang}"})
        blocks: list[ManualBlock] = []
        page_id = f"page-{page_index:04d}-{page.stem}"
        for block_index, (kind, raw) in enumerate(result.blocks, start=1):
            payload = _payload(kind, raw)
            block_id = f"{page_id}:block-{block_index:04d}"
            assets = (raw,) if kind == "image" else _asset_refs(payload)
            block_hash = value_sha256({"kind": kind, "payload": payload})
            block = ManualBlock(
                block_id=block_id,
                source_ref=f"page/{page.name}#block-{block_index}",
                kind=kind,
                payload=payload,
                content_sha256=block_hash,
                asset_refs=assets,
            )
            blocks.append(block)
            all_assets.extend(assets)
            all_block_hashes.append(block_hash)
        pages.append(
            ManualPage(
                page_id=page_id,
                source_ref=f"page/{page.name}",
                source_path=page.relative_to(bundle_root).as_posix(),
                language=page_lang,
                source_sha256=file_sha256(page),
                skipped_raw=result.skipped_raw,
                blocks=tuple(blocks),
            )
        )

    bundle_files: list[tuple[str, Path]] = [("index.rst", bundle_root / "index.rst")]
    bundle_files.extend((page.relative_to(bundle_root).as_posix(), page) for page in ordered_pages)
    manifest = bundle_root / "bundle_manifest.json"
    if manifest.is_file():
        bundle_files.append(("bundle_manifest.json", manifest))
    bundle_sha = ordered_files_sha256(bundle_files)
    content_sha = value_sha256(
        {
            "page_ids": [page.page_id for page in pages],
            "block_hashes": all_block_hashes,
        }
    )
    return ManualIR(
        model=model,
        region=region,
        language=lang,
        source=source,
        bundle_root=bundle_root.as_posix(),
        bundle_sha256=bundle_sha,
        snapshot_sha256=_snapshot_sha256(data_root),
        layout_params_sha256=file_sha256(layout_params_csv),
        style_contract_sha256=contract_sha256(contract),
        content_sha256=content_sha,
        pages=tuple(pages),
        asset_refs=tuple(dict.fromkeys(all_assets)),
        metadata={
            "page_count": len(pages),
            "block_count": sum(len(page.blocks) for page in pages),
            "skipped_raw": sum(page.skipped_raw for page in pages),
        },
    )
