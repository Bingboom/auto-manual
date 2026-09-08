"""Build local standalone packages from one frozen review bundle; no upload."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from tools.build_docs import load_config, prepare_manual_bundle
from tools.markdown_bundle import export_markdown_from_bundle
from tools.utils.path_utils import docs_build_dir_of
from tools.web_language_bundle import split_web_bundle
from tools.web_manual_package import (
    PACKAGE_UI, archive_package, build_local_preview_bundle, build_package_site, print_package_pdf, safe_segment, write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--model", required=True, type=safe_segment)
    parser.add_argument("--region", required=True, type=safe_segment)
    parser.add_argument("--version", required=True, type=safe_segment)
    parser.add_argument("--languages", nargs="+", choices=tuple(PACKAGE_UI), required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--source", choices=("review-asis", "auto"), default="review-asis")
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--node", default="node")
    parser.add_argument("--browser", help="Chrome executable; otherwise use Playwright Chromium")
    args = parser.parse_args()
    languages = tuple(args.languages)
    if len(set(languages)) != len(languages):
        parser.error("languages must be unique")
    work = args.work_dir.resolve()
    output = args.output_dir.resolve()
    if work.exists() or output.exists() or work.is_relative_to(output) or output.is_relative_to(work):
        parser.error("work-dir and output-dir must be new, separate directories")
    cfg = load_config(args.config)
    # Keep the existing target directory contract used by figure selectors.
    target = docs_build_dir_of(work) / args.model / args.region
    bundle = prepare_manual_bundle(
        cfg, model=args.model, region=args.region, data_root=args.data_root,
        source_mode=args.source, output_root=target / "source", write_wrapper_index=False,
    )
    release = output / args.model / args.region / args.version
    release.mkdir(parents=True)
    os.environ["AUTO_MANUAL_PRESENTATION_PROFILE"] = "web"
    packages = {}
    for language in languages:
        derivative = split_web_bundle(bundle, language=language, destination=target / language / "rst")
        stem = f"manual_{args.model.replace('-', '').lower()}_{args.region.lower()}_{language}"
        markdown = export_markdown_from_bundle(
            cfg, args.model, args.region, f"{stem}.md", materialized_bundle=derivative,
            output_dir=target / language / "md",
        )
        package = release / language
        html = build_package_site(
            markdown, title=bundle.title, language=language, languages=languages,
            pdf_name=f"{stem}.pdf", source_dir=target / language / "site-source", output_dir=package,
        )
        print_package_pdf(html, package / f"{stem}.pdf", node=args.node, browser=args.browser)
        packages[language] = archive_package(package, release / f"{stem}_{args.version}.zip")
        packages[language]["source_projection"] = json.loads(derivative.manifest_path.read_text(encoding="utf-8"))
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    preview = build_local_preview_bundle(release, destination=work / "manual-preview", languages=languages)
    preview_archive = archive_package(preview, release / f"manual_{args.model.lower()}_{args.region.lower()}_{args.version}_all.zip")
    write_json(release / "release.json", {
        "schema_version": "web-package-release/v1", "model": args.model, "region": args.region,
        "version": args.version, "source_revision": revision, "packages": packages,
        "local_preview": preview_archive,
    })
    write_json(release.parent / "catalog.json", {
        "model": args.model, "region": args.region, "version": args.version,
        "languages": {lang: f"{args.version}/{lang}/index.html" for lang in languages},
    })
    print(f"Local release ready: {release}")


if __name__ == "__main__":
    main()
