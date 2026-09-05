"""Semantic and hash validation for a serialized manual IR."""
from __future__ import annotations

import json
import re
from typing import Any

from tools.lang_registry import canonical_language

from .hashing import value_sha256
from .model import ManualIR, SCHEMA_VERSION


_NEUTRAL_PAGE_LANGUAGES = frozenset(("", "cover", "toc"))


class ManualIRValidationError(ValueError):
    """A file did not satisfy the public Manual IR contract."""

    def __init__(self, source: str, issues: list[str]) -> None:
        self.source = source
        self.issues = tuple(issues)
        super().__init__(f"invalid Manual IR {source}: " + "; ".join(issues))


def _structure_issues(raw: Any) -> list[str]:
    """Check the v1 envelope before decoding or traversing semantic fields.

    Optional fields may be absent, but explicit null/wrong types must not turn
    into empty collections or strings. Payload kinds remain extensible; their
    renderer-specific schemas belong to their owners, not this envelope.
    """
    issues: list[str] = []

    def text(value: Any, location: str, *, empty: bool = False) -> None:
        if not isinstance(value, str) or (not empty and not value.strip()):
            issues.append(f"{location}: expected {'a' if empty else 'a non-empty'} string")
        elif isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeError:
                issues.append(f"{location}: expected valid UTF-8 text")

    def digest(value: Any, location: str) -> None:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            issues.append(f"{location}: expected a lowercase SHA-256 digest (64 hex characters)")

    def sequence(value: Any, location: str) -> bool:
        # Dataclass asdict retains tuples; serialized JSON uses arrays.
        if not isinstance(value, (list, tuple)):
            issues.append(f"{location}: expected an array")
            return False
        return True

    def strings(value: Any, location: str, *, empty: bool = False) -> None:
        if sequence(value, location):
            for index, item in enumerate(value):
                text(item, f"{location}[{index}]", empty=empty)

    def count(value: Any, location: str) -> None:
        if type(value) is not int or value < 0:
            issues.append(f"{location}: expected a non-negative integer")

    def json_value(value: Any, location: str) -> None:
        try:
            json.dumps(value, allow_nan=False, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
            issues.append(f"{location}: invalid JSON value: {exc}")

    if not isinstance(raw, dict):
        return ["$: expected a JSON object"]
    for field in ("schema_version", "model", "region", "source", "bundle_root"):
        text(raw.get(field), field)
    text(raw.get("language"), "language", empty=True)
    for field in ("bundle_sha256", "layout_params_sha256", "style_contract_sha256", "content_sha256"):
        digest(raw.get(field), field)
    if raw.get("snapshot_sha256") is not None:
        digest(raw["snapshot_sha256"], "snapshot_sha256")
    strings(raw.get("asset_refs", ()), "asset_refs")
    metadata = raw.get("metadata", {})
    if not isinstance(metadata, dict):
        issues.append("metadata: expected an object")
    else:
        json_value(metadata, "metadata")
        if "declared_languages" in metadata:
            strings(metadata["declared_languages"], "metadata.declared_languages", empty=True)
        for field in ("page_count", "block_count", "skipped_raw"):
            if field in metadata:
                count(metadata[field], f"metadata.{field}")
    pages = raw.get("pages")
    if not sequence(pages, "pages"):
        return issues
    for index, page in enumerate(pages):
        loc = f"pages[{index}]"
        if not isinstance(page, dict):
            issues.append(f"{loc}: expected an object")
            continue
        for field in ("page_id", "source_ref", "source_path"):
            text(page.get(field), f"{loc}.{field}")
        text(page.get("language"), f"{loc}.language", empty=True)
        digest(page.get("source_sha256"), f"{loc}.source_sha256")
        count(page.get("skipped_raw", 0), f"{loc}.skipped_raw")
        blocks = page.get("blocks")
        if not sequence(blocks, f"{loc}.blocks"):
            continue
        for block_index, block in enumerate(blocks):
            block_loc = f"{loc}.blocks[{block_index}]"
            if not isinstance(block, dict):
                issues.append(f"{block_loc}: expected an object")
                continue
            for field in ("block_id", "source_ref", "kind"):
                text(block.get(field), f"{block_loc}.{field}")
            digest(block.get("content_sha256"), f"{block_loc}.content_sha256")
            strings(block.get("asset_refs", ()), f"{block_loc}.asset_refs")
            if "payload" not in block:
                issues.append(f"{block_loc}.payload: required field is missing")
            else:
                json_value(block["payload"], f"{block_loc}.payload")
    return issues


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
    """Validate the same envelope and semantics required by read_manual_ir.

    Language registration and zero skipped raw blocks are opt-in production
    policies, independent of whether a v1 document is safe to read.
    """
    issues = _payload_issues(ir.to_dict(), require_zero_skipped_raw=require_zero_skipped_raw)
    if require_known_languages and not _structure_issues(ir.to_dict()):
        issues.extend(unknown_language_issues(ir))
    return issues


def _payload_issues(raw: Any, *, require_zero_skipped_raw: bool = False) -> list[str]:
    issues = _structure_issues(raw)
    if issues:
        return issues
    # All shapes/types below have been checked; no coercion or repair occurs.
    pages = raw["pages"]
    if raw["schema_version"] != SCHEMA_VERSION:
        issues.append(f"schema_version must be {SCHEMA_VERSION}; got {raw['schema_version']!r}")
    if not pages:
        issues.append("manual IR has no pages")
    page_ids: set[str] = set()
    page_refs: set[str] = set()
    block_ids: set[str] = set()
    source_refs: set[str] = set()
    block_hashes: list[str] = []
    for index, page in enumerate(pages):
        loc = f"pages[{index}] ({page['page_id']})"
        if page["page_id"] in page_ids:
            issues.append(f"{loc}: duplicate page_id: {page['page_id']}")
        page_ids.add(page["page_id"])
        if page["source_ref"] in page_refs:
            issues.append(f"{loc}: duplicate page source_ref: {page['source_ref']}")
        page_refs.add(page["source_ref"])
        if require_zero_skipped_raw and page.get("skipped_raw", 0):
            issues.append(f"{loc}: skipped_raw={page['skipped_raw']}")
        for block_index, block in enumerate(page["blocks"]):
            block_loc = f"{loc}.blocks[{block_index}] ({block['block_id']})"
            prefix = page["source_ref"] + "#"
            if not block["source_ref"].startswith(prefix) or not block["source_ref"][len(prefix):].strip():
                issues.append(
                    f"{block_loc}.source_ref: expected {page['source_ref']!r} "
                    f"with a non-empty block fragment; got {block['source_ref']!r}"
                )
            if block["block_id"] in block_ids:
                issues.append(f"{block_loc}: duplicate block_id: {block['block_id']}")
            block_ids.add(block["block_id"])
            if block["source_ref"] in source_refs:
                issues.append(f"{block_loc}: duplicate block source_ref: {block['source_ref']}")
            source_refs.add(block["source_ref"])
            expected = value_sha256({"kind": block["kind"], "payload": block["payload"]})
            if block["content_sha256"] != expected:
                issues.append(f"{block_loc}: content hash mismatch")
            block_hashes.append(block["content_sha256"])
    expected_content = value_sha256(
        {"page_ids": [page["page_id"] for page in pages], "block_hashes": block_hashes}
    )
    if raw["content_sha256"] != expected_content:
        issues.append("manual content hash mismatch")
    expected_assets = tuple(
        dict.fromkeys(
            asset for page in pages for block in page["blocks"]
            for asset in block.get("asset_refs", ())
        )
    )
    if tuple(raw.get("asset_refs", ())) != expected_assets:
        issues.append("manual asset_refs do not match block asset refs")
    return issues
