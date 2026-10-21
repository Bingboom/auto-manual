"""Replay the Git-only JE-2000F JP candidate through the repository's shared Manual IR."""

from pathlib import Path
import argparse
import json
import re
import shutil
import sys

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO_ROOT))
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
from tools.utils.path_utils import PathSegments  # noqa: E402
from tools.web.frozen_ai_web import replay_package  # noqa: E402
from tools.web.prepared_style_audit import require_prepared_document_styles  # noqa: E402
from tools.web.presentation import load_web_manual_contract  # noqa: E402


def check_inventory(base, rows):
    for row in rows:
        path = (base / row["path"]).resolve()
        if (
            not path.is_relative_to(base.resolve())
            or not path.is_file()
            or file_sha256(path) != row["sha256"]
        ):
            raise ValueError("pinned input missing or changed: " + row["path"])


def rebuild(output):
    if output.exists():
        raise ValueError("use an unused output directory")
    manifest = json.loads((SOURCE_ROOT / "source_manifest.json").read_text())
    check_inventory(SOURCE_ROOT, manifest["inputs"])
    check_inventory(REPO_ROOT, manifest["repo_inputs"])
    source = json.loads((SOURCE_ROOT / "source/ja/content.json").read_text())
    identity = json.loads((SOURCE_ROOT / "source/pdf-identity.json").read_text())
    import hashlib

    raw = b"".join(
        (SOURCE_ROOT / part["path"]).read_bytes() for part in identity["archive_parts"]
    )
    if hashlib.sha256(raw).hexdigest() != source["source_sha256"]:
        raise ValueError("authority PDF identity changed")
    refs = sorted(set(re.findall(r"assets/[A-Za-z0-9_.-]+", json.dumps(source))))
    (output / "assets").mkdir(parents=True)
    for ref in refs:
        shutil.copyfile(SOURCE_ROOT / ref, output / ref)
    filename = "manual_je2000f_jp_ja.md"
    _write_myst_sphinx_scaffold(
        output / filename, title=source["title"], presentation_profile="web"
    )
    with (output / "conf.py").open("a") as stream:
        stream.write("\nlanguage = 'ja'\n")
    registry = load_component_registry()
    theme = load_manual_theme(component_registry=registry)
    contract = load_web_manual_contract(model=source["model"], region=source["region"])
    pages = tuple(
        SourcePage(
            page_id=ch["id"],
            source_ref="native-pdf/" + ch["id"],
            source_path="source/ja/content.json#" + ch["id"],
            language="ja",
            source_sha256=value_sha256(ch),
            blocks=tuple(("flow", n) for n in ch["nodes"]),
        )
        for ch in source["chapters"]
    )
    specs = component_specs_in_flow(
        [payload for page in pages for _, payload in page.blocks]
    )
    metadata = {
        "projection": "whole-document-components/v1",
        "web_source_normalization": "preface-auto-resume/v1",
        "title": source["title"],
        "markdown_filename": filename,
        "declared_languages": ["ja"],
        "publication_eligible": False,
        "pending_source_review": [
            "Native JE-2000F JP candidate awaits operator source/artwork review and separate merge/release authorization."
        ],
        "source_authority": identity,
        "asset_sha256": {ref: file_sha256(output / ref) for ref in refs},
        "component_registry": registry,
        "component_registry_sha256": registry_sha256(registry),
        "manual_theme": theme,
        "manual_theme_sha256": theme_sha256(theme),
        "web_contract": contract,
        "composites": [],
        "page_declarations": {},
        "frozen_stylesheet_sha256": file_sha256(output / "_static/web_manual.css"),
        "component_inventory": {
            key: sum(s.component_id == key for s in specs)
            for key in sorted({s.component_id for s in specs})
        },
    }
    ir = build_manual_ir_from_source(
        ManualSource(
            model="JE-2000F",
            region="JP",
            language="ja",
            source="prepared-document",
            bundle_root="frozen-source",
            bundle_sha256=value_sha256(source),
            snapshot_sha256=None,
            layout_params_sha256=value_sha256({"layout": "web"}),
            style_contract_sha256=value_sha256(contract),
            pages=pages,
            metadata=metadata,
            schema_version=V2_SCHEMA_VERSION,
        )
    )
    validate_document(ir)
    report = require_prepared_document_styles(
        ir.to_dict(), exceptions=manifest.get("shared_component_exceptions", [])
    )
    write_manual_ir(ir, output / PathSegments.MANUAL_IR_JSON)
    replay_package(output)
    print(
        json.dumps(
            {
                "output": str(output),
                "chapters": len(pages),
                "components": metadata["component_inventory"],
                "shared_styles": report,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return ir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    rebuild(parser.parse_args().output.resolve())
