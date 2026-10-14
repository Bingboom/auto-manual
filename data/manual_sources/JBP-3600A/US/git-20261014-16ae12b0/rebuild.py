"""Replay the JBP-3600A US English, French or Spanish source through the shared Manual IR APIs.

Run from the repository root with an unused --output directory. The archived
PDF is checked before anything is written. This freezes
no online data and enrolls no phase2/print target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / "build.py").is_file())
ASSET_REFERENCE = re.compile(r"assets/([A-Za-z0-9_.\-]+)")
sys.path.insert(0, str(REPO_ROOT))


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


def archived_pdf_sha256(original: dict) -> str:
    return hashlib.sha256((SOURCE_ROOT / original["filename"]).read_bytes()).hexdigest()


def rebuild(output: Path, language: str = "en") -> None:
    if output.exists():
        raise ValueError("use an unused output directory")
    content = SOURCE_ROOT / "source" / language / "content.json"
    source = json.loads(content.read_text())
    manifest_path = SOURCE_ROOT / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    original = manifest["original_source"]
    if archived_pdf_sha256(original) != original["sha256"] or original["sha256"] != source["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    check_inventory(SOURCE_ROOT, manifest["inputs"])
    check_inventory(REPO_ROOT, manifest["repo_inputs"])
    # A candidate is publishable only after the operator accepts these exact
    # source inputs (source/approval.json); frozen web/ outputs are not part of that review.
    approved = manifest.get("publication_status") == "operator-approved-git-only-release"
    approval = None
    if approved:
        acceptance = SOURCE_ROOT / "source/approval.json"
        approval = json.loads(acceptance.read_text()) if acceptance.is_file() else {}
        reviewed = [row for row in manifest["inputs"]
                    if not row["path"].startswith("web/") and row["path"] != "source/approval.json"]
        if (approval.get("target") != {key: manifest["target"][key] for key in ("model", "region", "technical_version")}
                or approval.get("original_source_sha256") != original["sha256"]
                or approval.get("reviewed_inputs") != reviewed
                or not approval.get("operator_quote") or not approval.get("merge_authorization")):
            raise ValueError("operator acceptance does not cover these source inputs")
    # The page carries only the artwork its copy and the source stylesheet reference.
    referenced = sorted(set(ASSET_REFERENCE.findall(
        content.read_text()
        + (SOURCE_ROOT / "source/presentation.css").read_text()
    )))
    (output / "assets").mkdir(parents=True)
    for name in referenced:
        shutil.copy2(SOURCE_ROOT / "assets" / name, output / "assets" / name)
    filename = "manual_" + source["model"].replace("-", "").lower()
    filename += "_" + source["region"].lower() + "_" + source["language"] + ".md"
    _write_myst_sphinx_scaffold(
        output / filename, title=source["title"], presentation_profile="web",
    )
    with (output / "conf.py").open("a") as stream:
        stream.write("\nlanguage = " + repr(source["language"]) + "\n")
    # Source-local geometry; shared styles still own components and breakpoints.
    source_css = output / "_static/source_presentation.css"
    shutil.copy2(SOURCE_ROOT / "source/presentation.css", source_css)
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source["model"], region=source["region"])
    pages = tuple(SourcePage(
        page_id=ch["id"], source_ref="native-pdf/" + ch["id"],
        source_path=f"source/{language}/content.json#" + ch["id"], language=source["language"],
        source_sha256=value_sha256(ch),
        blocks=tuple(("flow", flow) for flow in ch["nodes"]),
    ) for ch in source["chapters"])
    specs = component_specs_in_flow([b for page in pages for _, b in page.blocks])
    metadata = {
        "projection": "whole-document-components/v1",
        "title": source["title"], "markdown_filename": filename,
        "declared_languages": [source["language"]],
        "source_authority": {
            "filename": original["filename"], "sha256": source["source_sha256"],
            "physical_pages": manifest["included_pages"][language]["physical_pages"],
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
        "publication_eligible": approved,
        "pending_source_review": [] if approved else [
            "Git-only source candidate requires operator acceptance and separate merge/release authorization."
        ],
        "operator_source_acceptance": approval,
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
    parser.add_argument("--language", choices=("en", "fr", "es"), default="en")
    args = parser.parse_args()
    rebuild(args.output.resolve(), args.language)
