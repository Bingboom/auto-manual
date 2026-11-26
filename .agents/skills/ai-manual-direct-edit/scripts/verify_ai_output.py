#!/usr/bin/env python3
"""Verify Illustrator-edited PDF deliverables and render PNGs for visual QA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import fitz


def normalize_text(raw: str) -> str:
    """Normalize common PDF ligatures, curly apostrophes, and whitespace."""
    cleaned = (
        raw.replace("\ufb01", "fi")
        .replace("\ufb02", "fl")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u00a0", " ")
    )
    return " ".join(cleaned.split())


def has_illustrator_piece_info(doc: fitz.Document) -> bool:
    """Return True if page 1 or the PDF catalog retains native /Illustrator PieceInfo."""
    if len(doc) == 0:
        return False
    page_obj = doc.xref_object(doc[0].xref)
    if "/Illustrator" in page_obj:
        return True
    catalog = doc.xref_object(doc.pdf_catalog())
    return "/Illustrator" in catalog


def parse_page_selection(spec: str, page_count: int) -> list[int]:
    """Parse 1-based page selection like '1,4-6,15' into sorted unique 1-based indices."""
    selected: set[int] = set()
    for token in spec.split(","):
        part = token.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            if start < 1 or end > page_count or start > end:
                raise ValueError(f"Page range {part!r} out of bounds for {page_count} page(s)")
            selected.update(range(start, end + 1))
        else:
            page = int(part)
            if page < 1 or page > page_count:
                raise ValueError(f"Page {page} out of bounds for {page_count} page(s)")
            selected.add(page)
    return sorted(selected)


def verify_pdf(
    pdf_path: Path,
    qa_spec: dict[str, Any] | None = None,
    render_dir: Path | None = None,
    dpi: int = 150,
    pages_spec: str | None = None,
    require_illustrator: bool | None = None,
) -> dict[str, Any]:
    """Run metadata, stale-value, required-phrase, and optional PNG render checks."""
    spec = qa_spec or {}
    must_have_ai = (
        require_illustrator
        if require_illustrator is not None
        else bool(spec.get("require_illustrator", True))
    )

    doc = fitz.open(pdf_path)
    try:
        page_count = len(doc)
        creator = doc.metadata.get("creator") or ""
        ai_piece_info = has_illustrator_piece_info(doc)
        page_texts = [doc[i].get_text("text") for i in range(page_count)]
        norm_texts = [normalize_text(txt) for txt in page_texts]

        rendered_files: list[str] = []
        if render_dir is not None:
            render_dir.mkdir(parents=True, exist_ok=True)
            targets = (
                parse_page_selection(pages_spec, page_count)
                if pages_spec
                else list(range(1, page_count + 1))
            )
            for pno in targets:
                out_png = render_dir / f"p{pno:02d}.png"
                doc[pno - 1].get_pixmap(dpi=dpi).save(str(out_png))
                rendered_files.append(str(out_png))
    finally:
        doc.close()

    errors: list[str] = []
    expected_pages = spec.get("expected_pages")
    if expected_pages is not None and page_count != int(expected_pages):
        errors.append(f"Page count mismatch: expected {expected_pages}, got {page_count}")

    if must_have_ai and not ai_piece_info:
        errors.append("Missing native /PieceInfo /Illustrator data (PDF is not Illustrator-editable)")

    stale_hits: list[dict[str, Any]] = []
    for item in spec.get("stale_patterns", []):
        pattern = str(item["pattern"])
        desc = str(item.get("desc", ""))
        ignore_pages = {int(p) for p in item.get("ignore_pages", [])}
        norm_pat = normalize_text(pattern)
        for pno, raw_txt in enumerate(page_texts, start=1):
            if pno in ignore_pages:
                continue
            if pattern in raw_txt or (norm_pat and norm_pat in norm_texts[pno - 1]):
                stale_hits.append({"page": pno, "pattern": pattern, "desc": desc})

    missing_phrases: list[dict[str, Any]] = []
    must_exist_items = spec.get("must_exist", [])
    for item in must_exist_items:
        pno = int(item["page"])
        phrase = str(item["phrase"])
        if pno < 1 or pno > page_count:
            missing_phrases.append(
                {"page": pno, "phrase": phrase, "reason": f"page out of bounds (1..{page_count})"}
            )
            continue
        if normalize_text(phrase) not in norm_texts[pno - 1]:
            missing_phrases.append({"page": pno, "phrase": phrase, "reason": "not found"})

    ok = not errors and not stale_hits and not missing_phrases
    return {
        "ok": ok,
        "pdf": str(pdf_path),
        "pages": page_count,
        "creator": creator,
        "has_illustrator_piece_info": ai_piece_info,
        "errors": errors,
        "stale_hits": stale_hits,
        "missing_phrases": missing_phrases,
        "checked_phrases": len(must_exist_items),
        "rendered_files": rendered_files,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Illustrator-edited PDF deliverables and render pages for visual review."
    )
    parser.add_argument("--pdf", required=True, type=Path, help="Path to output PDF to verify.")
    parser.add_argument(
        "--spec",
        type=Path,
        default=None,
        help="Optional QA JSON spec with expected_pages, stale_patterns, must_exist.",
    )
    parser.add_argument(
        "--render-dir",
        type=Path,
        default=None,
        help="Optional output directory to render PNG pages for visual inspection.",
    )
    parser.add_argument("--dpi", type=int, default=150, help="PNG render DPI (default: 150).")
    parser.add_argument(
        "--pages",
        default=None,
        help="Optional 1-based page selection to render (e.g. '1,4-6,15'). Default: all pages.",
    )
    parser.add_argument(
        "--no-require-illustrator",
        action="store_true",
        help="Allow PDFs without /PieceInfo /Illustrator (e.g. non-AI test fixtures).",
    )
    parser.add_argument("--json", action="store_true", help="Print full machine-readable JSON result.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.pdf.is_file():
        print(f"ERROR: PDF not found: {args.pdf}", file=sys.stderr)
        return 2

    qa_spec: dict[str, Any] | None = None
    if args.spec is not None:
        if not args.spec.is_file():
            print(f"ERROR: QA spec not found: {args.spec}", file=sys.stderr)
            return 2
        qa_spec = json.loads(args.spec.read_text(encoding="utf-8"))

    require_ai = False if args.no_require_illustrator else None
    result = verify_pdf(
        pdf_path=args.pdf,
        qa_spec=qa_spec,
        render_dir=args.render_dir,
        dpi=args.dpi,
        pages_spec=args.pages,
        require_illustrator=require_ai,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"PDF: {result['pdf']}")
        print(f"Pages: {result['pages']}")
        print(f"Creator: {result['creator']}")
        print(f"Has PieceInfo /Illustrator: {result['has_illustrator_piece_info']}")
        if result["rendered_files"]:
            print(f"Rendered {len(result['rendered_files'])} page(s) to {args.render_dir}")
        for err in result["errors"]:
            print(f"  [ERROR] {err}")
        print("\n=== STALE VALUE QA ===")
        if result["stale_hits"]:
            for hit in result["stale_hits"]:
                print(f"  [STALE] P{hit['page']:02d}: {hit['pattern']!r} ({hit['desc']})")
        else:
            print("  PASS: 0 stale values!")
        print("\n=== COMPLETENESS QA ===")
        if result["missing_phrases"]:
            for miss in result["missing_phrases"]:
                print(f"  [MISSING] P{miss['page']:02d}: {miss['phrase']!r} ({miss['reason']})")
        else:
            print(f"  PASS: All {result['checked_phrases']} required phrase(s) verified intact!")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
