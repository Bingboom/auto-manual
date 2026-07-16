#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.build_docs import BuildTarget, build_root_for_target, load_config, resolve_build_targets  # noqa: E402
from tools.asset_rewrites import restore_registry_asset_uris  # noqa: E402
from tools.gen_index_bundle import bundle_dir_for_target  # noqa: E402
from tools.review_support import review_dir_for_target  # noqa: E402
from tools.safe_copy import (  # noqa: E402
    assert_source_tree_no_symlinks,
    copy_regular_file_no_symlinks,
    copytree_replace_no_symlinks,
)
from tools.utils.path_utils import Paths  # noqa: E402


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
    return Paths(root=ROOT).docs_dir

def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _repo_relative_lexical(path: Path) -> str:
    candidate = Path(os.path.abspath(path))
    root = Path(os.path.abspath(ROOT))
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return candidate.as_posix()


def _copy_rst_tree(src_dir: Path, dst_dir: Path, *, label: str) -> list[Path]:
    copied: list[Path] = []
    if not src_dir.exists():
        return copied

    assert_source_tree_no_symlinks(src_dir, label=label)
    for src_file in sorted(path for path in src_dir.rglob("*.rst") if path.is_file()):
        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        copy_regular_file_no_symlinks(
            src_file,
            dst_file,
            source_root=src_dir,
            destination_root=dst_dir,
            label=label,
        )
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


def _replace_directory_atomically(staging_dir: Path, destination: Path) -> None:
    """Publish a sibling staging tree, restoring the previous tree on failure."""

    if destination.is_symlink():
        raise RuntimeError(f"Review bundle must not be a symbolic link: {destination}")
    if not destination.exists():
        os.replace(staging_dir, destination)
        return
    if not destination.is_dir():
        raise RuntimeError(f"Review bundle is not a directory: {destination}")

    previous = staging_dir.with_name(f"{staging_dir.name}.previous")
    try:
        os.replace(destination, previous)
        os.replace(staging_dir, destination)
    except BaseException:
        try:
            if previous.exists():
                if destination.exists():
                    if staging_dir.exists():
                        raise RuntimeError(
                            "Review refresh rollback found both staging and destination trees"
                        )
                    os.replace(destination, staging_dir)
                os.replace(previous, destination)
        except BaseException as rollback_error:
            raise RuntimeError(
                "Review refresh failed and automatic rollback failed; "
                f"the previous review is preserved at {previous}"
            ) from rollback_error
        raise
    try:
        shutil.rmtree(previous)
    except OSError:
        # The new review is already fully published.  Keeping the hidden
        # previous tree is safer than turning a cleanup issue into a false
        # refresh failure after the atomic swap succeeded.
        pass


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

    review_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{review_dir.name}.refresh-",
            dir=review_dir.parent,
        )
    )
    existing_overrides = review_dir / "overrides"
    try:
        index_staging = staging_dir / "index.rst"
        copy_regular_file_no_symlinks(
            index_src,
            index_staging,
            source_root=runtime_bundle_dir,
            destination_root=staging_dir,
            label="runtime review index",
        )

        staged_page_paths = _copy_rst_tree(
            page_src,
            staging_dir / "page",
            label="runtime review page source",
        )
        staged_generated_paths = _copy_rst_tree(
            generated_src,
            staging_dir / "generated",
            label="runtime review generated source",
        )
        restored_asset_references = restore_registry_asset_uris(
            source_bundle_dir=runtime_bundle_dir,
            target_bundle_dir=staging_dir,
            strict=True,
        )
        overrides_staging = staging_dir / "overrides"
        if existing_overrides.exists():
            if existing_overrides.is_symlink():
                raise RuntimeError(
                    f"Review overrides must not be a symbolic link: {existing_overrides}"
                )
            assert_source_tree_no_symlinks(
                existing_overrides,
                label="review overrides",
            )
            copytree_replace_no_symlinks(
                existing_overrides,
                overrides_staging,
                destination_root=staging_dir,
                label="review overrides",
            )
        else:
            overrides_staging.mkdir(parents=True, exist_ok=True)
        _write_overrides_readme(overrides_staging)
        staged_override_paths = [
            path for path in overrides_staging.rglob("*") if path.is_file()
        ]

        def published(path: Path) -> Path:
            return review_dir / path.relative_to(staging_dir)

        index_path = published(index_staging)
        page_paths = tuple(published(path) for path in staged_page_paths)
        generated_paths = tuple(published(path) for path in staged_generated_paths)
        override_paths = tuple(published(path) for path in staged_override_paths)
        manifest_path = review_dir / "manifest.json"
        manifest_staging = staging_dir / "manifest.json"

        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": _read_git_sha(),
            "model": model,
            "region": region,
            "lang": lang,
            "runtime_bundle_dir": _repo_relative(runtime_bundle_dir),
            "review_dir": _repo_relative_lexical(review_dir),
            "index_path": _repo_relative_lexical(index_path),
            "page_files": [_repo_relative_lexical(path) for path in page_paths],
            "generated_files": [
                _repo_relative_lexical(path) for path in generated_paths
            ],
            "override_files": [_repo_relative_lexical(path) for path in override_paths],
            "semantic_asset_references": restored_asset_references,
        }
        runtime_bundle_manifest = _load_runtime_bundle_manifest(runtime_bundle_dir)
        if runtime_bundle_manifest:
            manifest["page_manifest"] = runtime_bundle_manifest.get("page_manifest")
            manifest["recipe_ids"] = runtime_bundle_manifest.get("recipe_ids", [])
            manifest["snippet_ids"] = runtime_bundle_manifest.get("snippet_ids", [])
            manifest["spec_master"] = runtime_bundle_manifest.get("spec_master", {})
        manifest_staging.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        _replace_directory_atomically(staging_dir, review_dir)
        return ReviewBundle(
            review_dir=review_dir,
            index_path=index_path,
            manifest_path=manifest_path,
            page_paths=page_paths,
            generated_paths=generated_paths,
            model=model,
            region=region,
            lang=lang,
            reused_existing=False,
        )
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)


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
