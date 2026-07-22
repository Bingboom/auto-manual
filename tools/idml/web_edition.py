"""Render the same-source print PDF into a page-card web edition.

Path: the LaTeX publish PDF is built from the *same* prepared bundle / manual
IR the IDML export consumes, through the repo's composition contract (the
``components_*.tex`` / ``page_*.py`` layout that replicates the approved
InDesign reference). That PDF — not a hand-rolled HTML layout — is the concrete
output of the layout contract, so this module presents it faithfully: each page
is rasterized to an image and stacked in a print-layout web reading flow, with
a visually-hidden per-page text layer so the document stays searchable and
screen-reader accessible, plus a link to download the original PDF.

The PDF is committed under ``reports/releases/<model>/<region>/web_edition/``
(built at publish time, where XeLaTeX is available); Read the Docs, which has no
TeX toolchain, only rasterizes and serves it.
"""
from __future__ import annotations

import html
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Rasterization zoom: 2x gives crisp text on HiDPI without oversized PNGs.
DEFAULT_RENDER_ZOOM = 2.0


@dataclass(frozen=True)
class WebEdition:
    out_dir: Path
    body_path: Path
    manifest_path: Path
    page_count: int
    asset_count: int
    pdf_name: str


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


_WEB_EDITION_CSS = """\
<style>
.we-doc { background:#4b4e54; border-radius:8px; padding:0 0 2.5rem; margin-top:1rem; }
.we-toolbar { position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; align-items:baseline;
  gap:.35rem .9rem; padding:.65rem 1rem; background:#33353a; color:#f5f5f5; border-radius:8px 8px 0 0; }
.we-toolbar .we-title { font-weight:600; }
.we-toolbar .we-meta { font-size:.8rem; color:#c8cacc; }
.we-toolbar .we-actions { margin-left:auto; font-size:.85rem; white-space:nowrap; }
.we-toolbar .we-actions a { color:#9ecbff; margin-left:.9rem; text-decoration:none; }
.we-toolbar .we-actions a:hover { text-decoration:underline; }
.we-sheet { max-width:min(52rem, calc(100% - 2rem)); margin:1.5rem auto 0; }
.we-page { position:relative; background:#fff; box-shadow:0 2px 14px rgba(0,0,0,.5); border-radius:2px; }
.we-page img { display:block; width:100%; height:auto; }
.we-page-text { position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden;
  clip:rect(0 0 0 0); white-space:nowrap; border:0; }
.we-page-num { text-align:center; color:rgba(255,255,255,.62); font-size:.78rem; margin-top:.45rem; }
@media (prefers-color-scheme: dark) { .we-doc { background:#2a2c30; } }
</style>"""

_META_FIELDS = (("version", "v{}"), ("built", "{}"), ("source", "{}"))


def _meta_line(provenance: dict, page_count: int) -> str:
    parts = []
    for key, fmt in _META_FIELDS:
        value = provenance.get(key)
        if value:
            parts.append(fmt.format(_esc(value)))
    parts.append(f"{page_count} pages")
    return " · ".join(parts)


def render_web_edition_from_pdf(
    pdf_path: Path,
    *,
    out_dir: Path,
    title: str,
    provenance: dict | None = None,
    zoom: float = DEFAULT_RENDER_ZOOM,
    log: Callable[[str], None] = print,
) -> WebEdition:
    """Rasterize ``pdf_path`` into a page-card web reading flow under ``out_dir``."""
    try:
        import fitz  # PyMuPDF, pinned in requirements.lock
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError(
            "PyMuPDF is required to render the web edition; install requirements.lock"
        ) from exc

    provenance = provenance or {}
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Keep the original PDF beside the rasters so the toolbar can offer it.
    pdf_copy = assets_dir / pdf_path.name
    shutil.copy2(pdf_path, pdf_copy)

    matrix = fitz.Matrix(zoom, zoom)
    cards: list[str] = []
    with fitz.open(pdf_path) as document:
        total = document.page_count
        for number, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            name = f"page_{number:03d}.png"
            pixmap.save(assets_dir / name)
            text = page.get_text().strip()
            text_layer = (
                f'<div class="we-page-text" aria-hidden="false">{_esc(text)}</div>' if text else ""
            )
            loading = "eager" if number == 1 else "lazy"
            cards.append(
                '<section class="we-sheet">'
                '<div class="we-page">'
                f'<img src="assets/{name}" alt="Page {number} of {total}" '
                f'width="{pixmap.width}" height="{pixmap.height}" loading="{loading}"/>'
                f"{text_layer}</div>"
                f'<div class="we-page-num">{number} / {total}</div>'
                "</section>"
            )

    toolbar = (
        '<div class="we-toolbar">'
        f'<span class="we-title">{_esc(title)}</span>'
        f'<span class="we-meta">{_meta_line(provenance, total)}</span>'
        '<span class="we-actions">'
        f'<a href="assets/{_esc(pdf_path.name)}" target="_blank" rel="noopener">Open PDF</a>'
        f'<a href="assets/{_esc(pdf_path.name)}" download>Download PDF</a>'
        "</span></div>"
    )
    body = _WEB_EDITION_CSS + f'\n<div class="we-doc">{toolbar}\n' + "\n".join(cards) + "\n</div>\n"
    body_path = out_dir / "body.html"
    body_path.write_text(body, encoding="utf-8")

    manifest = {
        "schema": "web-edition/v2",
        "title": title,
        "page_count": total,
        "asset_count": total,
        "pdf": pdf_path.name,
        "render_zoom": zoom,
        "provenance": provenance,
        "generator": "tools.idml.web_edition",
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    log(f"[web-edition] {title}: rasterized {total} page(s) from {pdf_path.name} -> {out_dir}")
    return WebEdition(
        out_dir=out_dir,
        body_path=body_path,
        manifest_path=manifest_path,
        page_count=total,
        asset_count=total,
        pdf_name=pdf_path.name,
    )
