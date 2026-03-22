#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_docs import build_root_for_target, load_config, render_build_template, resolve_output_path, resolve_product_name_for_build  # noqa: E402
from tools.gen_index_bundle import bundle_dir_for_target  # noqa: E402
from tools.review_bundle import resolve_docs_dir  # noqa: E402
from tools.review_support import review_dir_for_target  # noqa: E402


def _repo_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return path.as_posix()


def _read_git_sha() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = (proc.stdout or "").strip()
    return value or None


def _resolve_configured_path(cfg: dict, key: str, fallback: Path) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get(key)
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return fallback


def _build_langs(cfg: dict) -> list[str]:
    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = build_cfg.get("languages", ["en"])
    return [str(item).strip() for item in langs if str(item).strip()] or ["en"]


def _file_info(path: Path) -> dict[str, object]:
    exists = path.exists()
    sha256 = None
    if exists and path.is_file():
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": _repo_relative(path),
        "exists": exists,
        "sha256": sha256,
    }


def build_release_manifest(
    *,
    config_path: Path,
    model: str,
    region: str,
    built_at: datetime | None = None,
) -> tuple[Path, Path]:
    cfg = load_config(config_path)
    docs_dir = resolve_docs_dir(cfg)
    docs_build_dir = docs_dir / "_build"
    build_root = build_root_for_target(model, region, docs_build_dir=docs_build_dir)
    runtime_bundle_dir = bundle_dir_for_target(docs_dir=docs_dir, model=model, region=region)
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region)

    build_cfg_raw = cfg.get("build", {})
    build_cfg = build_cfg_raw if isinstance(build_cfg_raw, dict) else {}
    langs = _build_langs(cfg)
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

    word_output = resolve_output_path(build_root / "word", word_output_name)
    pdf_output = resolve_output_path(build_root / "pdf", pdf_output_name)
    html_output = build_root / "html" / "index.html"

    built_at_value = built_at or datetime.now(timezone.utc)
    timestamp = built_at_value.strftime("%Y%m%dT%H%M%SZ")
    manifest_dir = ROOT / "reports" / "releases" / model / region
    manifest_dir.mkdir(parents=True, exist_ok=True)
    json_path = manifest_dir / f"{timestamp}.json"
    csv_path = manifest_dir / f"{timestamp}.csv"

    spec_master_csv = _resolve_configured_path(cfg, "spec_master_csv", ROOT / "data" / "phase1" / "Spec_Master.csv")
    spec_footnotes_csv = _resolve_configured_path(cfg, "spec_footnotes_csv", ROOT / "data" / "phase1" / "Spec_Footnotes.csv")
    spec_titles_csv = _resolve_configured_path(cfg, "spec_titles_csv", ROOT / "data" / "phase1" / "spec_titles.csv")
    product_name = resolve_product_name_for_build(cfg, model=model, region=region, lang=primary_lang)

    manifest = {
        "git_sha": _read_git_sha(),
        "built_at": built_at_value.isoformat(),
        "config_path": _repo_relative(config_path),
        "model": model,
        "region": region,
        "build_languages": langs,
        "product_name": product_name,
        "spec_master_csv": _repo_relative(spec_master_csv),
        "spec_footnotes_csv": _repo_relative(spec_footnotes_csv),
        "spec_titles_csv": _repo_relative(spec_titles_csv),
        "tracked_review_dir": _repo_relative(review_dir),
        "runtime_bundle_dir": _repo_relative(runtime_bundle_dir),
        "word_output": _file_info(word_output),
        "html_output": _file_info(html_output),
        "pdf_output": _file_info(pdf_output),
    }
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csv_row = {
        "git_sha": manifest["git_sha"] or "",
        "built_at": manifest["built_at"],
        "config_path": manifest["config_path"] or "",
        "model": model,
        "region": region,
        "build_languages": ",".join(langs),
        "product_name": product_name or "",
        "spec_master_csv": manifest["spec_master_csv"] or "",
        "spec_footnotes_csv": manifest["spec_footnotes_csv"] or "",
        "spec_titles_csv": manifest["spec_titles_csv"] or "",
        "tracked_review_dir": manifest["tracked_review_dir"] or "",
        "runtime_bundle_dir": manifest["runtime_bundle_dir"] or "",
        "word_output": manifest["word_output"]["path"] or "",
        "word_output_exists": str(manifest["word_output"]["exists"]).lower(),
        "word_output_sha256": manifest["word_output"]["sha256"] or "",
        "html_output": manifest["html_output"]["path"] or "",
        "html_output_exists": str(manifest["html_output"]["exists"]).lower(),
        "html_output_sha256": manifest["html_output"]["sha256"] or "",
        "pdf_output": manifest["pdf_output"]["path"] or "",
        "pdf_output_exists": str(manifest["pdf_output"]["exists"]).lower(),
        "pdf_output_sha256": manifest["pdf_output"]["sha256"] or "",
    }
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_row))
        writer.writeheader()
        writer.writerow(csv_row)

    return json_path, csv_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Write a release manifest for one explicit target.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--model", required=True, help="Explicit release target model")
    ap.add_argument("--region", required=True, help="Explicit release target region")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = ROOT / config_path

    try:
        json_path, csv_path = build_release_manifest(
            config_path=config_path,
            model=args.model,
            region=args.region,
        )
    except RuntimeError as exc:
        print(f"[release-manifest] ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"[release-manifest] JSON: {json_path}")
    print(f"[release-manifest] CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
