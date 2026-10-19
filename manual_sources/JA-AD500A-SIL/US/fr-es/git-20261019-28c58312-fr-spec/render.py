"""Hash-checked French spec-label correction edition through the existing prepared Web pipeline.

Run from the repository with the language (``fr``) and an unused output directory.
This adapter does not register a phase2 target or render its own HTML: the
prepared RST pages pass through manual-ir/v2 and the shared Web renderers; the
page-local, geometry-only ``source/presentation.css`` travels as the IR source stylesheet.
A review candidate renders without a release acceptance and is not
publication-eligible; an approved edition needs ``source/approval.json``
binding every reviewed ``source/`` and ``assets/`` input.
"""
from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
import hashlib
import json
import os
import shutil
import sys


SOURCE = Path(__file__).resolve().parent
ROOT = next(parent for parent in SOURCE.parents if (parent / "build.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.manual_ir import read_manual_ir, write_manual_ir  # noqa: E402
from tools.manual_ir.components import component_specs_in_flow  # noqa: E402
from tools.manual_ir.document import validate_document  # noqa: E402
from tools.manual_ir.hashing import value_sha256  # noqa: E402
from tools.markdown_bundle import _rewrite_local_file_uris_to_relative, export_markdown_from_bundle  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402

APPROVED = "operator-approved-git-only-release"
CANDIDATE = "review-candidate-no-release-authorization"
TARGET = {"model": "JA-AD500A-SIL", "region": "US", "languages": ["fr"]}
STYLESHEET = "_static/source.css"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_inputs(source: Path, manifest: dict) -> None:
    for entry in manifest["repo_inputs"]:
        path = (ROOT / entry["path"]).resolve()
        if not path.is_relative_to(ROOT) or sha256(path) != entry["sha256"]:
            raise ValueError(f"repository input changed: {entry['path']}")
    listed = set()
    for entry in manifest["inputs"]:
        path = (source / entry["path"]).resolve()
        if not path.is_relative_to(source):
            raise ValueError("input escapes frozen source")
        if not path.is_file() or path.stat().st_size != entry["size"] or sha256(path) != entry["sha256"]:
            raise ValueError(f"frozen source input changed: {entry['path']}")
        listed.add(entry["path"])
    present = {p.relative_to(source).as_posix() for root in ("assets", "source")
               for p in (source / root).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    if not present <= listed:
        raise ValueError(f"manifest does not cover every input: {sorted(present - listed)}")


def acceptance(source: Path, manifest: dict) -> dict | None:
    """Return the operator acceptance that binds every reviewed source and artwork input, if any."""
    path = source / "source" / "approval.json"
    if manifest["publication_status"] == CANDIDATE:
        if path.exists() or manifest["publication_eligible"]:
            raise ValueError("a review candidate carries no release acceptance")
        return None
    if manifest["publication_status"] != APPROVED or not path.is_file():
        raise ValueError("unknown publication status or missing acceptance")
    approval = json.loads(path.read_text(encoding="utf-8"))
    reviewed = [entry for entry in manifest["inputs"]
                if entry["path"].startswith(("source/", "assets/")) and entry["path"] != "source/approval.json"]
    if (not approval.get("operator_quote")
            or approval["original_source_sha256"] != manifest["original_source"]["sha256"]
            or approval["target"] != TARGET
            or approval["reviewed_inputs"] != reviewed):
        raise ValueError("operator acceptance does not cover these inputs")
    return approval


def relocatable_ir(path: Path, source: Path) -> None:
    """Make page paths and component source refs package-relative; re-derive the content hashes."""
    prefix = json.dumps(source.as_posix() + "/")[1:-1]
    raw = json.loads(path.read_text(encoding="utf-8").replace(prefix, ""))
    block_hashes = []
    for page in raw["pages"]:
        for block in page["blocks"]:
            block["content_sha256"] = value_sha256({"kind": block["kind"], "payload": block["payload"]})
            block_hashes.append(block["content_sha256"])
    raw["content_sha256"] = value_sha256(
        {"page_ids": [page["page_id"] for page in raw["pages"]], "block_hashes": block_hashes})
    text = json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if source.as_posix() in text:
        raise ValueError("IR still carries the absolute source path")
    path.write_text(text, encoding="utf-8")


def render(source: Path, lang: str, output: Path) -> dict:
    if lang not in TARGET["languages"]:
        raise ValueError("language must be fr")
    filename = f"manual_jaad500asil_us_{lang}.md"
    source, output = source.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(source):
        raise ValueError("use a new output directory outside the frozen input")
    manifest = json.loads((source / "source_manifest.json").read_text(encoding="utf-8"))
    check_inputs(source, manifest)
    approval = acceptance(source, manifest)
    page_dir = source / "source" / "page"
    bundle = SimpleNamespace(
        bundle_dir=source / "source", page_dir=page_dir,
        page_paths=tuple(page_dir / name for name in manifest["page_order"][lang]),
        title="Jackery DC Input Module", reference_doc=None,
        model=TARGET["model"], region=TARGET["region"], lang=lang, languages=(lang,),
    )
    previous = os.environ.get("AUTO_MANUAL_PRESENTATION_PROFILE")
    os.environ["AUTO_MANUAL_PRESENTATION_PROFILE"] = "web"
    try:
        export_markdown_from_bundle(
            {}, bundle.model, bundle.region, str(output / filename),
            materialized_bundle=bundle, output_dir=output,
        )
    finally:
        if previous is None:
            os.environ.pop("AUTO_MANUAL_PRESENTATION_PROFILE", None)
        else:
            os.environ["AUTO_MANUAL_PRESENTATION_PROFILE"] = previous
    # The intermediate bundle must not carry this machine's absolute paths.
    _rewrite_local_file_uris_to_relative(output / "manual_bundle.html")
    ir = read_manual_ir(output / "manual.ir.json")
    specs = component_specs_in_flow([block.payload for p in ir.pages for block in p.blocks])
    counts = {key: sum(spec.component_id == key for spec in specs)
              for key in manifest["required_components"]}
    if counts != manifest["required_components"]:
        raise ValueError(f"source components missing or duplicated: {counts}")
    shutil.copyfile(source / "source" / "presentation.css", output / STYLESHEET)
    ir = replace(ir, bundle_root="frozen-source", metadata={
        **ir.metadata, "frozen_source_manifest": manifest,
        "markdown_filename": filename,
        "frozen_stylesheet_sha256": sha256(output / "_static" / "web_manual.css"),
        "source_stylesheet": {"path": STYLESHEET, "sha256": sha256(output / STYLESHEET)},
        "component_inventory": counts,
        "publication_eligible": approval is not None,
        "operator_source_acceptance": approval,
        "pending_source_review": manifest["pending_source_review"],
    })
    write_manual_ir(ir, output / "manual.ir.json")
    relocatable_ir(output / "manual.ir.json", source)
    validate_document(read_manual_ir(output / "manual.ir.json"))
    # Fresh prepared-source assembly above owns component discovery; public replay
    # then validates all ComponentSpec slots and actual packaged asset bytes.
    replay_package(output)
    with (output / "conf.py").open("a", encoding="utf-8") as stream:
        stream.write(f"language = {lang!r}\n")
    return {"output": str(output), "components": counts, "publication_eligible": approval is not None}


if __name__ == "__main__":
    print(json.dumps(render(SOURCE, sys.argv[1], Path(sys.argv[2])), ensure_ascii=False, indent=2))
