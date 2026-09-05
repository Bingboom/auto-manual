"""Web consumer of an assembled document: never reads RST or source CSVs."""
from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup, Comment, NavigableString

from tools.manual_ir import ManualIR
from tools.manual_ir.document import validate_document, validate_tree
from tools.manual_ir.hashing import file_sha256
from tools.web_composite_manifest import WebCompositeEntry, WebCompositeManifest
from tools.web_presentation import transform_web_fragment
from tools.document_assets import stage_fragment_assets
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


def render_document_fragments(ir: ManualIR, *, package_root: Path) -> tuple[str, ...]:
    """Replay content + bundled assets; source_path is an identity, not an input."""
    validate_document(ir)
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
        markup = "".join(tree_to_html(block.payload) for block in page.blocks)
        soup = BeautifulSoup(markup, "html.parser")
        for image in soup.find_all("img"):
            src = str(image["src"])
            if src in ir.metadata["asset_sha256"]:
                image["src"] = (root / src).as_uri()
        declaration = ir.metadata["page_declarations"].get(page.page_id)
        fragment = transform_web_fragment(
            str(soup), source_path=Path(page.source_path),
            contract=ir.metadata["web_contract"], composite_manifest=composites,
            model=ir.model, region=ir.region, language=page.language,
            declared_troubleshooting=declaration == "troubleshooting",
            declared_lcd_icons=declaration == "lcd_icons",
        )
        fragments.append(stage_fragment_assets(fragment, Path(page.source_path), root, (paths.docs_dir, paths.root)))
    return tuple(fragments)
