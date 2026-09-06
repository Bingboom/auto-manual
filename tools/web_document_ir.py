"""Web consumer of an assembled document: never reads RST or source CSVs."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString

from tools.manual_ir import V1_SCHEMA_VERSION, ManualIR
from tools.manual_ir.document import validate_document, validate_tree
from tools.manual_ir.flow import flow_nodes_to_html
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.hashing import file_sha256
from tools.web_composite_manifest import WebCompositeEntry, WebCompositeManifest
from tools.web_presentation import transform_web_fragment
from tools.document_assets import stage_fragment_assets
from tools.web_embedded_components import render_embedded_web_component
from tools.utils.path_utils import get_paths


def tree_to_html(tree: list[dict]) -> str:
    validate_tree(tree)
    soup = BeautifulSoup("", "html.parser")
    def decode(node):
        if node["type"] == "text":
            return NavigableString(node["text"])
        if node["type"] == "comment":
            return Comment(node["text"])
        tag = soup.new_tag(node["type"], attrs=node["attributes"])
        for child in node["children"]:
            tag.append(decode(child))
        return tag
    for node in tree:
        soup.append(decode(node))
    return str(soup)


def _rebase_packaged_flow(value, *, root: Path, assets: dict[str, str]):
    """Rebind packaged component and ordinary-flow assets before HTML replay."""

    if isinstance(value, dict):
        return {
            key: (
                (root / child).as_uri()
                if key in {"source", "asset_ref"}
                and isinstance(child, str)
                and child in assets
                else _rebase_packaged_flow(child, root=root, assets=assets)
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_rebase_packaged_flow(child, root=root, assets=assets) for child in value]
    if isinstance(value, tuple):
        return tuple(
            _rebase_packaged_flow(child, root=root, assets=assets) for child in value
        )
    return deepcopy(value)


def render_document_fragments(ir: ManualIR, *, package_root: Path) -> tuple[str, ...]:
    """Replay content + bundled assets; source_path is an identity, not an input."""
    validate_document(ir)
    coverage = ir.metadata.get("web_figure_coverage")
    if coverage is not None:
        from tools.web_figure_coverage import (
            enforce_required_web_figure_coverage,
            validate_web_figure_coverage,
        )

        if not isinstance(coverage, dict):
            raise ValueError("Web figure coverage metadata must be an object")
        validate_web_figure_coverage(coverage)
        enforce_required_web_figure_coverage(ir, coverage)
    root = package_root.resolve()
    for relative, expected in ir.metadata["asset_sha256"].items():
        asset = (root / relative).resolve()
        if not asset.is_relative_to(root) or not asset.is_file() or file_sha256(asset) != expected:
            raise ValueError(f"document asset missing or changed: {relative}")
    composites = WebCompositeManifest(tuple(
        WebCompositeEntry.from_payload({**entry, "path": str(root / entry["path"])}, source=root)
        for entry in ir.metadata["composites"]
    ), source=root)
    paths = get_paths()
    fragments = []
    for page in ir.pages:
        embedded_components_complete = (
            ir.metadata.get("projection") == "whole-document-components/v1"
        )
        page_nodes = [block.payload for block in page.blocks]
        if embedded_components_complete:
            page_nodes = [
                _rebase_packaged_flow(
                    node,
                    root=root,
                    assets=ir.metadata["asset_sha256"],
                )
                for node in page_nodes
            ]
        embedded_specs = (
            component_specs_in_flow(tuple(page_nodes))
            if ir.metadata.get("projection") == "whole-document-components/v1"
            else ()
        )
        resolved_component_ids = frozenset(
            spec.component_id for spec in embedded_specs
        )
        if ir.schema_version == V1_SCHEMA_VERSION:
            markup = "".join(tree_to_html(block.payload) for block in page.blocks)
        else:
            markup = flow_nodes_to_html(
                page_nodes,
                component_renderer=lambda node: render_embedded_web_component(
                    node,
                    source_path=Path(page.source_path),
                    model=ir.model,
                    region=ir.region,
                    language=page.language,
                    composite_manifest=composites,
                    contract=ir.metadata["web_contract"],
                ),
            )
        if embedded_components_complete:
            presentation_markup = markup
        else:
            soup = BeautifulSoup(markup, "html.parser")
            for image in soup.find_all("img"):
                src = str(image["src"])
                if src in ir.metadata["asset_sha256"]:
                    image["src"] = (root / src).as_uri()
            presentation_markup = str(soup)
        declaration = ir.metadata["page_declarations"].get(page.page_id)
        fragment = transform_web_fragment(
            presentation_markup, source_path=Path(page.source_path),
            contract=ir.metadata["web_contract"], composite_manifest=composites,
            model=ir.model, region=ir.region, language=page.language,
            declared_troubleshooting=declaration == "troubleshooting",
            declared_lcd_icons=declaration == "lcd_icons",
            resolved_component_ids=resolved_component_ids,
            embedded_components_complete=embedded_components_complete,
        )
        fragments.append(stage_fragment_assets(fragment, Path(page.source_path), root, (paths.docs_dir, paths.root)))
    return tuple(fragments)
