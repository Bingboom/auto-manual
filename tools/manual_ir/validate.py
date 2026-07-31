"""Semantic and hash validation for a serialized manual IR."""
from __future__ import annotations

from tools.lang_registry import canonical_language

from .hashing import value_sha256
from .model import ManualIR, SCHEMA_VERSION


_NEUTRAL_PAGE_LANGUAGES = frozenset(("", "cover", "toc"))


def unknown_language_issues(ir: ManualIR) -> list[str]:
    """Return unregistered Manual IR language tokens with their source location."""

    issues: list[str] = []
    manual_language = str(ir.language or "").strip()
    if (
        manual_language not in _NEUTRAL_PAGE_LANGUAGES
        and canonical_language(manual_language) is None
    ):
        issues.append(f"manual language is not registered: {manual_language!r}")

    declared = ir.metadata.get("declared_languages")
    if isinstance(declared, list):
        for index, value in enumerate(declared):
            language = str(value or "").strip()
            if (
                language not in _NEUTRAL_PAGE_LANGUAGES
                and canonical_language(language) is None
            ):
                issues.append(
                    "metadata.declared_languages"
                    f"[{index}] is not registered: {language!r}"
                )

    for page in ir.pages:
        language = str(page.language or "").strip()
        if (
            language not in _NEUTRAL_PAGE_LANGUAGES
            and canonical_language(language) is None
        ):
            issues.append(f"{page.page_id}: language is not registered: {language!r}")
    return issues


def validate_manual_ir(
    ir: ManualIR,
    *,
    require_zero_skipped_raw: bool = False,
    require_known_languages: bool = False,
) -> list[str]:
    issues: list[str] = []
    if ir.schema_version != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION}")
    if not ir.pages:
        issues.append("manual IR has no pages")
    page_ids: set[str] = set()
    block_ids: set[str] = set()
    source_refs: set[str] = set()
    block_hashes: list[str] = []
    for page in ir.pages:
        if page.page_id in page_ids:
            issues.append(f"duplicate page_id: {page.page_id}")
        page_ids.add(page.page_id)
        if require_zero_skipped_raw and page.skipped_raw:
            issues.append(f"{page.page_id}: skipped_raw={page.skipped_raw}")
        for block in page.blocks:
            if block.block_id in block_ids:
                issues.append(f"duplicate block_id: {block.block_id}")
            block_ids.add(block.block_id)
            if block.source_ref in source_refs:
                issues.append(f"duplicate block source_ref: {block.source_ref}")
            source_refs.add(block.source_ref)
            expected = value_sha256({"kind": block.kind, "payload": block.payload})
            if block.content_sha256 != expected:
                issues.append(f"{block.block_id}: content hash mismatch")
            block_hashes.append(block.content_sha256)
    expected_content = value_sha256(
        {"page_ids": [page.page_id for page in ir.pages], "block_hashes": block_hashes}
    )
    if ir.content_sha256 != expected_content:
        issues.append("manual content hash mismatch")
    expected_assets = tuple(
        dict.fromkeys(asset for page in ir.pages for block in page.blocks for asset in block.asset_refs)
    )
    if ir.asset_refs != expected_assets:
        issues.append("manual asset_refs do not match block asset refs")
    if require_known_languages:
        issues.extend(unknown_language_issues(ir))
    return issues
