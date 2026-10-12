"""Replay this Web-layout edition through the shared Manual IR APIs.

Run from the repository root with an unused --output directory. This freezes no
online data and enrolls no phase2/print target. Source selections, visual text
recoveries and artwork decisions remain independently reviewable JSON inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO_ROOT))
ASSET_REFERENCE = re.compile(r"assets/([A-Za-z0-9_.\-]+)")


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


def rebuild(output: Path, language: str) -> None:
    if output.exists():
        raise ValueError("use an unused output directory")
    source = json.loads((SOURCE_ROOT / f"source/{language}/content.json").read_text())
    pdfs = list(SOURCE_ROOT.glob("*.pdf"))
    if len(pdfs) != 1 or file_sha256(pdfs[0]) != source["source_sha256"]:
        raise ValueError("authoritative PDF identity changed")
    manifest_path = SOURCE_ROOT / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    check_inventory(SOURCE_ROOT, manifest["inputs"])
    check_inventory(REPO_ROOT, manifest["repo_inputs"])
    # A Web-layout candidate is publishable only after the operator accepts these exact
    # source inputs (source/approval.json); frozen web/ outputs are not part of that review.
    approved = manifest.get("publication_status") == "operator-approved-git-only-release"
    approval = None
    if approved:
        acceptance = SOURCE_ROOT / "source/approval.json"
        approval = json.loads(acceptance.read_text()) if acceptance.is_file() else {}
        reviewed = [row for row in manifest["inputs"]
                    if not row["path"].startswith("web/") and row["path"] != "source/approval.json"]
        if (approval.get("target") != {key: manifest["target"][key] for key in ("model", "region", "technical_version")}
                or approval.get("original_source_sha256") != manifest["original_source"]["sha256"]
                or approval.get("reviewed_inputs") != reviewed
                or not approval.get("operator_quote") or not approval.get("merge_authorization")):
            raise ValueError("operator acceptance does not cover these source inputs")
    # Shared variant copies are immutable inputs; obsolete hashes are refused
    # again at fresh sealing, independent of the source-local inventory. Each
    # locale carries only the artwork its own copy and the source stylesheet
    # reference, so the other locales' redrawn variants stay in the pool.
    referenced = sorted(set(ASSET_REFERENCE.findall(
        (SOURCE_ROOT / f"source/{language}/content.json").read_text()
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
    # Source-local geometry corrections; shared styles still own components and breakpoints.
    source_css = output / "_static/source_presentation.css"
    shutil.copy2(SOURCE_ROOT / "source/presentation.css", source_css)
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source["model"], region=source["region"])
    pages = tuple(SourcePage(
        page_id=ch["id"], source_ref="native-pdf/" + ch["id"],
        source_path="source/" + language + "/content.json#" + ch["id"], language=source["language"],
        source_sha256=value_sha256(ch),
        blocks=tuple(("flow", flow) for flow in ch["nodes"]),
    ) for ch in source["chapters"])
    specs = component_specs_in_flow([b for page in pages for _, b in page.blocks])
    metadata = {
        "projection": "whole-document-components/v1",
        "web_source_normalization": "preface-auto-resume/v1",
        "title": source["title"], "markdown_filename": filename,
        "publication_eligible": approved,
        "pending_source_review": [] if approved else [
            "Web-layout candidate requires operator acceptance and separate merge/release authorization."
        ],
        "operator_source_acceptance": approval,
        "declared_languages": [source["language"]],
        "source_authority": {
            "filename": pdfs[0].name, "sha256": source["source_sha256"],
            "physical_pages": [2, *range({"en": 4, "fr": 28, "es": 52}[language], {"en": 28, "fr": 52, "es": 76}[language]), 76],
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
    parser.add_argument("--language", choices=("en", "fr", "es"), default="en")
    args = parser.parse_args()
    rebuild(args.output.resolve(), args.language)
