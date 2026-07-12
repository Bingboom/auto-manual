"""Stable JSON serialization for the manual IR."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import ManualBlock, ManualIR, ManualPage


def write_manual_ir(ir: ManualIR, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(ir.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _block(raw: dict[str, Any]) -> ManualBlock:
    return ManualBlock(
        block_id=str(raw["block_id"]),
        source_ref=str(raw["source_ref"]),
        kind=str(raw["kind"]),
        payload=raw.get("payload"),
        content_sha256=str(raw["content_sha256"]),
        asset_refs=tuple(str(value) for value in raw.get("asset_refs") or []),
    )


def _page(raw: dict[str, Any]) -> ManualPage:
    return ManualPage(
        page_id=str(raw["page_id"]),
        source_ref=str(raw["source_ref"]),
        source_path=str(raw["source_path"]),
        language=str(raw["language"]),
        source_sha256=str(raw["source_sha256"]),
        skipped_raw=int(raw.get("skipped_raw") or 0),
        blocks=tuple(_block(block) for block in raw.get("blocks") or []),
    )


def read_manual_ir(path: Path) -> ManualIR:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ManualIR(
        model=str(raw["model"]),
        region=str(raw["region"]),
        language=str(raw["language"]),
        source=str(raw["source"]),
        bundle_root=str(raw["bundle_root"]),
        bundle_sha256=str(raw["bundle_sha256"]),
        snapshot_sha256=raw.get("snapshot_sha256"),
        layout_params_sha256=str(raw["layout_params_sha256"]),
        style_contract_sha256=str(raw["style_contract_sha256"]),
        content_sha256=str(raw["content_sha256"]),
        pages=tuple(_page(page) for page in raw.get("pages") or []),
        asset_refs=tuple(str(value) for value in raw.get("asset_refs") or []),
        schema_version=str(raw["schema_version"]),
        metadata=dict(raw.get("metadata") or {}),
    )
