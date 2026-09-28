"""Bounded intake of approved frozen AI JSON into the existing Web IR pipeline.

Run with ``python -m tools.frozen_ai_web --source-root ... --output-root ...``.
The historical input is immutable; every output must be a new directory.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from tools.component_specs.registry import load_component_registry, registry_sha256
from tools.component_specs.overview_instance import overview_instance_sha256, resolve_overview_instance
from tools.component_specs.theme import load_manual_theme, theme_sha256
from tools.frozen_ai_document import ordered_pages
from tools.frozen_ai_source import FrozenBook
from tools.manual_ir import V2_SCHEMA_VERSION, build_manual_ir_from_source, read_manual_ir, write_manual_ir
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.document import validate_document
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.source import ManualSource
from tools.markdown_bundle import _rewrite_local_file_uris_to_relative, _write_myst_sphinx_scaffold
from tools.utils.path_utils import PathSegments
from tools.web_document_ir import render_document_fragments
from tools.web_presentation import load_web_manual_contract


def replay_package(package: Path) -> tuple[str, ...]:
    """Replay frozen IR and images; never read extraction files or old HTML."""
    ir = read_manual_ir(package / PathSegments.MANUAL_IR_JSON)
    css = package / "_static" / "web_manual.css"
    if file_sha256(css) != ir.metadata["frozen_stylesheet_sha256"]:
        raise ValueError("frozen Web stylesheet changed")
    fragments = render_document_fragments(ir, package_root=package)
    # Only document headings become MyST for Sphinx navigation. Registered
    # component markup passes through unchanged, including its own headings.
    chunks = []
    for fragment in fragments:
        soup = BeautifulSoup(fragment, "html.parser")
        for item in soup.contents:
            if isinstance(item, Tag) and item.name in {"h1", "h2", "h3", "h4"} and not item.get("class"):
                if item.get("id"):
                    # Sphinx normalizes underscores in explicit MyST labels;
                    # source chapter links must retain their exact IR anchors.
                    chunks.append(f'<span id="{item["id"]}"></span>')
                chunks.append(f"{'#' * int(item.name[1])} {item.get_text(' ', strip=True)}")
            else:
                chunks.append(str(item))
    path = package / ir.metadata["markdown_filename"]
    path.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
    _rewrite_local_file_uris_to_relative(path)
    return fragments


def build_book(source_root: Path, output: Path, language: str):
    if output.exists():
        raise ValueError(f"output already exists; use a new candidate directory: {output}")
    if output.resolve().is_relative_to(source_root.resolve()):
        raise ValueError("output must not be inside the historical source")
    book = FrozenBook(source_root, output, language)
    title, pages = ordered_pages(book)
    return assemble_book(book, title, pages)


def assemble_book(book, title, pages):
    """Assemble either positioned intake through the same frozen Web pipeline."""
    output, language = book.output, book.language
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = getattr(book, "contract", None) or load_web_manual_contract(
        model=book.target["model"], region=book.target["region"],
    )
    filename = f"manual_{book.target['model'].replace('-', '').lower()}_{book.target['region'].lower()}_{language}.md"
    _write_myst_sphinx_scaffold(output / filename, title=title, presentation_profile="web")
    with (output / "conf.py").open("a", encoding="utf-8") as stream:
        stream.write(f"language = {language!r}\n")
    specs = component_specs_in_flow([payload for page in pages for _, payload in page.blocks])
    metadata = {
        "projection": "whole-document-components/v1",
        "web_source_normalization": "preface-auto-resume/v1",
        "title": title, "markdown_filename": filename,
        "declared_languages": [language], "frozen_source_manifest": book.manifest,
        "source_errata": book.errata,
        **({"pdf_intake_provenance": book.provenance} if hasattr(book, "provenance") else {}),
        "asset_sha256": book.hashes, "component_registry": registry,
        "component_registry_sha256": registry_sha256(registry),
        "manual_theme": theme, "manual_theme_sha256": theme_sha256(theme),
        "web_contract": contract, "composites": [], "page_declarations": {},
        "frozen_stylesheet_sha256": file_sha256(output / "_static" / "web_manual.css"),
        "frozen_figure_inventory": [
            {"slug": figure["slug"], "section": figure["section_id"],
             "physical_page": figure["physical_page"], **book.art[figure["slug"]],
             "presentation": figure.get("presentation") or (
                 "lcd-mode-artwork" if figure["slug"] == "lcd_mode_art" else "approved-composite")}
            for figure in book.figures
        ],
        "component_inventory": {identity: sum(spec.component_id == identity for spec in specs)
                                for identity in sorted({spec.component_id for spec in specs})},
    }
    if contract.get("figure_targets") and contract.get("product_overview", {}).get("source_patterns"):
        overview = getattr(book, "overview_instance", None) or resolve_overview_instance(
            model=book.target["model"], region=book.target["region"])
        metadata.update(overview_instance=overview, overview_instance_sha256=overview_instance_sha256(overview))
    source = ManualSource(
        model=book.target["model"], region=book.target["region"], language=language,
        source=getattr(book, "source_kind", "frozen-ai-json"), bundle_root="frozen-source",
        bundle_sha256=value_sha256(book.manifest), snapshot_sha256=None,
        layout_params_sha256=value_sha256({"layout": "web"}),
        style_contract_sha256=value_sha256(contract), pages=pages,
        metadata=metadata, schema_version=V2_SCHEMA_VERSION,
    )
    ir = build_manual_ir_from_source(source)
    validate_document(ir)
    path = output / PathSegments.MANUAL_IR_JSON
    write_manual_ir(ir, path)
    fragments = replay_package(output)
    # Bind coverage evidence to the actual public replay, not an assumed count.
    rendered = BeautifulSoup("".join(fragments), "html.parser")
    expected_references = getattr(book, "expected_reference_count", len(book.figures) - 1)
    if len(rendered.select(".hb-reference-figure")) != expected_references:
        raise ValueError("source figure coverage disagrees with public replay")
    ir = replace(ir, metadata={**ir.metadata, "rendered_source_figure_count": len(book.figures)})
    write_manual_ir(ir, path)
    return ir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.source_root / "source_manifest.json").read_text(encoding="utf-8"))
    target = manifest["target"]
    result = []
    for language in target["languages"]:
        output = args.output_root / target["model"] / target["region"] / language / "md"
        ir = build_book(args.source_root, output, language)
        result.append({"language": language, "pages": len(ir.pages), "output": str(output),
                       "components": ir.metadata["component_inventory"]})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
