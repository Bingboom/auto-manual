"""Stable JSON serialization for the manual IR."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import ManualBlock, ManualIR, ManualPage
from .validate import ManualIRValidationError, _payload_issues


def write_manual_ir(ir: ManualIR, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(ir.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _block(raw: dict[str, Any]) -> ManualBlock:
    return ManualBlock(
        block_id=raw["block_id"],
        source_ref=raw["source_ref"],
        kind=raw["kind"],
        payload=raw["payload"],
        content_sha256=raw["content_sha256"],
        asset_refs=tuple(raw.get("asset_refs", ())),
    )


def _page(raw: dict[str, Any]) -> ManualPage:
    return ManualPage(
        page_id=raw["page_id"],
        source_ref=raw["source_ref"],
        source_path=raw["source_path"],
        language=raw["language"],
        source_sha256=raw["source_sha256"],
        skipped_raw=raw.get("skipped_raw", 0),
        blocks=tuple(_block(block) for block in raw["blocks"]),
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key!r}")
        result[key] = value
    return result


def read_manual_ir(path: Path) -> ManualIR:
    """Read v1 JSON or raise ManualIRValidationError with file/field context.

    Success guarantees the public envelope, identities, content hashes and
    ordered asset union. External-file digest freshness and renderer-specific
    production policies still belong to their consumers.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, ValueError, RecursionError) as exc:
        raise ManualIRValidationError(str(path), [str(exc)]) from exc
    issues = _payload_issues(raw)
    if issues:
        raise ManualIRValidationError(str(path), issues)
    return ManualIR(
        model=raw["model"],
        region=raw["region"],
        language=raw["language"],
        source=raw["source"],
        bundle_root=raw["bundle_root"],
        bundle_sha256=raw["bundle_sha256"],
        snapshot_sha256=raw.get("snapshot_sha256"),
        layout_params_sha256=raw["layout_params_sha256"],
        style_contract_sha256=raw["style_contract_sha256"],
        content_sha256=raw["content_sha256"],
        pages=tuple(_page(page) for page in raw["pages"]),
        asset_refs=tuple(raw.get("asset_refs", ())),
        schema_version=raw["schema_version"],
        metadata=raw.get("metadata", {}),
    )
