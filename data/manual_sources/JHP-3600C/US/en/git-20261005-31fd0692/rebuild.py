"""Replay this source-local semantic intake through the shared Manual IR APIs.

Run from the repository root with an unused --output directory. This freezes no
online data and enrolls no phase2/print target. Source selections, visual text
recoveries and artwork decisions remain independently reviewable JSON inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO_ROOT))

from audit_source import check_retired_artwork  # noqa: E402

from tools.component_specs.registry import load_component_registry, registry_sha256  # noqa: E402
from tools.component_specs.theme import load_manual_theme, theme_sha256  # noqa: E402
from tools.manual_ir import (  # noqa: E402
    ManualSource, SourcePage, V2_SCHEMA_VERSION,
    build_manual_ir_from_source, write_manual_ir,
)
from tools.manual_ir.components import component_specs_in_flow  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import file_sha256, value_sha256  # noqa: E402
from tools.markdown_bundle import _write_myst_sphinx_scaffold  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.presentation import load_web_manual_contract  # noqa: E402


def check_inventory(base: Path, rows: list[dict]) -> None:
    for row in rows:
        path = (base / row["path"]).resolve()
        if not path.is_relative_to(base):
            raise ValueError("input escapes its pinned root")
        if not path.is_file() or file_sha256(path) != row["sha256"]:
            raise ValueError("input changed: " + row["path"])


def rebuild(output: Path) -> None:
    if output.exists():
        raise ValueError("use an unused output directory")
    source = json.loads((SOURCE_ROOT / "source/content.json").read_text())
    pdfs = list(SOURCE_ROOT.glob("*.pdf"))
    if len(pdfs) != 1 or file_sha256(pdfs[0]) != source["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    manifest_path = SOURCE_ROOT / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    check_inventory(SOURCE_ROOT, manifest["inputs"])
    check_inventory(REPO_ROOT, manifest["repo_inputs"])
    check_retired_artwork(source, json.loads((SOURCE_ROOT / "source/asset_decisions.json").read_text()))
    # Shared variant copies are immutable inputs; obsolete hashes are refused
    # again at fresh sealing, independent of the source-local inventory.
    shutil.copytree(SOURCE_ROOT / "web/en/assets", output / "assets")
    filename = "manual_" + source["model"].replace("-", "").lower()
    filename += "_" + source["region"].lower() + "_" + source["language"] + ".md"
    _write_myst_sphinx_scaffold(
        output / filename, title=source["title"], presentation_profile="web",
    )
    with (output / "conf.py").open("a") as stream:
        stream.write("\nlanguage = " + repr(source["language"]) + "\n")
    # Source-local geometry corrections; shared styles still own components and breakpoints.
    source_css = output / "_static/source_presentation.css"
    shutil.copy2(SOURCE_ROOT / "source/presentation.css", source_css)
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source["model"], region=source["region"])
    pages = tuple(SourcePage(
        page_id=ch["id"], source_ref="native-pdf/" + ch["id"],
        source_path="source/content.json#" + ch["id"], language=source["language"],
        source_sha256=value_sha256(ch),
        blocks=tuple(("flow", flow) for flow in ch["nodes"]),
    ) for ch in source["chapters"])
    specs = component_specs_in_flow([b for page in pages for _, b in page.blocks])
    metadata = {
        "projection": "whole-document-components/v1",
        "web_source_normalization": "preface-auto-resume/v1",
        "title": source["title"], "markdown_filename": filename,
        "declared_languages": [source["language"]],
        "source_authority": {
            "filename": pdfs[0].name, "sha256": source["source_sha256"],
            "physical_pages": [2, *range(4, 35)],
        },
        "asset_sha256": {
            p.relative_to(output).as_posix(): file_sha256(p)
            for p in sorted((output / "assets").iterdir())
        },
        "component_registry": registry,
        "component_registry_sha256": registry_sha256(registry),
        "manual_theme": theme, "manual_theme_sha256": theme_sha256(theme),
        "web_contract": contract, "composites": [], "page_declarations": {},
        "frozen_stylesheet_sha256": file_sha256(output / "_static/web_manual.css"),
        "source_stylesheet": {
            "path": "_static/source_presentation.css",
            "sha256": file_sha256(source_css),
        },
        "component_inventory": {
            identity: sum(s.component_id == identity for s in specs)
            for identity in sorted({s.component_id for s in specs})
        },
    }
    ir = build_manual_ir_from_source(ManualSource(
        model=source["model"], region=source["region"], language=source["language"],
        source="prepared-document", bundle_root="frozen-source",
        bundle_sha256=value_sha256(source), snapshot_sha256=None,
        layout_params_sha256=value_sha256({"layout": "web"}),
        style_contract_sha256=value_sha256(contract), pages=pages,
        metadata=metadata, schema_version=V2_SCHEMA_VERSION,
    ))
    validate_document(ir)
    write_manual_ir(ir, output / PathSegments.MANUAL_IR_JSON)
    replay_package(output)
    print(json.dumps({"output": str(output), "chapters": len(pages),
                      "components": metadata["component_inventory"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    rebuild(parser.parse_args().output.resolve())
