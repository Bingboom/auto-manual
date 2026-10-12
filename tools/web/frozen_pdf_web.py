"""Re-import native PDF copy into the existing shared Web IR pipeline.

Artwork must be fully resolved and hash-pinned before building a candidate.
This command never reads historical screenshot assets or publishes output.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from tools.web.frozen_ai_web import assemble_book
from tools.web.frozen_pdf_document import ordered_pages
from tools.web.frozen_pdf_source import PdfBook


def build_pdf_book(pdf_path: Path, recipe_root: Path, assets_manifest: Path,
                   output: Path, language: str):
    if output.exists():
        raise ValueError(f'output already exists; use a new candidate directory: {output}')
    if output.resolve().is_relative_to(recipe_root.resolve()):
        raise ValueError('output must not be inside the historical source')
    book = PdfBook(pdf_path, recipe_root, assets_manifest, output, language)
    title, pages = ordered_pages(book)
    return assemble_book(book, title, pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path, required=True)
    parser.add_argument('--recipe-root', type=Path, required=True)
    parser.add_argument('--assets-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--language', required=True)
    args = parser.parse_args()
    ir = build_pdf_book(args.pdf, args.recipe_root, args.assets_manifest, args.output, args.language)
    print(f'{ir.model}/{ir.region}/{ir.language}: {len(ir.pages)} chapters')


if __name__ == '__main__':
    main()
