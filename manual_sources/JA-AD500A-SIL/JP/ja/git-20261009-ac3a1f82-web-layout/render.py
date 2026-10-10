"""Hash-checked Web-layout edition through the existing prepared Web pipeline.

Run from the repository with an unused output directory as the sole argument.
This adapter does not register a phase2 target or render its own HTML: the
prepared RST pages pass through manual-ir/v2 and the shared Web renderers; the
page-local ``source/presentation.css`` travels as the IR source stylesheet.
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
FILENAME = "manual_jaad500asil_jp_ja.md"
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
    if (approval["operator_quote"] != "上线提交发布"
            or approval["original_source_sha256"] != manifest["original_source"]["sha256"]
            or approval["target"] != {"model": "JA-AD500A-SIL", "region": "JP", "language": "ja"}
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


def render(source: Path, output: Path) -> dict:
    source, output = source.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(source):
        raise ValueError("use a new output directory outside the frozen input")
    manifest = json.loads((source / "source_manifest.json").read_text(encoding="utf-8"))
    check_inputs(source, manifest)
    approval = acceptance(source, manifest)
    page_dir = source / "source" / "page"
    bundle = SimpleNamespace(
        bundle_dir=source / "source", page_dir=page_dir,
        page_paths=tuple(page_dir / name for name in manifest["page_order"]),
        title="Jackery DC Input Module", reference_doc=None,
        model="JA-AD500A-SIL", region="JP", lang="ja", languages=("ja",),
    )
    previous = os.environ.get("AUTO_MANUAL_PRESENTATION_PROFILE")
    os.environ["AUTO_MANUAL_PRESENTATION_PROFILE"] = "web"
    try:
        export_markdown_from_bundle(
            {}, bundle.model, bundle.region, str(output / FILENAME),
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
        "markdown_filename": FILENAME,
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
    replay_package(output)
    with (output / "conf.py").open("a", encoding="utf-8") as stream:
        stream.write("language = 'ja'\n")
    return {"output": str(output), "components": counts, "publication_eligible": approval is not None}


if __name__ == "__main__":
    print(json.dumps(render(SOURCE, Path(sys.argv[1])), ensure_ascii=False, indent=2))
