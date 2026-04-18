#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

from tools.config_pages import CoverPdfPage, CsvPage, PdfInsertPage, RstIncludePage  # noqa: E402
from tools.build_docs import build_root_for_target, load_config, resolve_build_targets  # noqa: E402
from tools.gen_index_bundle import bundle_dir_for_target, plan_materialized_pages  # noqa: E402
from tools.review_bundle import resolve_docs_dir  # noqa: E402
from tools.review_support import (  # noqa: E402
    SyncPlanEntry,
    resolve_existing_review_bundle_dir,
    review_dir_for_target,
    sync_review_paths,
)
from tools.word_bundle_common import resolve_config_path  # noqa: E402

PLACEHOLDER_RE = re.compile(r"\|([A-Z0-9][A-Z0-9_]+)\|")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Sync parameter-driven runtime files into an existing review bundle.")
    ap.add_argument("--config", required=True, help="Config YAML path")
    ap.add_argument("--model", default=None, help="Single target model override")
    ap.add_argument("--region", default=None, help="Single target region override")
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
    scope: str,
    page_files: tuple[str, ...],
) -> tuple[SyncPlanEntry, ...]:
    if scope not in {"generated", "params"}:
        raise RuntimeError(f"Unsupported sync scope: {scope}")

    sync_plan: dict[Path, SyncPlanEntry] = {}
    planned_pages = plan_materialized_pages(cfg, model=model, region=region)
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
            review_dir = resolve_existing_review_bundle_dir(
                docs_dir=docs_dir,
                model=target.model,
                region=target.region,
                lang=target.lang,
            )
            if review_dir is None:
                review_dir = review_dir_for_target(
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
                scope=args.sync_scope,
                page_files=tuple(args.page_file),
            )
            copied = sync_review_paths(
                runtime_bundle_dir=runtime_bundle_dir,
                review_dir=review_dir,
                scope=args.sync_scope,
                plan=sync_plan,
            )
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
