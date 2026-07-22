#!/usr/bin/env python3
"""Render the committed same-source print PDF into a page-card web edition.

The layout contract's concrete output is the LaTeX publish PDF (built at
publish time from the same bundle the IDML export uses, through the repo's
composition contract). It is committed under
``reports/releases/<model>/<region>/web_edition/<name>.pdf`` (+ optional
``<name>.json`` provenance sidecar). This CLI finds it and rasterizes it into a
``webedition/`` directory that ``tools/readthedocs_source.py`` grafts into the
RTD catalog as the primary entry.

Best-effort: if no committed PDF is found it logs and exits 0, so the RTD build
stays green and the catalog keeps the HTML-only entry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.idml.web_edition import render_web_edition_from_pdf  # noqa: E402
from tools.utils.path_utils import releases_of, repo_root  # noqa: E402

_WEB_EDITION_SEGMENT = "web_edition"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--out", required=True, type=Path, help="Output webedition/ directory")
    parser.add_argument(
        "--releases-root",
        default=None,
        type=Path,
        help="Root holding <model>/<region>/web_edition/*.pdf (default: reports/releases)",
    )
    parser.add_argument("--title", default=None, help="Manual title (default: from sidecar or model/region)")
    parser.add_argument(
        "--keep-cover",
        action="store_true",
        help="Include the print cover page (page 1); by default the web edition omits it",
    )
    parser.add_argument(
        "--skip-pages",
        default=None,
        help="Comma-separated 1-based page numbers to omit (overrides the default cover skip and any sidecar skip_pages)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail (exit 1) instead of skipping when no committed PDF is found",
    )
    return parser.parse_args(argv)


def _resolve_skip_pages(args: argparse.Namespace, sidecar: dict) -> frozenset[int]:
    if args.skip_pages is not None:
        return frozenset(int(p) for p in args.skip_pages.split(",") if p.strip())
    sidecar_skip = sidecar.get("skip_pages")
    if isinstance(sidecar_skip, list):
        return frozenset(int(p) for p in sidecar_skip)
    # Default: a web catalog entry does not need the print cover (page 1).
    return frozenset() if args.keep_cover else frozenset({1})


def _find_pdf(web_edition_dir: Path) -> Path | None:
    if not web_edition_dir.is_dir():
        return None
    pdfs = sorted(path for path in web_edition_dir.glob("*.pdf") if path.is_file())
    if not pdfs:
        return None
    if len(pdfs) > 1:
        print(f"[web-edition] warning: multiple PDFs under {web_edition_dir}; using {pdfs[0].name}")
    return pdfs[0]


def _load_sidecar(pdf_path: Path) -> dict:
    sidecar = pdf_path.with_suffix(".json")
    if not sidecar.is_file():
        return {}
    try:
        loaded = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(f"[web-edition] warning: unreadable sidecar {sidecar.name}; ignoring")
        return {}
    return loaded if isinstance(loaded, dict) else {}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = repo_root()
    releases_root = args.releases_root or releases_of(root)
    web_edition_dir = releases_root / args.model / args.region / _WEB_EDITION_SEGMENT

    pdf_path = _find_pdf(web_edition_dir)
    if pdf_path is None:
        message = f"[web-edition] skipped {args.model}/{args.region}: no committed PDF under {web_edition_dir}"
        if args.strict:
            print(message, file=sys.stderr)
            return 1
        print(message)
        return 0

    sidecar = _load_sidecar(pdf_path)
    title = args.title or sidecar.get("title") or f"{args.model} / {args.region}"
    provenance = sidecar.get("provenance") if isinstance(sidecar.get("provenance"), dict) else {}
    skip_pages = _resolve_skip_pages(args, sidecar)

    render_web_edition_from_pdf(
        pdf_path, out_dir=args.out, title=title, provenance=provenance, skip_pages=skip_pages
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
