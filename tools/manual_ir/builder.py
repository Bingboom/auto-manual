"""Build a deterministic semantic IR from one prepared RST bundle."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from tools.idml_rst_extract import bundle_page_order, extract_page
from tools.idml.page_identity import page_language
from tools.render_contract import (
    LAYOUT_PARAMS_HASH_ALGORITHM,
    contract_sha256,
    layout_tokens_sha256,
    load_layout_tokens,
    load_render_contract,
)
from tools.utils.path_utils import Paths

from .hashing import file_sha256, ordered_files_sha256, value_sha256
from .model import ManualBlock, ManualIR, ManualPage


_JSON_BLOCK_KINDS = frozenset({"component", "data", "table"})
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


# Matches `<semantic_name>_<feishu-file-token>.<ext>` wherever the basename
# appears — full `_attachments/...` paths in CSV cells and RST directives, and
# bare basenames inside rendered LaTeX macro arguments alike. The token is a
# single 16+ char alphanumeric run; the all-lowercase lookahead keeps long
# English name words (e.g. `internationalization`) out of the match.
_ATTACHMENT_TOKEN_RE = re.compile(
    r"([A-Za-z0-9_][A-Za-z0-9_.\-]*?)"
    r"_(?![a-z]{16,}\.)[A-Za-z0-9]{16,}"
    r"(\.(?:png|jpe?g|pdf|svg))"
)


def _token_normalized_sha256(text: str) -> str:
    return hashlib.sha256(
        _ATTACHMENT_TOKEN_RE.sub(r"\1\2", text).encode("utf-8")
    ).hexdigest()


def _normalized_table_sha256(path: Path) -> str:
    """Digest of one synced table with volatile attachment tokens stripped.

    Synced CSVs embed attachment file paths whose basenames end in a Feishu
    file token, and tokens rotate on EVERY export — so the raw bytes of e.g.
    ``symbols_blocks.csv`` differ between two syncs of identical data. Strip
    the token (keep the semantic name and extension) before hashing so the
    identity tracks content, not export runs.
    """
    return _token_normalized_sha256(path.read_text(encoding="utf-8", errors="replace"))


def _normalized_page_sha256(path: Path) -> str:
    """Digest of one bundle page with volatile attachment tokens stripped.

    Finalized bundle pages embed staged attachment paths whose basenames end
    in a Feishu file token, and tokens rotate on EVERY export — the same
    volatility the snapshot identity already normalizes away. The per-page
    ``source_sha256`` feeds the reference-layout contract pins, so hash the
    token-normalized text: identical page content pins identically across
    export runs, while any real content change still changes the digest.
    """
    return _token_normalized_sha256(path.read_text(encoding="utf-8", errors="replace"))


def _snapshot_sha256(data_root: Path | None) -> str | None:
    """Content identity of the phase2 snapshot, stable across re-syncs.

    Two volatility sources used to make this pin structurally un-matchable on
    CI (part of why the 1.6 publish had to bypass the same-source gate):
    hashing the manifest FILE picked up ``generated_at``/tool metadata, and
    the per-table digests picked up rotated attachment tokens embedded in the
    CSVs. Hash the canonical set of token-normalized per-table digests
    instead: identical data ⇒ identical identity, whenever and wherever the
    sync ran; a real value change still changes the identity. Falls back to
    the manifest file hash for legacy manifests without a tables list.
    """
    if data_root is None:
        return None
    manifest = data_root / "snapshot_manifest.json"
    if not manifest.is_file():
        return None
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return file_sha256(manifest)
    tables = payload.get("tables")
    if not isinstance(tables, list) or not tables:
        return file_sha256(manifest)
    canonical: list[tuple[str, str, str]] = []
    for entry in tables:
        if not isinstance(entry, dict):
            continue
        logical_name = str(entry.get("logical_name"))
        file_name = str(entry.get("file_name"))
        table_path = data_root / file_name
        if table_path.is_file():
            digest = _normalized_table_sha256(table_path)
        else:
            digest = str(entry.get("sha256"))
        canonical.append((logical_name, file_name, digest))
    return value_sha256(sorted(canonical))


def _declared_languages(root: Path, bundle_root: Path) -> list[str]:
    """Snapshot the prepared bundle's manifest-declared language contract.

    Small direct-export fixtures intentionally have no bundle manifest.  A
    production bundle does, and its source page manifest is the authority for
    the complete language set even if a generated include is accidentally
    missing.  Keeping this declaration in the IR lets approved-layout
    activation distinguish an incomplete production target from an ordinary
    single-language fixture without consulting mutable source files later.
    """
    bundle_manifest = bundle_root / "bundle_manifest.json"
    if not bundle_manifest.is_file():
        return []
    try:
        bundle_payload = json.loads(bundle_manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    manifest_ref = bundle_payload.get("page_manifest")
    if not isinstance(manifest_ref, str) or not manifest_ref.strip():
        return []
    manifest_path = (root / manifest_ref).resolve()
    try:
        manifest_path.relative_to(root.resolve())
        manifest_payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError):
        return []
    pages = manifest_payload.get("pages") if isinstance(manifest_payload, dict) else None
    if not isinstance(pages, list):
        return []
    languages: list[str] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        raw_values = page.get("langs", page.get("lang"))
        if raw_values is None:
            continue
        values = raw_values if isinstance(raw_values, list) else [raw_values]
        for value in values:
            language = str(value).strip().lower()
            if language and "{" not in language and language not in languages:
                languages.append(language)
    return languages


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
                source_sha256=_normalized_page_sha256(page),
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
        layout_params_sha256=layout_tokens_sha256(load_layout_tokens(layout_params_csv)),
        style_contract_sha256=contract_sha256(contract),
        content_sha256=content_sha,
        pages=tuple(pages),
        asset_refs=tuple(dict.fromkeys(all_assets)),
        metadata={
            "page_count": len(pages),
            "block_count": sum(len(page.blocks) for page in pages),
            "skipped_raw": sum(page.skipped_raw for page in pages),
            "declared_languages": _declared_languages(root, bundle_root),
            "layout_params_hash_algorithm": LAYOUT_PARAMS_HASH_ALGORITHM,
        },
    )
