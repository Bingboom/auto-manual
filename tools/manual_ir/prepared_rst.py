"""Legacy prepared-RST projection into the public ManualSource boundary.

This adapter deliberately retains IDML/LaTeX extraction, only-tag policy,
page-language suffixes, bundle discovery and provenance hashing. It is not a
renderer-neutral RST parser. Flow Markdown has a different projection policy
and must not reuse these tags accidentally.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, overload

import yaml

from tools.build_docs_theme import normalize_sphinx_tag_value
from tools.idml_rst_extract import bundle_page_order, extract_page
from tools.idml.page_identity import page_language
from tools.render_contract import (
    LAYOUT_PARAMS_HASH_ALGORITHM,
    contract_sha256,
    layout_tokens_sha256,
    load_layout_token_layers,
    load_render_contract,
)
from tools.utils.path_utils import Paths

from .hashing import _normalized_page_sha256, _snapshot_sha256, ordered_files_sha256
from .source import ManualSource, SourcePage


_JSON_BLOCK_KINDS = frozenset({"component", "data", "table"})


def _payload(kind: str, raw: str) -> Any:
    if kind not in _JSON_BLOCK_KINDS:
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


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


@overload
def load_prepared_rst_source(
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
    missing_ok: Literal[False] = False,
) -> ManualSource: ...


@overload
def load_prepared_rst_source(
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
    missing_ok: Literal[True],
) -> ManualSource | None: ...


def load_prepared_rst_source(
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
    missing_ok: bool = False,
) -> ManualSource | None:
    paths = Paths(root=root)
    layout_params_csv = layout_params_csv or paths.layout_params_csv
    style_contract_path = style_contract_path or paths.manual_style_contract
    ordered_pages = bundle_page_order(bundle_root)
    if not ordered_pages:
        if missing_ok:
            return None
        raise ValueError(f"prepared bundle has no included page files: {bundle_root}")

    contract = load_render_contract(style_contract_path)
    base_tags = {
        "latex",
        # IDML consumes the LaTeX-capable source projection, but some pages
        # also provide an editable semantic branch that must replace opaque
        # raw-LaTeX artwork.  The dedicated tag lets those pages express
        # ``latex and not idml`` / ``not latex or idml`` without changing the
        # ordinary Sphinx builders.
        "idml",
        f"region_{region.lower()}",
        "model_" + model.lower().replace("-", "_"),
    }
    # The product line, spelled exactly as the Sphinx plane spells it -- the
    # same normalizer, so ``.. only:: category_bp`` cannot mean one thing to
    # the PDF line and another to IDML.
    normalized_category = normalize_sphinx_tag_value(category)
    if normalized_category:
        base_tags.add(f"category_{normalized_category}")
    pages: list[SourcePage] = []
    for page_index, page in enumerate(ordered_pages, start=1):
        page_lang = page_language(page, lang)
        result = extract_page(page, base_tags | {f"lang_{page_lang}"})
        pages.append(SourcePage(
            page_id=f"page-{page_index:04d}-{page.stem}",
            source_ref=f"page/{page.name}",
            source_path=page.relative_to(bundle_root).as_posix(),
            language=page_lang,
            source_sha256=_normalized_page_sha256(page),
            skipped_raw=result.skipped_raw,
            blocks=tuple((kind, _payload(kind, raw)) for kind, raw in result.blocks),
        ))

    bundle_files: list[tuple[str, Path]] = [("index.rst", bundle_root / "index.rst")]
    bundle_files.extend((page.relative_to(bundle_root).as_posix(), page) for page in ordered_pages)
    manifest = bundle_root / "bundle_manifest.json"
    if manifest.is_file():
        bundle_files.append(("bundle_manifest.json", manifest))
    bundle_sha = ordered_files_sha256(bundle_files)
    return ManualSource(
        model=model,
        region=region,
        language=lang,
        source=source,
        bundle_root=bundle_root.as_posix(),
        bundle_sha256=bundle_sha,
        snapshot_sha256=_snapshot_sha256(data_root),
        layout_params_sha256=layout_tokens_sha256(
            load_layout_token_layers(layout_params_csv, layout_param_overlays)
        ),
        style_contract_sha256=contract_sha256(contract),
        pages=tuple(pages),
        metadata={
            "declared_languages": _declared_languages(root, bundle_root),
            "layout_params_hash_algorithm": LAYOUT_PARAMS_HASH_ALGORITHM,
        },
    )
