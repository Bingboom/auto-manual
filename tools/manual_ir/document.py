"""Whole-document validation at the prepared-content boundary.

Version 1 preserves the legacy HTML-shaped tree for historical replay. Version
2 uses renderer-neutral flow nodes and keeps optional HTML attributes only as
presentation hints during the migration.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from tools.manual_ir import (
    V1_SCHEMA_VERSION,
    V2_SCHEMA_VERSION,
    ManualIR,
    ManualIRValidationError,
    validate_manual_ir,
)
from tools.manual_ir.flow import validate_flow_node

# This vocabulary is deliberately finite. Unknown content must not vanish.
CONTENT_TAGS = frozenset("section div span p h1 h2 h3 h4 h5 h6 table thead tbody tfoot tr td th colgroup col img figure figcaption a ul ol li dl dt dd strong em b i sup sub br hr blockquote pre code small abbr aside header footer caption".split())


def content_tree(markup: str) -> list[dict]:
    def encode(node):
        if isinstance(node, Comment):
            return {"type": "comment", "text": str(node)}
        if isinstance(node, NavigableString):
            return {"type": "text", "text": str(node)}
        if not isinstance(node, Tag) or node.name not in CONTENT_TAGS:
            raise ValueError(f"unsupported document content: {getattr(node, 'name', type(node))}")
        return {"type": node.name, "attributes": dict(node.attrs),
                "children": [encode(child) for child in node.children]}
    return [encode(node) for node in BeautifulSoup(markup, "html.parser").contents]


def validate_tree(tree: object) -> None:
    if not isinstance(tree, list):
        raise ValueError("document content must be an ordered node list")
    for node in tree:
        if not isinstance(node, dict):
            raise ValueError("document node must be an object")
        kind = node.get("type")
        if kind in ("text", "comment"):
            if set(node) != {"type", "text"} or not isinstance(node["text"], str):
                raise ValueError("invalid document text node")
            continue
        if kind not in CONTENT_TAGS or set(node) != {"type", "attributes", "children"}:
            raise ValueError(f"unsupported document node: {kind}")
        attrs = node["attributes"]
        if not isinstance(attrs, dict) or any(
            not isinstance(key, str) or not (
                isinstance(value, str) or isinstance(value, list)
                and all(isinstance(item, str) for item in value)
            ) for key, value in attrs.items()
        ):
            raise ValueError("invalid document attributes")
        if kind == "img" and not str(attrs.get("src", "")).strip():
            raise ValueError("document image requires src")
        validate_tree(node["children"])


def validate_document(ir: ManualIR) -> None:
    issues = validate_manual_ir(ir, require_zero_skipped_raw=True, require_known_languages=True)
    if issues:
        raise ManualIRValidationError(ir.source, issues)
    projection = ir.metadata.get("projection")
    expected_projection = {
        V1_SCHEMA_VERSION: "whole-document-content/v1",
        V2_SCHEMA_VERSION: "whole-document-flow/v1",
    }.get(ir.schema_version)
    if projection != expected_projection:
        raise ValueError(f"expected {expected_projection}")
    assets = ir.metadata.get("asset_sha256")
    if not isinstance(assets, dict) or any(
        not isinstance(path, str) or not path.startswith("assets/")
        or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
        for path, digest in assets.items()
    ):
        raise ValueError("invalid document asset manifest")
    if set(ir.asset_refs) - set(assets):
        raise ValueError("document image is missing from the asset manifest")
    if not isinstance(ir.metadata.get("web_contract"), dict) or not isinstance(ir.metadata.get("composites"), list):
        raise ValueError("document presentation bindings are missing")
    figure_coverage = ir.metadata.get("web_figure_coverage")
    if figure_coverage is not None:
        from tools.web_figure_coverage import validate_web_figure_coverage

        if not isinstance(figure_coverage, dict):
            raise ValueError("invalid Web figure coverage")
        validate_web_figure_coverage(figure_coverage)
        if (
            figure_coverage.get("model") != ir.model
            or figure_coverage.get("region") != ir.region
        ):
            raise ValueError("Web figure coverage target does not match document")
    declarations = ir.metadata.get("page_declarations")
    if not isinstance(declarations, dict) or set(declarations) - {p.page_id for p in ir.pages}:
        raise ValueError("invalid document page declarations")
    page_slots = ir.metadata.get("page_slots", {})
    if (
        not isinstance(page_slots, dict)
        or set(page_slots) - {p.page_id for p in ir.pages}
        or any(
            not isinstance(page_id, str)
            or not isinstance(slot, str)
            or not slot.strip()
            for page_id, slot in page_slots.items()
        )
    ):
        raise ValueError("invalid document page slots")
    for page in ir.pages:
        if not page.blocks:
            raise ValueError(f"{page.page_id}: empty document page")
        for block_index, block in enumerate(page.blocks):
            location = (
                f"{page.page_id}.blocks[{block_index}] ({block.block_id})"
            )
            if ir.schema_version == V1_SCHEMA_VERSION:
                if block.kind != "document_content":
                    raise ValueError(f"{location}: unexpected block {block.kind}")
                validate_tree(block.payload)
            else:
                if block.kind != "flow":
                    raise ValueError(f"{location}: unexpected block {block.kind}")
                flow_issues = validate_flow_node(block.payload)
                if flow_issues:
                    raise ValueError(
                        f"{location}: invalid flow block: "
                        + "; ".join(flow_issues)
                    )
