"""Rebuild one frozen native language through shared RST/MyST/Manual IR APIs."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

SOURCE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = next(p for p in SOURCE_ROOT.parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO_ROOT))

from tools.gen_index_bundle_models import MaterializedBundle  # noqa: E402
from tools.markdown_bundle import export_markdown_from_bundle  # noqa: E402
from tools.manual_ir import read_manual_ir, write_manual_ir  # noqa: E402


def rebuild(language: str, output: Path) -> None:
    """Validate frozen inputs and render a source-native language to a new root."""
    manifest = json.loads((SOURCE_ROOT / "source_manifest.json").read_text())
    if language not in manifest["target"]["languages"]:
        raise ValueError("language is outside this native source")
    if output.exists():
        raise ValueError("use an unused output directory")
    for base, key in [(SOURCE_ROOT, "inputs"), (REPO_ROOT, "repo_inputs")]:
        for row in manifest[key]:
            path = (base / row["path"]).resolve()
            if not path.is_relative_to(base):
                raise ValueError("input escaped its pinned root")
            if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError("frozen input changed: " + row["path"])
    os.environ["AUTO_MANUAL_PRESENTATION_PROFILE"] = "web"
    root = SOURCE_ROOT / "source" / language
    names = ["disclaimer", "specifications", "dimensions", "box_contents",
             "product_overview", "important_safety", "faq", "installation", "warranty"]
    paths = tuple(root / f"{name}_{language}.rst" for name in names)
    capture = json.loads((root / "capture.json").read_text())
    title = next(row["text"] for row in capture["roles"] if row["role"] == "spec-value-0")
    bundle = MaterializedBundle(
        bundle_dir=root, page_dir=root, index_path=root / "index.rst",
        conf_path=root / "conf.py", conf_base_path=root / "conf_base.py",
        wrapper_index_path=root / "index.rst", page_paths=paths, title=title,
        reference_doc=None, model="JA-AD600A", region="EU", lang=language,
        languages=(language,),
    )
    config = {
        "build": {"web_entry_source_patterns": ["disclaimer*"]},
        "paths": {"web_illustration_manifest": str(SOURCE_ROOT / f"illustrations_{language}.json")},
        "pages": [{"type": "rst_include", "slot_id": name + "_" + language,
                   "lang": language, "file": str(root / f"{name}_{language}.rst")}
                  for name in names],
    }
    output.mkdir(parents=True)
    markdown_path = export_markdown_from_bundle(
        config, "JA-AD600A", "EU", f"manual_jaad600a_eu_{language}.md",
        materialized_bundle=bundle, output_dir=output,
    )
    shutil.copy2(SOURCE_ROOT / "presentation.css", output / "_static/dcdc_source_local.css")
    # Portal assembly owns global CSS; carry the reviewed source-local rules
    # with this document, preserving the shared exporter's body verbatim.
    stylesheet = output / "_static/dcdc_source_local.css"
    style_text = stylesheet.read_text()
    if "</style" in style_text.lower():
        raise ValueError("source stylesheet contains HTML")
    ir = read_manual_ir(output / "manual.ir.json")
    metadata = {**ir.metadata,
                "markdown_filename": markdown_path.name,
                "frozen_stylesheet_sha256": hashlib.sha256(
                    (output / "_static/web_manual.css").read_bytes()).hexdigest(),
                "source_stylesheet": {
                    "path": "_static/dcdc_source_local.css",
                    "sha256": hashlib.sha256(stylesheet.read_bytes()).hexdigest()}}
    write_manual_ir(replace(ir, metadata=metadata), output / "manual.ir.json")
    markdown_path.write_text("<style>\n" + style_text + "\n</style>\n\n" +
                             markdown_path.read_text())
    with (output / "conf.py").open("a") as stream:
        stream.write(f"\nlanguage = {language!r}\nhtml_css_files.append('dcdc_source_local.css')\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rebuild(args.language, args.output.resolve())
