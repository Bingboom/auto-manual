from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from tools.build_docs import (
    build_root_for_target,
    load_config,
    render_build_template,
    resolve_output_path,
    resolve_product_name_for_build,
)
from tools.data_snapshot import resolve_data_snapshot_paths
from tools.gen_index_bundle import bundle_dir_for_target
from tools.release_contract import release_manifests_dir_for_target
from tools.review_bundle import resolve_docs_dir
from tools.review_support import review_dir_for_target
from tools.toolchain_provenance import collect_toolchain
from tools.utils.path_utils import docs_build_dir_of
from tools.utils.targets import resolve_output_lang


def repo_relative(path: Path | None, *, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        return path.as_posix()


def build_langs(cfg: dict) -> list[str]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = build_cfg.get("languages", ["en"])
    return [str(item).strip() for item in langs if str(item).strip()] or ["en"]


def file_info(path: Path, *, repo_root: Path) -> dict[str, object]:
    exists = path.exists()
    sha256 = None
    if exists and path.is_file():
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": repo_relative(path, repo_root=repo_root),
        "exists": exists,
        "sha256": sha256,
    }


def build_release_manifest(
    *,
    repo_root: Path,
    config_path: Path,
    model: str,
    region: str,
    git_sha: str | None,
    data_root: str | None = None,
    built_at: datetime | None = None,
    docs_build_dir: Path | None = None,
    releases_root: Path | None = None,
    toolchain: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    cfg = load_config(config_path)
    docs_dir = resolve_docs_dir(cfg)
    output_lang = resolve_output_lang(cfg)
    actual_docs_build_dir = docs_build_dir or docs_build_dir_of(docs_dir)
    build_root = build_root_for_target(model, region, output_lang, docs_build_dir=actual_docs_build_dir)
    runtime_bundle_dir = bundle_dir_for_target(
        docs_dir=docs_dir,
        docs_build_dir=actual_docs_build_dir,
        model=model,
        region=region,
        lang=output_lang,
    )
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=output_lang)

    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = build_langs(cfg)
    primary_lang = langs[0]

    word_output_name = render_build_template(
        str(build_cfg.get("word_output", "manual_demo.docx")),
        model=model,
        region=region,
        lang=primary_lang,
    )
    pdf_output_name = render_build_template(
        str(build_cfg.get("output_pdf", "manual_demo.pdf")),
        model=model,
        region=region,
        lang=primary_lang,
    )
    md_output_template = build_cfg.get("md_output")
    if isinstance(md_output_template, str) and md_output_template.strip():
        md_output_name = render_build_template(
            md_output_template,
            model=model,
            region=region,
            lang=primary_lang,
        )
    else:
        md_output_name = Path(word_output_name).with_suffix(".md").as_posix()

    word_output = resolve_output_path(build_root / "word", word_output_name)
    pdf_output = resolve_output_path(build_root / "pdf", pdf_output_name)
    md_output = resolve_output_path(build_root / "md", md_output_name)
    html_output = build_root / "html" / "index.html"

    built_at_value = built_at or datetime.now(timezone.utc)
    timestamp = built_at_value.strftime("%Y%m%dT%H%M%SZ")
    manifest_dir = release_manifests_dir_for_target(
        repo_root=repo_root,
        config_path=config_path,
        model=model,
        region=region,
        cfg=cfg,
        releases_root=releases_root,
    )
    manifest_dir.mkdir(parents=True, exist_ok=True)
    json_path = manifest_dir / f"{timestamp}.json"
    csv_path = manifest_dir / f"{timestamp}.csv"

    snapshot_paths = resolve_data_snapshot_paths(
        cfg,
        repo_root=repo_root,
        data_root=data_root,
        model=model,
        region=region,
    )
    product_name = resolve_product_name_for_build(
        cfg,
        model=model,
        region=region,
        lang=primary_lang,
        data_root=data_root,
        repo_root=repo_root,
    )

    # Toolchain provenance (Milestone I3): the release must be able to name the
    # exact environment that produced it — the LaTeX line has no golden
    # snapshot, so this record is the only way to attribute a rendering drift.
    toolchain_record = toolchain if toolchain is not None else collect_toolchain(repo_root=repo_root)

    manifest = {
        "git_sha": git_sha,
        "built_at": built_at_value.isoformat(),
        "toolchain": toolchain_record,
        "config_path": repo_relative(config_path, repo_root=repo_root),
        "model": model,
        "region": region,
        "build_languages": langs,
        "product_name": product_name,
        "spec_master_csv": repo_relative(snapshot_paths.spec_master_csv, repo_root=repo_root),
        "spec_footnotes_csv": repo_relative(snapshot_paths.spec_footnotes_csv, repo_root=repo_root),
        "spec_notes_csv": repo_relative(snapshot_paths.spec_notes_csv, repo_root=repo_root),
        "spec_titles_csv": repo_relative(snapshot_paths.spec_titles_csv, repo_root=repo_root),
        "tracked_review_dir": repo_relative(review_dir, repo_root=repo_root),
        "runtime_bundle_dir": repo_relative(runtime_bundle_dir, repo_root=repo_root),
        "word_output": file_info(word_output, repo_root=repo_root),
        "md_output": file_info(md_output, repo_root=repo_root),
        "html_output": file_info(html_output, repo_root=repo_root),
        "pdf_output": file_info(pdf_output, repo_root=repo_root),
    }
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csv_row = {
        "git_sha": manifest["git_sha"] or "",
        "built_at": manifest["built_at"],
        "toolchain_python": str(toolchain_record.get("python") or ""),
        "toolchain_xelatex": str(toolchain_record.get("xelatex") or ""),
        "toolchain_pandoc": str(toolchain_record.get("pandoc") or ""),
        "config_path": manifest["config_path"] or "",
        "model": model,
        "region": region,
        "build_languages": ",".join(langs),
        "product_name": product_name or "",
        "spec_master_csv": manifest["spec_master_csv"] or "",
        "spec_footnotes_csv": manifest["spec_footnotes_csv"] or "",
        "spec_notes_csv": manifest["spec_notes_csv"] or "",
        "spec_titles_csv": manifest["spec_titles_csv"] or "",
        "tracked_review_dir": manifest["tracked_review_dir"] or "",
        "runtime_bundle_dir": manifest["runtime_bundle_dir"] or "",
        "word_output": manifest["word_output"]["path"] or "",
        "word_output_exists": str(manifest["word_output"]["exists"]).lower(),
        "word_output_sha256": manifest["word_output"]["sha256"] or "",
        "md_output": manifest["md_output"]["path"] or "",
        "md_output_exists": str(manifest["md_output"]["exists"]).lower(),
        "md_output_sha256": manifest["md_output"]["sha256"] or "",
        "html_output": manifest["html_output"]["path"] or "",
        "html_output_exists": str(manifest["html_output"]["exists"]).lower(),
        "html_output_sha256": manifest["html_output"]["sha256"] or "",
        "pdf_output": manifest["pdf_output"]["path"] or "",
        "pdf_output_exists": str(manifest["pdf_output"]["exists"]).lower(),
        "pdf_output_sha256": manifest["pdf_output"]["sha256"] or "",
    }
    import csv

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_row))
        writer.writeheader()
        writer.writerow(csv_row)

    return json_path, csv_path
