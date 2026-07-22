"""Render the IDML same-source IR into a print-layout web edition.

This is a second, HTML-emitting backend over the *same* ``manual-ir/v1`` that
feeds the IDML export (``tools/idml/ir_projection.py``): both consume the IR
projected from the prepared bundle by ``build_same_source_ir``. The IDML/PDF
edition is the pixel-authoritative print artifact (InDesign owns the final
line-level geometry); this edition presents the same source content as a
page-card web document — one card per IR page, blocks flowed in reading order,
images resolved from the bundle. Text reflows with web fallback fonts, so line
breaks intentionally diverge from the InDesign layout; the shared truth is the
content and page sequence, not per-line typography.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools.attachment_identity import resolve_semantic_attachment
from tools.manual_ir import ManualIR, ManualPage

# US Letter in points; a sane default page box. The web card constrains width
# to this aspect ratio and grows in height when reflowed content needs it.
DEFAULT_PAGE_SIZE_PT = (612.0, 792.0)
_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class WebEdition:
    out_dir: Path
    body_path: Path
    manifest_path: Path
    page_count: int
    asset_count: int
    unresolved_assets: tuple[str, ...]


# --------------------------------------------------------------------------
# asset resolution + staging
# --------------------------------------------------------------------------
class _AssetStager:
    """Resolve IR asset references to files and copy them into ``assets/``.

    Regular ``image`` block payloads are bundle-relative paths; component and
    data figures are bare attachment basenames resolved semantically. PDF
    sources (placed cover / overview art) are rasterized to PNG.
    """

    def __init__(self, *, bundle_root: Path, data_root: Path, assets_dir: Path) -> None:
        self._bundle_root = bundle_root
        self._data_root = data_root
        self._assets_dir = assets_dir
        self._by_source: dict[Path, str] = {}
        self._unresolved: set[str] = set()
        self._attachment_categories: tuple[str, ...] = self._scan_categories(data_root)

    @staticmethod
    def _scan_categories(data_root: Path) -> tuple[str, ...]:
        attachments = data_root / "_attachments"
        if not attachments.is_dir():
            return ()
        return tuple(sorted(p.name for p in attachments.iterdir() if p.is_dir()))

    @property
    def unresolved(self) -> tuple[str, ...]:
        return tuple(sorted(self._unresolved))

    @property
    def count(self) -> int:
        return len(self._by_source)

    def _resolve(self, reference: str, *, category: str | None) -> Path | None:
        ref = (reference or "").strip()
        if not ref:
            return None
        path = Path(ref)
        if path.is_absolute() and path.exists():
            return path
        candidates = [
            self._bundle_root / ref,
            self._bundle_root / "renderers" / "latex" / "assets" / path.name,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        ordered = ([category] if category else []) + [
            name for name in self._attachment_categories if name != category
        ]
        for name in ordered:
            found = resolve_semantic_attachment(self._data_root / "_attachments" / name, path.name)
            if found is not None:
                return found
        return None

    def stage(self, reference: str, *, category: str | None = None) -> str | None:
        """Return the ``assets/<name>`` href for a reference, or None if unresolved."""
        source = self._resolve(reference, category=category)
        if source is None:
            self._unresolved.add(reference)
            return None
        source = source.resolve(strict=False)
        cached = self._by_source.get(source)
        if cached is not None:
            return cached
        self._assets_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:8]
        stem = _SLUG_RE.sub("-", source.stem.lower()).strip("-") or "asset"
        if source.suffix.lower() == ".pdf":
            name = f"{stem}-{digest}.png"
            target = self._assets_dir / name
            if not self._rasterize_pdf(source, target):
                self._unresolved.add(reference)
                return None
        else:
            name = f"{stem}-{digest}{source.suffix.lower()}"
            target = self._assets_dir / name
            if not target.exists():
                shutil.copy2(source, target)
        href = f"assets/{name}"
        self._by_source[source] = href
        return href

    @staticmethod
    def _rasterize_pdf(source: Path, target: Path) -> bool:
        if target.exists():
            return True
        try:
            import fitz  # PyMuPDF, pinned in requirements.lock
        except ImportError:  # pragma: no cover - environment guard
            return False
        try:
            with fitz.open(source) as document:
                if document.page_count == 0:
                    return False
                pixmap = document[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
                pixmap.save(target)
        except Exception:  # pragma: no cover - corrupt art is skipped, not fatal
            return False
        return True


# --------------------------------------------------------------------------
# block -> HTML
# --------------------------------------------------------------------------
def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)")
_IMAGE_DIRECTIVE_RE = re.compile(r"^\.\.\s+image::\s*(\S+)")


def _inline(text: str) -> str:
    """Escape text and re-enable the small RST inline set the IR carries."""
    escaped = _esc(text)
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC_RE.sub(r"<em>\1</em>", escaped)
    return escaped


def _is_noise(text: str) -> bool:
    """RST line-block artifacts (a bare ``|``) and blanks carry no content."""
    stripped = str(text).strip()
    return stripped in ("", "|")


def _paragraphs(text: str) -> str:
    chunks = [chunk.strip() for chunk in str(text).split("\n\n")]
    out = []
    for chunk in chunks:
        if _is_noise(chunk):
            continue
        lines = [line for line in chunk.split("\n") if not _is_noise(line)]
        if not lines:
            continue
        out.append("<p>" + "<br/>".join(_inline(line) for line in lines) + "</p>")
    return "".join(out)


def _list_item_text(payload: str) -> str:
    text = str(payload).lstrip()
    for bullet in ("• ", "• ", "- ", "* "):
        if text.startswith(bullet):
            return text[len(bullet):]
    return text


def _img(href: str | None, *, cls: str, alt: str = "") -> str:
    if not href:
        return f'<div class="we-img-missing">[missing image: {_esc(alt)}]</div>'
    return f'<img class="{cls}" src="{_esc(href)}" alt="{_esc(alt)}" loading="lazy"/>'


def _table(rows: list, *, header: bool = True, cell: Callable[[Any], str] = _inline) -> str:
    if not rows:
        return ""
    parts = ["<table class=\"we-table\">"]
    body_rows = list(rows)
    if header:
        head = body_rows[0]
        parts.append("<thead><tr>" + "".join(f"<th>{cell(c)}</th>" for c in head) + "</tr></thead>")
        body_rows = body_rows[1:]
    parts.append("<tbody>")
    for row in body_rows:
        parts.append("<tr>" + "".join(f"<td>{cell(c)}</td>" for c in row) + "</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


class _PageRenderer:
    def __init__(self, stager: _AssetStager) -> None:
        self._stager = stager

    def render(self, page: ManualPage) -> str:
        html_parts: list[str] = []
        list_buffer: list[str] = []
        col_open = False

        def flush_list() -> None:
            if list_buffer:
                html_parts.append("<ul class=\"we-list\">" + "".join(list_buffer) + "</ul>")
                list_buffer.clear()

        for block in page.blocks:
            kind = block.kind
            payload = block.payload
            if kind in ("list", "sublist"):
                cls = "we-sublist-item" if kind == "sublist" else ""
                list_buffer.append(f'<li class="{cls}">{_esc(_list_item_text(payload))}</li>')
                continue
            flush_list()
            if kind == "layout":
                if payload == "twocol_start" and not col_open:
                    html_parts.append('<div class="we-twocol">')
                    col_open = True
                elif payload == "twocol_end" and col_open:
                    html_parts.append("</div>")
                    col_open = False
                continue
            html_parts.append(self._render_block(kind, payload))
        flush_list()
        if col_open:
            html_parts.append("</div>")
        return "".join(part for part in html_parts if part)

    def _render_block(self, kind: str, payload: Any) -> str:
        if kind in ("h1", "h2", "h3"):
            return f'<{kind} class="we-{kind}">{_esc(payload)}</{kind}>'
        if kind == "body":
            return f'<div class="we-body">{_paragraphs(payload)}</div>'
        if kind == "safetylead":
            return f'<p class="we-safetylead">{_esc(payload)}</p>'
        if kind == "image":
            href = self._stager.stage(str(payload))
            return f'<figure class="we-figure">{_img(href, cls="we-image", alt=str(payload))}</figure>'
        if kind == "table" and isinstance(payload, list):
            return _table(payload, cell=self._cell)
        if kind == "component" and isinstance(payload, dict):
            return self._render_component(payload)
        if kind == "data" and isinstance(payload, dict):
            return self._render_data(payload)
        if isinstance(payload, str):
            return f'<div class="we-body">{_paragraphs(payload)}</div>'
        return ""

    def _cell(self, value: Any) -> str:
        """Render a table cell: embedded ``.. image::`` directives become images."""
        text = str(value)
        match = _IMAGE_DIRECTIVE_RE.match(text.strip())
        if match:
            href = self._stager.stage(match.group(1))
            return _img(href, cls="we-cell-img", alt=match.group(1))
        return _inline(text)

    def _texts(self, payload: dict) -> str:
        return "".join(_paragraphs(t) for t in payload.get("texts", []))

    def _render_component(self, payload: dict) -> str:
        kind = payload.get("kind")
        if kind == "langtag":
            lang = _esc(payload.get("lang", ""))
            texts = "".join(f"<span>{_esc(t)}</span>" for t in payload.get("texts", []))
            return f'<div class="we-langtag"><span class="we-lang">{lang}</span>{texts}</div>'
        if kind in ("warninglead", "warnbox", "notice"):
            label = _esc(payload.get("label", kind.upper()))
            return (
                f'<div class="we-callout we-{_esc(kind)}"><span class="we-callout-label">{label}</span>'
                f'<div class="we-callout-body">{self._texts(payload)}</div></div>'
            )
        if kind in ("safetyinstruction", "safetywarning", "fcc"):
            return f'<div class="we-callout we-{_esc(kind)}"><div class="we-callout-body">{self._texts(payload)}</div></div>'
        if kind == "inbox":
            cells = []
            for item in payload.get("items", []):
                href = self._stager.stage(str(item.get("img", "")))
                cells.append(
                    f'<figure class="we-inbox-item">{_img(href, cls="we-inbox-img", alt=str(item.get("label", "")))}'
                    f'<figcaption>{_esc(item.get("label", ""))}</figcaption></figure>'
                )
            return f'<div class="we-inbox">{"".join(cells)}</div>'
        if kind == "lcdmode":
            href = self._stager.stage(str(payload.get("img", "")))
            groups = []
            for group in payload.get("groups", []):
                table = _table(
                    [["Action", "Detail"]] + [list(action) for action in group.get("actions", [])]
                )
                groups.append(
                    f'<div class="we-lcdmode-group"><div class="we-lcdmode-state">{_esc(group.get("state", ""))}</div>'
                    f"{table}</div>"
                )
            fig = f'<figure class="we-figure">{_img(href, cls="we-image", alt="LCD mode")}</figure>' if href else ""
            return f'<div class="we-lcdmode">{fig}{"".join(groups)}</div>'
        # unknown component: render any text faithfully
        return f'<div class="we-body">{self._texts(payload)}</div>'

    def _render_data(self, payload: dict) -> str:
        kind = payload.get("kind")
        if kind == "placed_pdf":
            href = self._stager.stage(str(payload.get("asset", "")))
            return f'<div class="we-placed">{_img(href, cls="we-placed-img", alt=str(payload.get("asset", "")))}</div>'
        if kind == "spec_start":
            return f'<h1 class="we-h1">{_esc(payload.get("title", "SPECIFICATIONS"))}</h1>'
        if kind == "spec_section":
            return _table(payload.get("rows", []), header=False)
        if kind == "spec_annotations":
            return f'<div class="we-annotations">{self._texts(payload)}</div>'
        if kind == "toc":
            return self._render_toc(payload)
        if kind in ("symbol_signals", "symbol_icons"):
            return self._render_symbol_rows(payload)
        if kind == "lcd_icons":
            return self._render_lcd_rows(payload)
        if kind == "back_cover":
            return self._render_back_cover(payload)
        return ""

    def _render_toc(self, payload: dict) -> str:
        blocks = []
        for lang in payload.get("languages", []):
            items = "".join(
                f'<li><span class="we-toc-folio">{_esc(e.get("folio", ""))}</span>'
                f'<span class="we-toc-title">{_esc(e.get("title", ""))}</span></li>'
                for e in lang.get("entries", [])
            )
            blocks.append(
                f'<div class="we-toc-lang"><div class="we-toc-langlabel">{_esc(lang.get("label", lang.get("code", "")))}</div>'
                f'<ul class="we-toc">{items}</ul></div>'
            )
        return f'<div class="we-toc-wrap">{"".join(blocks)}</div>'

    def _render_symbol_rows(self, payload: dict) -> str:
        category = "symbols"
        rows = []
        for row in payload.get("rows", []):
            href = self._stager.stage(str(row.get("figure", "")), category=category)
            label = row.get("label")
            label_html = f'<div class="we-symbol-label">{_esc(label)}</div>' if label else ""
            rows.append(
                f'<div class="we-symbol-row"><div class="we-symbol-fig">{_img(href, cls="we-symbol-img", alt=str(label or ""))}</div>'
                f'<div class="we-symbol-text">{label_html}{_paragraphs(row.get("text", ""))}</div></div>'
            )
        return f'<div class="we-symbols">{"".join(rows)}</div>'

    def _render_lcd_rows(self, payload: dict) -> str:
        rows = []
        for row in payload.get("rows", []):
            href = self._stager.stage(str(row.get("figure", "")), category="lcd_icons")
            rows.append(
                '<div class="we-lcd-row">'
                f'<div class="we-lcd-no">{_esc(row.get("no", ""))}</div>'
                f'<div class="we-lcd-fig">{_img(href, cls="we-lcd-img", alt=str(row.get("name", "")))}</div>'
                f'<div class="we-lcd-text"><div class="we-lcd-name">{_esc(row.get("name", ""))}</div>{_paragraphs(row.get("desc", ""))}</div>'
                "</div>"
            )
        return f'<div class="we-lcd">{"".join(rows)}</div>'

    def _render_back_cover(self, payload: dict) -> str:
        lines = []
        if payload.get("company"):
            lines.append(f'<div class="we-bc-company">{_esc(payload["company"])}</div>')
        for key in ("address", "phone", "email", "web"):
            if payload.get(key):
                lines.append(f'<div class="we-bc-line">{_esc(payload[key])}</div>')
        return f'<div class="we-backcover">{"".join(lines)}</div>'


# --------------------------------------------------------------------------
# document assembly
# --------------------------------------------------------------------------
_WEB_EDITION_CSS = """\
<style>
.we-doc { --we-page-w: 612; --we-page-h: 792; background:#4b4e54; border-radius:8px; padding:0 0 2.5rem; margin-top:1rem; }
.we-toolbar { position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; align-items:baseline;
  gap:.35rem .9rem; padding:.65rem 1rem; background:#33353a; color:#f5f5f5; border-radius:8px 8px 0 0; }
.we-toolbar .we-title { font-weight:600; }
.we-toolbar .we-meta { font-size:.8rem; color:#c8cacc; }
.we-toolbar .we-actions { margin-left:auto; font-size:.85rem; }
.we-toolbar .we-actions a { color:#9ecbff; margin-left:.9rem; text-decoration:none; }
.we-toolbar .we-actions a:hover { text-decoration:underline; }
.we-page { max-width:min(52rem, calc(100% - 2rem)); margin:1.5rem auto 0; }
.we-page-inner { background:#fff; color:#1c1c1c; box-shadow:0 2px 14px rgba(0,0,0,.5); border-radius:2px;
  min-height:calc((52rem) * var(--we-page-h) / var(--we-page-w)); box-sizing:border-box;
  padding:calc(52rem * 0.06) calc(52rem * 0.08); overflow-wrap:break-word;
  font-family:"Gilroy","Montserrat","Poppins",-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; }
.we-page-num { text-align:center; color:rgba(255,255,255,.62); font-size:.78rem; margin-top:.45rem; }
.we-h1 { font-size:1.5rem; font-weight:700; letter-spacing:.01em; margin:0 0 .8rem; }
.we-h2 { font-size:1.18rem; font-weight:700; margin:1.1rem 0 .5rem; }
.we-h3 { font-size:1rem; font-weight:700; margin:.9rem 0 .4rem; }
.we-body p { margin:.4rem 0; line-height:1.5; font-size:.92rem; }
.we-list { margin:.4rem 0 .4rem 1.2rem; }
.we-list li { margin:.2rem 0; line-height:1.45; font-size:.92rem; }
.we-list li.we-sublist-item { list-style:circle; margin-left:1.1rem; }
.we-safetylead { font-weight:700; text-transform:uppercase; letter-spacing:.03em; margin:.8rem 0; }
.we-figure { margin:.8rem 0; text-align:center; }
.we-image { max-width:100%; height:auto; }
.we-img-missing { color:#b00; font-size:.8rem; font-style:italic; }
.we-table { border-collapse:collapse; width:100%; margin:.6rem 0; font-size:.85rem; }
.we-table th, .we-table td { border:1px solid #c9c9c9; padding:.35rem .5rem; text-align:left; vertical-align:top; }
.we-table th { background:#f0f0f0; font-weight:700; }
.we-cell-img { max-width:3rem; max-height:3rem; }
.we-lcdmode-group { margin:.6rem 0; }
.we-lcdmode-state { font-weight:700; margin:.3rem 0; }
.we-twocol { columns:2; column-gap:1.6rem; }
.we-callout { border-left:4px solid #d0a000; background:#fbf6e6; padding:.5rem .8rem; margin:.7rem 0; }
.we-callout.we-safetywarning, .we-callout.we-warnbox { border-left-color:#c0392b; background:#fbeae8; }
.we-callout.we-fcc { border-left-color:#888; background:#f3f3f3; }
.we-callout-label { font-weight:700; display:block; margin-bottom:.2rem; }
.we-langtag .we-lang { font-weight:700; background:#1c1c1c; color:#fff; padding:.05rem .4rem; border-radius:3px; margin-right:.5rem; }
.we-inbox { display:flex; flex-wrap:wrap; gap:1rem; margin:.8rem 0; }
.we-inbox-item { width:8rem; text-align:center; margin:0; }
.we-inbox-img { max-width:100%; height:auto; }
.we-symbols, .we-lcd { margin:.6rem 0; }
.we-symbol-row, .we-lcd-row { display:flex; gap:.8rem; align-items:flex-start; padding:.45rem 0; border-bottom:1px solid #eee; }
.we-symbol-fig, .we-lcd-fig { flex:0 0 4rem; text-align:center; }
.we-symbol-img, .we-lcd-img { max-width:3.6rem; max-height:3.6rem; }
.we-lcd-no { flex:0 0 1.4rem; font-weight:700; }
.we-symbol-label, .we-lcd-name { font-weight:700; }
.we-toc-wrap { display:flex; flex-wrap:wrap; gap:1.5rem; }
.we-toc-langlabel { font-weight:700; margin-bottom:.3rem; }
.we-toc { list-style:none; margin:0; padding:0; }
.we-toc li { display:flex; gap:.6rem; font-size:.88rem; padding:.12rem 0; }
.we-toc-folio { flex:0 0 1.6rem; color:#888; }
.we-annotations { font-size:.8rem; color:#555; margin-top:.6rem; }
.we-placed { text-align:center; }
.we-placed-img { max-width:100%; height:auto; box-shadow:0 1px 6px rgba(0,0,0,.25); }
.we-backcover { text-align:center; margin-top:2rem; }
.we-bc-company { font-weight:700; font-size:1.1rem; margin-bottom:.4rem; }
@media (prefers-color-scheme: dark) { .we-doc { background:#2a2c30; } }
</style>"""

_META_FIELDS = (("version", "v{}"), ("finalized", "{}"), ("source", "{}"))


def _meta_line(provenance: dict, page_count: int) -> str:
    parts = []
    for key, fmt in _META_FIELDS:
        value = provenance.get(key)
        if value:
            parts.append(fmt.format(_esc(value)))
    parts.append(f"{page_count} pages")
    return " · ".join(parts)


def render_web_edition(
    ir: ManualIR,
    *,
    bundle_root: Path,
    data_root: Path,
    out_dir: Path,
    title: str,
    provenance: dict | None = None,
    html_edition_href: str | None = None,
    log: Callable[[str], None] = print,
) -> WebEdition:
    provenance = provenance or {}
    out_dir.mkdir(parents=True, exist_ok=True)
    stager = _AssetStager(bundle_root=bundle_root, data_root=data_root, assets_dir=out_dir / "assets")
    renderer = _PageRenderer(stager)

    cards: list[str] = []
    total = len(ir.pages)
    for number, page in enumerate(ir.pages, start=1):
        inner = renderer.render(page)
        cards.append(
            f'<section class="we-page" id="page-{number}">'
            f'<div class="we-page-inner">{inner}</div>'
            f'<div class="we-page-num">{number} / {total}</div>'
            "</section>"
        )

    actions = ""
    if html_edition_href:
        actions = f'<span class="we-actions"><a href="{_esc(html_edition_href)}">HTML edition</a></span>'
    toolbar = (
        '<div class="we-toolbar">'
        f'<span class="we-title">{_esc(title)}</span>'
        f'<span class="we-meta">{_meta_line(provenance, total)}</span>'
        f"{actions}</div>"
    )
    body = _WEB_EDITION_CSS + f'\n<div class="we-doc">{toolbar}\n' + "\n".join(cards) + "\n</div>\n"
    body_path = out_dir / "body.html"
    body_path.write_text(body, encoding="utf-8")

    manifest = {
        "schema": "web-edition/v1",
        "title": title,
        "model": ir.model,
        "region": ir.region,
        "language": ir.language,
        "page_count": total,
        "asset_count": stager.count,
        "skipped_raw_blocks": sum(int(getattr(page, "skipped_raw", 0) or 0) for page in ir.pages),
        "unresolved_assets": list(stager.unresolved),
        "provenance": provenance,
        "generator": "tools.idml.web_edition",
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if stager.unresolved:
        log(f"[web-edition] warning: {len(stager.unresolved)} unresolved asset(s): {', '.join(stager.unresolved)}")
    log(f"[web-edition] {ir.model}/{ir.region}: {total} page(s), {stager.count} asset(s) -> {out_dir}")
    return WebEdition(
        out_dir=out_dir,
        body_path=body_path,
        manifest_path=manifest_path,
        page_count=total,
        asset_count=stager.count,
        unresolved_assets=stager.unresolved,
    )
