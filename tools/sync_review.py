#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.asset_rewrites import restore_registry_asset_uris  # noqa: E402
from tools.config_pages import CoverPdfPage, CsvPage, GeneratedPage, PdfInsertPage, RstIncludePage  # noqa: E402
from tools.build_docs import build_root_for_target, load_config, resolve_build_targets  # noqa: E402
from tools.gen_index_bundle import bundle_dir_for_target, plan_materialized_pages  # noqa: E402
from tools.review_bundle import resolve_docs_dir  # noqa: E402
from tools.review_support import (  # noqa: E402
    SyncPlanEntry,
    resolve_existing_review_bundle_dir,
    resolve_review_page_path_map,
    review_dir_for_target,
    sync_review_paths,
)
from tools.safe_copy import assert_source_tree_no_symlinks  # noqa: E402
from tools.utils.path_utils import PathSegments  # noqa: E402
from tools.word_bundle_common import resolve_config_path  # noqa: E402

PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")
WEB_LANGUAGE_PROJECTION_SCHEMA = "web-language-bundle/v1"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sync parameter-driven runtime files into an existing review bundle.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
    ap.add_argument("--lang", default=None, help="Optional language selector for multi-language configs")
    ap.add_argument("--all-targets", action="store_true", help="Use build.targets from config")
    ap.add_argument(
        "--sync-scope",
        choices=("generated", "params"),
        default="params",
        help="generated = generated csv/draft pages only; params = generated plus parameter-driven page refresh without resetting manual review prose",
    )
    ap.add_argument(
        "--page-file",
        action="append",
        default=[],
        help="Additional review page file name to sync from runtime/page, e.g. 02_whats_in_the_box.rst",
    )
    ap.add_argument("--docs-build-dir", default=None, help="Override prepared docs/_build root")
    return ap.parse_args(argv)


def _template_has_placeholders(source_path: Path) -> bool:
    if not source_path.exists() or not source_path.is_file():
        return False
    return bool(PLACEHOLDER_RE.search(source_path.read_text(encoding="utf-8")))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _projection_source_rows(payload: dict[str, object], *, manifest_path: Path) -> tuple[tuple[Path, str], ...]:
    raw_rows = payload.get("source_pages")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise RuntimeError(
            f"Web language projection has invalid source_pages: {manifest_path}"
        )
    rows: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            raise RuntimeError(
                f"Web language projection has invalid source_pages row: {manifest_path}"
            )
        raw_path = raw_row.get("path")
        expected_sha256 = raw_row.get("sha256")
        relative = Path(raw_path) if isinstance(raw_path, str) else Path()
        if (
            not isinstance(raw_path, str)
            or not raw_path
            or relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() != raw_path
            or raw_path in seen
            or not isinstance(expected_sha256, str)
            or not _SHA256_RE.fullmatch(expected_sha256)
        ):
            raise RuntimeError(
                f"Web language projection has invalid source_pages row: {manifest_path}"
            )
        seen.add(raw_path)
        rows.append((relative, expected_sha256))
    return tuple(rows)


def resolve_runtime_bundle_for_sync(runtime_bundle_dir: Path) -> Path:
    """Return the full runtime bundle behind a canonical Web projection."""

    projection_manifest = runtime_bundle_dir / "bundle_manifest.json"
    if runtime_bundle_dir.is_symlink() or projection_manifest.is_symlink():
        raise RuntimeError(
            f"Web language projection sync path must not use a symbolic link: {runtime_bundle_dir}"
        )
    if not projection_manifest.exists():
        return runtime_bundle_dir
    try:
        payload = json.loads(projection_manifest.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return runtime_bundle_dir
    if not isinstance(payload, dict) or payload.get("schema_version") != WEB_LANGUAGE_PROJECTION_SCHEMA:
        return runtime_bundle_dir

    build_root = runtime_bundle_dir.parent
    source_bundle = (
        build_root
        / PathSegments.WEB
        / PathSegments.SOURCE
        / PathSegments.RST
    )
    for directory in (
        build_root,
        build_root / PathSegments.WEB,
        build_root / PathSegments.WEB / PathSegments.SOURCE,
        source_bundle,
    ):
        if directory.is_symlink():
            raise RuntimeError(
                f"Web language projection source path must not use a symbolic link: {directory}"
            )
    if not source_bundle.is_dir():
        raise RuntimeError(
            f"Web language projection full source bundle is missing: {source_bundle}"
        )
    assert_source_tree_no_symlinks(
        source_bundle, label="Web language projection full source bundle"
    )

    expected_index_sha256 = payload.get("source_index_sha256")
    if not isinstance(expected_index_sha256, str) or not _SHA256_RE.fullmatch(
        expected_index_sha256
    ):
        raise RuntimeError(
            f"Web language projection has invalid source_index_sha256: {projection_manifest}"
        )
    source_index = source_bundle / "index.rst"
    if not source_index.is_file() or _sha256(source_index) != expected_index_sha256:
        raise RuntimeError(
            f"Web language projection full source index hash mismatch: {source_index}"
        )
    for relative, expected_sha256 in _projection_source_rows(
        payload, manifest_path=projection_manifest
    ):
        source_page = source_bundle / relative
        if not source_page.is_file() or _sha256(source_page) != expected_sha256:
            raise RuntimeError(
                f"Web language projection full source page hash mismatch: {source_page}"
            )
    return source_bundle


def resolve_sync_relative_paths(
    *,
    cfg: dict,
    docs_dir: Path,
    runtime_bundle_dir: Path,
    model: str | None,
    region: str | None,
    scope: str,
    page_files: tuple[str, ...],
) -> tuple[Path, ...]:
    sync_plan = resolve_sync_plan(
        cfg=cfg,
        docs_dir=docs_dir,
        runtime_bundle_dir=runtime_bundle_dir,
        model=model,
        region=region,
        scope=scope,
        page_files=page_files,
    )
    return tuple(entry.relative_path for entry in sync_plan)


def resolve_sync_plan(
    *,
    cfg: dict,
    docs_dir: Path,
    runtime_bundle_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None = None,
    scope: str,
    page_files: tuple[str, ...],
) -> tuple[SyncPlanEntry, ...]:
    if scope not in {"generated", "params"}:
        raise RuntimeError(f"Unsupported sync scope: {scope}")

    sync_plan: dict[Path, SyncPlanEntry] = {}
    planned_pages = plan_materialized_pages(
        cfg,
        model=model,
        region=region,
        langs=[lang] if (lang or "").strip() else None,
    )
    generated_dir = runtime_bundle_dir / "generated"
    if generated_dir.exists():
        for path in generated_dir.rglob("*.rst"):
            if not path.is_file():
                continue
            relative_path = path.relative_to(runtime_bundle_dir)
            sync_plan[relative_path] = SyncPlanEntry(relative_path=relative_path)

    for planned in planned_pages:
        page = planned.page
        page_relative = Path("page") / planned.file_name
        if isinstance(page, CsvPage):
            sync_plan[page_relative] = SyncPlanEntry(relative_path=page_relative)
            continue
        if scope == "generated":
            continue
        if isinstance(page, CoverPdfPage):
            sync_plan[page_relative] = SyncPlanEntry(relative_path=page_relative)
            continue
        if isinstance(page, PdfInsertPage):
            continue
        if isinstance(page, GeneratedPage):
            source_path = resolve_config_path(docs_dir, page.template, model, region)
            if _template_has_placeholders(source_path):
                sync_plan[page_relative] = SyncPlanEntry(
                    relative_path=page_relative,
                    mode="merge_params",
                    template_path=source_path,
                )
            continue
        if isinstance(page, RstIncludePage):
            source_path = resolve_config_path(docs_dir, page.file, model, region)
            if _template_has_placeholders(source_path):
                sync_plan[page_relative] = SyncPlanEntry(
                    relative_path=page_relative,
                    mode="merge_params",
                    template_path=source_path,
                )
            continue

    for file_name in page_files:
        relative_path = Path("page") / file_name
        sync_plan[relative_path] = SyncPlanEntry(relative_path=relative_path)

    return tuple(sync_plan[path] for path in sorted(sync_plan))


def resolve_review_dir_for_sync(
    *,
    docs_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None = None,
) -> Path:
    review_dir = resolve_existing_review_bundle_dir(
        docs_dir=docs_dir,
        model=model,
        region=region,
        lang=lang,
    )
    if review_dir is not None:
        return review_dir
    return review_dir_for_target(
        docs_dir=docs_dir,
        model=model,
        region=region,
        lang=lang,
    )


def remap_sync_plan_for_review_dir(
    sync_plan: tuple[SyncPlanEntry, ...],
    *,
    docs_dir: Path,
    review_dir: Path,
    model: str | None,
    region: str | None,
    lang: str | None,
) -> tuple[SyncPlanEntry, ...]:
    normalized_lang = (lang or "").strip().lower()
    if not normalized_lang:
        return sync_plan

    shared_review_dir = review_dir_for_target(
        docs_dir=docs_dir,
        model=model,
        region=region,
    )
    if review_dir != shared_review_dir:
        return sync_plan

    page_path_map = resolve_review_page_path_map(
        review_dir=review_dir,
        model=model,
        region=region,
        target_lang=normalized_lang,
    )
    if not page_path_map:
        return sync_plan

    remapped_plan: list[SyncPlanEntry] = []
    for entry in sync_plan:
        destination_relative_path = entry.relative_path
        if destination_relative_path.parts and destination_relative_path.parts[0] == "page":
            mapped_relative_path = page_path_map.get(destination_relative_path)
            if mapped_relative_path is None:
                # Shared family review bundles can intentionally omit language-only
                # pages such as localized prefaces. Leave those runtime pages in place
                # instead of aborting the whole sync.
                continue
            destination_relative_path = mapped_relative_path
        remapped_plan.append(
            SyncPlanEntry(
                relative_path=destination_relative_path,
                mode=entry.mode,
                template_path=entry.template_path,
                source_relative_path=entry.relative_path,
            )
        )
    return tuple(remapped_plan)


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
            if docs_build_dir is None:
                runtime_bundle_dir = bundle_dir_for_target(
                    docs_dir=docs_dir,
                    model=target.model,
                    region=target.region,
                    lang=target.lang,
                )
            else:
                runtime_bundle_dir = build_root_for_target(
                    target.model,
                    target.region,
                    target.lang,
                    docs_build_dir=docs_build_dir,
                ) / "rst"
            runtime_bundle_dir = resolve_runtime_bundle_for_sync(runtime_bundle_dir)
            review_dir = resolve_review_dir_for_sync(
                docs_dir=docs_dir,
                model=target.model,
                region=target.region,
                lang=target.lang,
            )
            sync_plan = resolve_sync_plan(
                cfg=cfg,
                docs_dir=docs_dir,
                runtime_bundle_dir=runtime_bundle_dir,
                model=target.model,
                region=target.region,
                lang=target.lang,
                scope=args.sync_scope,
                page_files=tuple(args.page_file),
            )
            sync_plan = remap_sync_plan_for_review_dir(
                sync_plan,
                docs_dir=docs_dir,
                review_dir=review_dir,
                model=target.model,
                region=target.region,
                lang=target.lang,
            )
            copied = sync_review_paths(
                runtime_bundle_dir=runtime_bundle_dir,
                review_dir=review_dir,
                scope=args.sync_scope,
                plan=sync_plan,
            )
            # The runtime bundle is finalized, so its RST carries staged file
            # paths; copying them verbatim would launder every semantic
            # `asset:` reference in docs/_review back into a bare path (the
            # seeding path in review_bundle.py already restores them — this
            # kept parity). Non-strict: sync copies a planned subset, and
            # reviewer-edited lines that no longer match provenance stay put.
            restored = restore_registry_asset_uris(
                source_bundle_dir=runtime_bundle_dir,
                target_bundle_dir=review_dir,
                strict=False,
            )
            if restored:
                print(f"[sync-review] restored {restored} semantic asset reference(s)")
            print(
                "[sync-review] bundle: "
                f"model='{target.model or ''}', region='{target.region or ''}', lang='{target.lang or ''}', "
                f"scope='{args.sync_scope}', files='{len(copied)}', path='{review_dir}'"
            )
    except RuntimeError as exc:
        print(f"[sync-review] ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
