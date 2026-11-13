"""Replay a source-bound Japanese candidate through the existing shared Web IR consumer."""

import argparse
import json
from pathlib import Path
import shutil
import sys

PACKAGE = Path(__file__).resolve().parent
REPO = next(p for p in PACKAGE.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
from tools.component_specs.registry import load_component_registry, registry_sha256  # noqa: E402
from tools.component_specs.theme import load_manual_theme, theme_sha256  # noqa: E402
from tools.manual_ir import (
    ManualSource,
    SourcePage,
    V2_SCHEMA_VERSION,
    build_manual_ir_from_source,
    write_manual_ir,
)  # noqa: E402
from tools.manual_ir.components import component_specs_in_flow  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import file_sha256, value_sha256  # noqa: E402
from tools.markdown_bundle import _write_myst_sphinx_scaffold  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.presentation import load_web_manual_contract  # noqa: E402
from tools.web.prepared_style_audit import require_prepared_document_styles  # noqa: E402


def rebuild(output):
    if output.exists():
        raise ValueError("use an unused output directory")
    manifest = json.loads((PACKAGE / "source_manifest.json").read_text())
    for base, rows in [(PACKAGE, manifest["inputs"]), (REPO, manifest["repo_inputs"])]:
        for row in rows:
            path = (base / row["path"]).resolve()
            if (
                not path.is_relative_to(base)
                or not path.is_file()
                or file_sha256(path) != row["sha256"]
            ):
                raise ValueError("input missing or changed: " + row["path"])
    source = json.loads((PACKAGE / "source/content.json").read_text())
    if (
        file_sha256(PACKAGE / manifest["original_source"]["path"])
        != source["source_sha256"]
    ):
        raise ValueError("authoritative PDF changed")
    if (
        manifest["publication_eligible"]
        or manifest["publication_status"] != "review-candidate-no-release-authorization"
    ):
        raise ValueError("candidate carries no release approval")
    shutil.copytree(PACKAGE / "assets", output / "assets")
    filename = "manual_js40a_jp_ja.md"
    _write_myst_sphinx_scaffold(
        output / filename, title=source["title"], presentation_profile="web"
    )
    with (output / "conf.py").open("a") as stream:
        stream.write("\nlanguage = 'ja'\n")
    shutil.copy2(
        PACKAGE / "source/geometry.css", output / "_static/source_geometry.css"
    )
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source["model"], region=source["region"])
    pages = tuple(
        SourcePage(
            page_id=ch["id"],
            source_ref="outlined-pdf/" + ch["id"],
            source_path="source/content.json#" + ch["id"],
            language="ja",
            source_sha256=value_sha256(ch),
            blocks=tuple(("flow", flow) for flow in ch["nodes"]),
        )
        for ch in source["chapters"]
    )
    specs = component_specs_in_flow(
        [block for page in pages for _, block in page.blocks]
    )
    counts = {
        identity: sum(s.component_id == identity for s in specs)
        for identity in sorted({s.component_id for s in specs})
    }
    if counts != manifest["required_components"]:
        raise ValueError("component inventory differs: " + str(counts))
    metadata = {
        "projection": "whole-document-components/v1",
        "title": source["title"],
        "markdown_filename": filename,
        "declared_languages": ["ja"],
        "publication_eligible": False,
        "operator_source_acceptance": None,
        "pending_source_review": manifest["pending_source_review"],
        "frozen_source_manifest": manifest,
        "source_authority": manifest["original_source"],
        "asset_sha256": {
            p.relative_to(output).as_posix(): file_sha256(p)
            for p in sorted((output / "assets").rglob("*"))
            if p.is_file()
        },
        "component_registry": registry,
        "component_registry_sha256": registry_sha256(registry),
        "manual_theme": theme,
        "manual_theme_sha256": theme_sha256(theme),
        "web_contract": contract,
        "composites": [],
        "page_declarations": {},
        "frozen_stylesheet_sha256": file_sha256(output / "_static/web_manual.css"),
        "source_stylesheet": {
            "path": "_static/source_geometry.css",
            "sha256": file_sha256(output / "_static/source_geometry.css"),
        },
        "component_inventory": counts,
    }
    ir = build_manual_ir_from_source(
        ManualSource(
            model=source["model"],
            region=source["region"],
            language="ja",
            source="prepared-document",
            bundle_root="frozen-source",
            bundle_sha256=value_sha256(source),
            snapshot_sha256=None,
            layout_params_sha256=value_sha256({"layout": "shared-web"}),
            style_contract_sha256=value_sha256(contract),
            pages=pages,
            metadata=metadata,
            schema_version=V2_SCHEMA_VERSION,
        )
    )
    validate_document(ir)
    require_prepared_document_styles(
        ir.to_dict(),
        stylesheet=(PACKAGE / "source/geometry.css").read_text(),
        exceptions=(),
    )
    write_manual_ir(ir, output / "manual.ir.json")
    replay_package(output)
    print(
        json.dumps(
            {
                "output": str(output),
                "chapters": len(pages),
                "components": counts,
                "shared_style_admission": "passed",
                "publication_eligible": False,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    rebuild(p.parse_args().output.resolve())
