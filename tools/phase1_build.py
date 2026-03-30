#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.phase1 import BuildPaths, BuildSelector, Phase1Builder  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser("phase1 builder")
    ap.add_argument("--model", default=None, help="comma-separated product models")
    ap.add_argument("--region", default=None, help="comma-separated regions")
    ap.add_argument("--page", default=None, help="comma-separated page ids")
    ap.add_argument("--lang", default=None, help="comma-separated langs")
    ap.add_argument(
        "--no-strict-renderer",
        action="store_true",
        help="skip page ids without registered renderers",
    )

    ap.add_argument("--page-registry", default="data/phase1/page_registry.csv")
    ap.add_argument("--template-dir", default="docs/templates")
    ap.add_argument("--out-dir", default="docs/generated")
    ap.add_argument(
        "--spec-master-csv",
        default="data/phase1/Spec_Master.csv",
        help="single source for spec page master rows",
    )
    ap.add_argument(
        "--spec-footnotes-csv",
        default="data/phase1/Spec_Footnotes.csv",
        help="optional source for spec page footnotes (pass empty to disable)",
    )
    ap.add_argument(
        "--spec-notes-csv",
        default="data/phase1/Spec_Notes.csv",
        help="optional source for spec page notes (pass empty to disable)",
    )
    ap.add_argument(
        "--spec-titles-csv",
        default="data/phase1/spec_titles.csv",
        help="optional source for spec page/section multilingual title overrides (pass empty to disable)",
    )
    return ap.parse_args()


def as_path(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (ROOT / p)


def as_optional_path(path_str: str | None) -> Path | None:
    raw = (path_str or "").strip()
    if not raw:
        return None
    return as_path(raw)


def main() -> None:
    args = parse_args()

    paths = BuildPaths(
        root=ROOT,
        page_registry=as_path(args.page_registry),
        template_dir=as_path(args.template_dir),
        output_dir=as_path(args.out_dir),
        spec_master_csv=as_path(args.spec_master_csv),
        spec_footnotes_csv=as_optional_path(args.spec_footnotes_csv),
        spec_notes_csv=as_optional_path(args.spec_notes_csv),
        spec_titles_csv=as_optional_path(args.spec_titles_csv),
    )

    selector = BuildSelector.from_args(
        models=args.model,
        regions=args.region,
        pages=args.page,
        langs=args.lang,
    )
    result = Phase1Builder(paths).build(selector, strict_renderer=not args.no_strict_renderer)

    for out_path in result.written_files:
        print(f"[phase1_build] Wrote: {out_path}")
    for reason in result.skipped_pages:
        print(f"[phase1_build] Skipped: {reason}")

    print(
        f"[phase1_build] Done. files={result.write_count}, "
        f"skipped={len(result.skipped_pages)}"
    )


if __name__ == "__main__":
    main()
