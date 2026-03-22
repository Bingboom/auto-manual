#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.config_pages import CoverPdfPage, CsvPage, PdfInsertPage, RstIncludePage  # noqa: E402
from tools.build_docs import load_config, resolve_build_targets  # noqa: E402
from tools.gen_index_bundle import bundle_dir_for_target, plan_materialized_pages  # noqa: E402
from tools.review_bundle import resolve_docs_dir  # noqa: E402
from tools.review_support import review_dir_for_target, sync_review_paths  # noqa: E402
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
        help="generated = spec/safety only; params = generated plus placeholder and cover pages",
    )
    ap.add_argument(
        "--page-file",
        action="append",
        default=[],
        help="Additional review page file name to sync from runtime/page, e.g. 02_whats_in_the_box.rst",
    )
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
    if scope not in {"generated", "params"}:
        raise RuntimeError(f"Unsupported sync scope: {scope}")

    relative_paths: set[Path] = set()
    planned_pages = plan_materialized_pages(cfg, model=model, region=region)
    generated_dir = runtime_bundle_dir / "generated"
    if generated_dir.exists():
        relative_paths.update(path.relative_to(runtime_bundle_dir) for path in generated_dir.rglob("*.rst") if path.is_file())

    for planned in planned_pages:
        page = planned.page
        page_relative = Path("page") / planned.file_name
        if isinstance(page, CsvPage):
            relative_paths.add(page_relative)
            continue
        if scope == "generated":
            continue
        if isinstance(page, CoverPdfPage):
            relative_paths.add(page_relative)
            continue
        if isinstance(page, PdfInsertPage):
            continue
        if isinstance(page, RstIncludePage):
            source_path = resolve_config_path(docs_dir, page.file, model, region)
            if _template_has_placeholders(source_path):
                relative_paths.add(page_relative)
            continue

    for file_name in page_files:
        relative_paths.add(Path("page") / file_name)

    return tuple(sorted(relative_paths))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path

    try:
        cfg = load_config(cfg_path)
        docs_dir = resolve_docs_dir(cfg)
        targets = resolve_build_targets(
            cfg,
            arg_model=args.model,
            arg_region=args.region,
            all_targets=args.all_targets,
        )
        for target in targets:
            runtime_bundle_dir = bundle_dir_for_target(
                docs_dir=docs_dir,
                model=target.model,
                region=target.region,
                lang=target.lang,
            )
            review_dir = review_dir_for_target(
                docs_dir=docs_dir,
                model=target.model,
                region=target.region,
                lang=target.lang,
            )
            relative_paths = resolve_sync_relative_paths(
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
                relative_paths=relative_paths,
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
