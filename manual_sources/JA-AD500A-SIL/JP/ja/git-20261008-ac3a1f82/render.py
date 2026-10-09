"""Hash-checked source-local intake through the existing prepared Web pipeline.

Run from the repository with an unused output directory as the sole argument.
This adapter does not register a phase2 target or render its own HTML.
"""
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
import hashlib
import json
import os
import sys


SOURCE = Path(__file__).resolve().parent
ROOT = next(parent for parent in SOURCE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.manual_ir import read_manual_ir, write_manual_ir
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.document import validate_document
from tools.markdown_bundle import export_markdown_from_bundle
from tools.web.frozen_ai_web import replay_package


def main():
    output = Path(sys.argv[1]).resolve()
    if output.exists() or output.is_relative_to(SOURCE):
        raise ValueError("use a new output directory outside the frozen input")
    manifest = json.loads((SOURCE / "source_manifest.json").read_text())
    for entry in manifest["repo_inputs"]:
        path = (ROOT / entry["path"]).resolve()
        if (not path.is_relative_to(ROOT)
                or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]):
            raise ValueError(f"repository input changed: {entry['path']}")
    for entry in manifest["inputs"]:
        path = (SOURCE / entry["path"]).resolve()
        if not path.is_relative_to(SOURCE):
            raise ValueError("input escapes frozen source")
        if (path.stat().st_size != entry["size"]
                or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]):
            raise ValueError(f"frozen source changed: {entry['path']}")
    page_dir = SOURCE / "source" / "page"
    bundle = SimpleNamespace(
        bundle_dir=SOURCE / "source", page_dir=page_dir,
        page_paths=tuple(page_dir / name for name in manifest["page_order"]),
        title="Jackery DC Input Module", reference_doc=None,
        model="JA-AD500A-SIL", region="JP", lang="ja", languages=("ja",),
    )
    os.environ["AUTO_MANUAL_PRESENTATION_PROFILE"] = "web"
    filename = "manual_jaad500asil_jp_ja.md"
    export_markdown_from_bundle(
        {}, bundle.model, bundle.region, str(output / filename),
        materialized_bundle=bundle, output_dir=output,
    )
    ir = read_manual_ir(output / "manual.ir.json")
    specs = component_specs_in_flow([block.payload for p in ir.pages for block in p.blocks])
    counts = {key: sum(spec.component_id == key for spec in specs)
              for key in manifest["required_components"]}
    if counts != manifest["required_components"]:
        raise ValueError(f"source components missing or duplicated: {counts}")
    ir = replace(ir, bundle_root="frozen-source", metadata={
        **ir.metadata, "frozen_source_manifest": manifest,
        "markdown_filename": filename,
        "frozen_stylesheet_sha256": hashlib.sha256(
            (output / "_static" / "web_manual.css").read_bytes()).hexdigest(),
        "component_inventory": counts,
        "publication_eligible": False,
        "pending_source_review": ["Japanese operator source/layout confirmation"],
    })
    validate_document(ir)
    write_manual_ir(ir, output / "manual.ir.json")
    replay_package(output)
    with (output / "conf.py").open("a") as stream:
        stream.write("language = 'ja'\n")
    print(json.dumps({"output": str(output), "components": counts}, indent=2))


if __name__ == "__main__":
    main()
