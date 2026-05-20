#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.build_docs import BuildTarget, build_root_for_target, load_config, resolve_build_targets  # noqa: E402
from tools.gen_index_bundle import bundle_dir_for_target  # noqa: E402
from tools.review_support import review_dir_for_target  # noqa: E402


@dataclass(frozen=True)
class ReviewBundle:
    review_dir: Path
    index_path: Path
    manifest_path: Path
    page_paths: tuple[Path, ...]
    generated_paths: tuple[Path, ...]
    model: str | None
    region: str | None
    lang: str | None
    reused_existing: bool = False


def resolve_docs_dir(cfg: dict) -> Path:
    paths_cfg_raw = cfg.get("paths", {})
    paths_cfg = paths_cfg_raw if isinstance(paths_cfg_raw, dict) else {}
    raw = paths_cfg.get("docs_dir")
    if isinstance(raw, str) and raw.strip():
        path = Path(raw.strip())
        return path if path.is_absolute() else (ROOT / path)
    return ROOT / "docs"

def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _copy_rst_tree(src_dir: Path, dst_dir: Path) -> list[Path]:
    copied: list[Path] = []
    if not src_dir.exists():
        return copied

    for src_file in sorted(path for path in src_dir.rglob("*.rst") if path.is_file()):
        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        copied.append(dst_file)
    return copied


def _write_overrides_readme(overrides_dir: Path) -> None:
    readme_path = overrides_dir / "README.md"
    readme_text = "\n".join(
        [
            "# Review Image Overrides",
            "",
            "Put replacement assets here using the same relative path as the public template asset.",
            "",
            "Example:",
            "- Default asset: `docs/templates/word_template/common_assets/overview/front_product.jpg`",
            f"- Review override: `{_repo_relative(overrides_dir / '_assets' / 'templates' / 'word_template' / 'common_assets' / 'overview' / 'front_product.jpg')}`",
            "",
            "When a matching file exists here, bundle generation will use this override instead of the default asset.",
            "",
        ]
    )
    readme_path.write_text(readme_text, encoding="utf-8")


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


def _collect_existing_rst_paths(review_dir: Path, relative_dir: str) -> tuple[Path, ...]:
    root_dir = review_dir / relative_dir
    if not root_dir.exists():
        return ()
    return tuple(sorted(path for path in root_dir.rglob("*.rst") if path.is_file()))


def _load_runtime_bundle_manifest(runtime_bundle_dir: Path) -> dict[str, object]:
    manifest_path = runtime_bundle_dir / "bundle_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _load_existing_review_bundle(
    review_dir: Path,
    *,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> ReviewBundle:
    return ReviewBundle(
        review_dir=review_dir,
        index_path=review_dir / "index.rst",
        manifest_path=review_dir / "manifest.json",
        page_paths=_collect_existing_rst_paths(review_dir, "page"),
        generated_paths=_collect_existing_rst_paths(review_dir, "generated"),
        model=model,
        region=region,
        lang=lang,
        reused_existing=True,
    )


def materialize_review_bundle(
    *,
    docs_dir: Path,
    docs_build_dir: Path | None = None,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    refresh_existing: bool = False,
) -> ReviewBundle:
    review_dir = review_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=lang)
    if review_dir.exists() and not refresh_existing:
        index_path = review_dir / "index.rst"
        page_dir = review_dir / "page"
        if not index_path.exists() or not page_dir.exists():
            raise RuntimeError(
                "Review bundle exists but is incomplete. "
                f"Re-run with --refresh-existing: {review_dir}"
            )
        return _load_existing_review_bundle(review_dir, model=model, region=region, lang=lang)

    if docs_build_dir is None:
        runtime_bundle_dir = bundle_dir_for_target(docs_dir=docs_dir, model=model, region=region, lang=lang)
    else:
        runtime_bundle_dir = build_root_for_target(model, region, lang, docs_build_dir=docs_build_dir) / "rst"
    index_src = runtime_bundle_dir / "index.rst"
    page_src = runtime_bundle_dir / "page"
    generated_src = runtime_bundle_dir / "generated"

    if not index_src.exists():
        raise RuntimeError(f"Runtime bundle index not found: {index_src}")
    if not page_src.exists():
        raise RuntimeError(f"Runtime bundle page directory not found: {page_src}")

    overrides_backup = review_dir.parent / f".{review_dir.name}.overrides.tmp"
    existing_overrides = review_dir / "overrides"
    if overrides_backup.exists():
        shutil.rmtree(overrides_backup)
    if existing_overrides.exists():
        shutil.copytree(existing_overrides, overrides_backup)
    if review_dir.exists():
        shutil.rmtree(review_dir)
    review_dir.mkdir(parents=True, exist_ok=True)

    index_dst = review_dir / "index.rst"
    shutil.copy2(index_src, index_dst)

    page_paths = _copy_rst_tree(page_src, review_dir / "page")
    generated_paths = _copy_rst_tree(generated_src, review_dir / "generated")
    overrides_dir = review_dir / "overrides"
    override_paths: list[Path] = []
    if overrides_backup.exists():
        shutil.move(str(overrides_backup), str(overrides_dir))
        override_paths = [path for path in overrides_dir.rglob("*") if path.is_file()]
    else:
        overrides_dir.mkdir(parents=True, exist_ok=True)
    _write_overrides_readme(overrides_dir)
    override_paths = [path for path in overrides_dir.rglob("*") if path.is_file()]
    manifest_path = review_dir / "manifest.json"

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": _read_git_sha(),
        "model": model,
        "region": region,
        "lang": lang,
        "runtime_bundle_dir": _repo_relative(runtime_bundle_dir),
        "review_dir": _repo_relative(review_dir),
        "index_path": _repo_relative(index_dst),
        "page_files": [_repo_relative(path) for path in page_paths],
        "generated_files": [_repo_relative(path) for path in generated_paths],
        "override_files": [_repo_relative(path) for path in override_paths],
    }
    runtime_bundle_manifest = _load_runtime_bundle_manifest(runtime_bundle_dir)
    if runtime_bundle_manifest:
        manifest["page_manifest"] = runtime_bundle_manifest.get("page_manifest")
        manifest["recipe_ids"] = runtime_bundle_manifest.get("recipe_ids", [])
        manifest["snippet_ids"] = runtime_bundle_manifest.get("snippet_ids", [])
        manifest["spec_master"] = runtime_bundle_manifest.get("spec_master", {})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return ReviewBundle(
        review_dir=review_dir,
        index_path=index_dst,
        manifest_path=manifest_path,
        page_paths=tuple(page_paths),
        generated_paths=tuple(generated_paths),
        model=model,
        region=region,
        lang=lang,
        reused_existing=False,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Create Git-friendly review bundles from prepared runtime bundles.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
    ap.add_argument("--lang", default=None, help="Optional language selector for multi-language configs")
    ap.add_argument("--all-targets", action="store_true", help="Use build.targets from config")
    ap.add_argument("--docs-build-dir", default=None, help="Override prepared docs/_build root")
    ap.add_argument(
        "--refresh-existing",
        action="store_true",
        help="Replace an existing review bundle with a fresh copy from the runtime bundle",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path

    try:
        cfg = load_config(cfg_path)
        docs_dir = resolve_docs_dir(cfg)
        docs_build_dir = None
        if isinstance(args.docs_build_dir, str) and args.docs_build_dir.strip():
            docs_build_dir = Path(args.docs_build_dir.strip())
            if not docs_build_dir.is_absolute():
                docs_build_dir = ROOT / docs_build_dir
        targets = resolve_build_targets(
            cfg,
            arg_model=args.model,
            arg_region=args.region,
            arg_lang=args.lang,
            all_targets=args.all_targets,
        )
        for target in targets:
            review_bundle = materialize_review_bundle(
                docs_dir=docs_dir,
                docs_build_dir=docs_build_dir,
                model=target.model,
                region=target.region,
                lang=target.lang,
                refresh_existing=args.refresh_existing,
            )
            action = "kept existing" if review_bundle.reused_existing else "seeded"
            print(
                "[review] bundle: "
                f"model='{target.model or ''}', region='{target.region or ''}', lang='{target.lang or ''}', "
                f"action='{action}', path='{review_bundle.review_dir}'"
            )
    except RuntimeError as exc:
        print(f"[review] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
