"""Replay this frozen native source through shared Manual IR and MyST.

The package supplies data and verified artwork; all rendering belongs to the
repository's existing ComponentSpec/Manual IR consumers. No table services.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

from tools.utils.path_utils import PathSegments
from tools.manual_ir import build_manual_ir_from_source, write_manual_ir
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.document import validate_document
from tools.manual_ir.hashing import file_sha256, value_sha256
from tools.manual_ir.model import V2_SCHEMA_VERSION
from tools.manual_ir.source import ManualSource, SourcePage
from tools.component_specs.registry import load_component_registry, registry_sha256
from tools.component_specs.theme import load_manual_theme, theme_sha256
from tools.markdown_bundle import _write_myst_sphinx_scaffold
from tools.web.frozen_ai_web import replay_package
from tools.web.presentation import load_web_manual_contract


def read(root: Path, relative: str):
    return json.loads((root / relative).read_text(encoding="utf-8"))


def validate_approval(root: Path, manifest: dict) -> dict:
    approval = read(root, "approval.json")
    target = manifest["target"]
    if (approval.get("schema_version") != "manual-reviewed-publication-approval/v1"
            or approval.get("authorization") != "MA-277"
            or approval.get("user_instruction") != "封面 不要放进去网页版里面啊"
            or approval.get("candidate_source_commit") != "5e1de68efb780b6a5c529b66e9f6544741c8642c"
            or approval.get("original_source_sha256") != manifest["original_source"]["sha256"]
            or (approval.get("model"), approval.get("region"), approval.get("language"))
            != (target["model"], target["region"], target["languages"][0])):
        raise ValueError("publication approval identity changed")
    if (file_sha256(root / "source/chapters.json") != approval["reviewed_chapters_sha256"]
            or file_sha256(root / "source/presentation.css")
            != approval["reviewed_presentation_css_sha256"]
            or read(root, "source/admission.json")["components"]
            != approval["reviewed_component_requirements"]):
        raise ValueError("approved copy, presentation or component requirements changed")
    if value_sha256(read(root, "source/chapters.json")) != approval["reviewed_non_cover_chapters_sha256"]:
        raise ValueError("non-cover chapter bytes changed")
    return approval


def validate_inputs(root: Path, manifest: dict, pdf: Path | None) -> None:
    for record in manifest["inputs"]:
        path = (root / record["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("source input escapes package")
        if not path.is_file() or file_sha256(path) != record["sha256"]:
            raise ValueError(f"frozen source input changed: {record['path']}")
    validate_approval(root, manifest)
    if pdf is not None:
        import fitz

        if file_sha256(pdf) != manifest["original_source"]["sha256"]:
            raise ValueError("original PDF SHA256 mismatch")
        native = read(root, "source/native-text.json")
        with fitz.open(pdf) as document:
            if len(document) != len(native["pages"]):
                raise ValueError("original PDF page count mismatch")
            for page, frozen in zip(document, native["pages"], strict=True):
                blocks = [{"bbox": list(b[:4]), "text": b[4]}
                          for b in page.get_text("blocks") if b[6] == 0]
                if blocks != frozen["blocks"]:
                    raise ValueError("fresh PDF native text/geometry differs from frozen source")


def admit(chapters: list[dict], required: dict) -> dict:
    if [p["page_id"] for p in chapters] != required["chapters"]:
        raise ValueError("source chapter map changed")
    counts = Counter(spec.component_id for spec in component_specs_in_flow(
        [b for p in chapters for b in p["blocks"]]))
    if dict(counts) != required["components"]:
        raise ValueError("source shared component requirements changed")

    def visit(item):
        if item["kind"] == "component":
            return  # Shared contract owns/validates its image/table carrier.
        if item["kind"] in {"image", "table"}:
            raise ValueError("unbound image/table; a shared ComponentSpec is required")
        for child in item.get("children", []):
            visit(child)
    for chapter in chapters:
        for block in chapter["blocks"]:
            visit(block)
    return {"chapters": required["chapters"], "components": dict(counts),
            "source_sha256": required["source_sha256"], "issues": [],
            "boundary": required["scope"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pdf", type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    output = args.output.resolve()
    if output.exists():
        raise ValueError("output exists; cold replay requires a new directory")
    manifest = read(package, "source_manifest.json")
    validate_inputs(package, manifest, args.pdf)
    # Keep generated-file hashes outside their own IR to avoid a seal cycle.
    manifest = {**manifest, "inputs": [r for r in manifest["inputs"]
                                      if not r["path"].startswith("web/")]}
    chapters = read(package, "source/chapters.json")
    requirements = read(package, "source/admission.json")
    target = requirements["target"]
    if target != {"model": manifest["target"]["model"], "region": manifest["target"]["region"],
                  "language": manifest["target"]["languages"][0]}:
        raise ValueError("source target disagrees with manifest")
    report = admit(chapters, requirements)
    output.mkdir(parents=True)
    assets = {}
    for record in read(package, "asset_provenance.json").values():
        source = package / record["path"]
        if file_sha256(source) != record["sha256"]:
            raise ValueError("artwork provenance hash changed")
        relative = "assets/" + source.name
        (output / "assets").mkdir(exist_ok=True)
        shutil.copy2(source, output / relative)
        assets[relative] = record["sha256"]
    title = manifest["document_title"]
    filename = "manual.md"
    _write_myst_sphinx_scaffold(output / filename, title=title, presentation_profile="web")
    source_style = "source/presentation.css"
    shutil.copy2(package / source_style, output / "_static/source_presentation.css")
    with (output / "conf.py").open("a") as stream:
        stream.write("language = 'ja'\n")
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=target["model"], region=target["region"])
    metadata = {"projection": "whole-document-components/v1",
                "web_source_normalization": "jp-native-print-reflow/v1", "title": title,
                "markdown_filename": filename, "publication_eligible": True,
                "pending_source_review": [], "publication_approval": read(package, "approval.json"),
                "declared_languages": ["ja"], "frozen_source_manifest": manifest,
                "asset_sha256": assets, "component_registry": registry,
                "component_registry_sha256": registry_sha256(registry), "manual_theme": theme,
                "manual_theme_sha256": theme_sha256(theme), "web_contract": contract,
                "composites": [], "page_declarations": {}, "candidate_admission": report,
                "source_stylesheet": {"path": "_static/source_presentation.css",
                                      "sha256": file_sha256(package / source_style)},
                "frozen_stylesheet_sha256": file_sha256(output / "_static/web_manual.css")}
    pages = tuple(SourcePage(page_id=p["page_id"], source_ref=f"ja/{p['page_id']}",
                             source_path=f"source/{p['page_id']}", language="ja",
                             source_sha256=value_sha256(p), blocks=tuple(("flow", b) for b in p["blocks"]))
                  for p in chapters)
    source = ManualSource(**target, source="native-pdf-semantic-source/v1", bundle_root="frozen-source",
                          bundle_sha256=value_sha256(manifest), snapshot_sha256=None,
                          layout_params_sha256=value_sha256(requirements), style_contract_sha256=value_sha256(contract),
                          pages=pages, metadata=metadata, schema_version=V2_SCHEMA_VERSION)
    ir = build_manual_ir_from_source(source)
    validate_document(ir)
    write_manual_ir(ir, output / PathSegments.MANUAL_IR_JSON)
    replay_package(output)
    print(json.dumps({"target": target, "chapters": len(pages), "assets": len(assets),
                      "admission": report, "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
