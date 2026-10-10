"""Source-bound transparency and glyph checks for freshly sealed symbol tables.

Historical receipts keep their original verification rules. This gate reads
actual ComponentSpecs; metadata cannot opt a symbol component out of admission.
"""
from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
import re

import fitz
from PIL import Image, ImageChops, ImageStat

from tools.manual_ir import read_manual_ir
from tools.manual_ir.components import component_specs_in_flow
from tools.utils.path_utils import PathSegments, get_paths
from tools.web.language_release_evidence import _safe_relative, _sha256
from tools.asset_pipeline.native_svg import native_symbol_svg
from tools.web.shared_symbol_assets import require_shared_symbol_binding, require_usable_symbol_file

SCHEMA = 'auto-manual-symbol-asset-admission/v1'


def _file(root: Path, relative: str, sha: str) -> Path:
    path = root / _safe_relative(relative, field='symbol asset path', source=root)
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('symbol file escapes source root')
    if not path.is_file() or _sha256(path) != sha:
        raise ValueError('symbol source/asset SHA-256 mismatch')
    return path


def _render(data: bytes, suffix: str) -> Image.Image:
    if suffix == '.svg':
        with fitz.open(stream=data, filetype='svg') as doc:
            page = doc[0]
            scale = 256 / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
            return Image.open(BytesIO(pix.tobytes('png'))).convert('RGBA')
    if suffix == '.png':
        return Image.open(BytesIO(data)).convert('RGBA')
    raise ValueError('symbol admission supports transparent SVG/PNG only')


def _normalized(image: Image.Image) -> Image.Image:
    alpha = image.getchannel('A')
    # An alpha channel alone is not evidence: RGBA gray rectangles also fail.
    border = [alpha.getpixel((x, y)) for x in range(image.width)
              for y in (0, image.height - 1)]
    border += [alpha.getpixel((x, y)) for y in range(image.height)
               for x in (0, image.width - 1)]
    if (not border or sum(value > 2 for value in border) / len(border) > 0.5
            or alpha.getextrema()[0] != 0):
        raise ValueError('symbol requires real transparent margins; opaque backdrop detected')
    bounds = alpha.point(lambda value: 255 if value > 2 else 0).getbbox()
    if bounds is None:
        raise ValueError('symbol is empty')
    image = image.crop(bounds)
    image.thumbnail((192, 192), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (192, 192))
    canvas.paste(image, ((192 - image.width) // 2, (192 - image.height) // 2))
    # Premultiplied RGB makes invisible RGB irrelevant and checks native tint.
    r, g, b, a = canvas.split()
    return Image.merge('RGBA', (ImageChops.multiply(r, a), ImageChops.multiply(g, a),
                                ImageChops.multiply(b, a), a))


def compare_symbol(candidate: bytes, suffix: str, reference: bytes) -> dict:
    actual = _normalized(_render(candidate, suffix))
    native = _normalized(_render(reference, '.svg'))
    errors = ImageStat.Stat(ImageChops.difference(actual, native)).mean
    # Fixed engineering tolerance, not supplied by a candidate manifest.
    # Allows antialiasing/resolution changes, rejects substituted glyphs/tint.
    if max(errors) / 255 > 0.02:
        raise ValueError('symbol glyph/background differs from authoritative PDF')
    return {'max_mean_channel_error': round(max(errors) / 255, 6)}


def _text(value: str) -> str:
    # Printed line-end word breaks are layout, not Web copy. Inline hyphens
    # remain significant, and all other caption words must still match.
    value = re.sub(r'(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)', '', value)
    return re.sub(r'\s+', '', value).casefold()


def _caption_errata(source_sha: str, model: str, region: str, language: str) -> list[dict]:
    path = get_paths().renderer_contracts_dir / 'symbol_caption_errata.json'
    if not path.is_file():
        return []
    ledger = json.loads(path.read_text(encoding='utf-8'))
    if ledger.get('schema_version') != 'auto-manual-symbol-caption-errata/v1':
        raise ValueError('unsupported trusted symbol caption errata')
    return [row for row in ledger['entries']
            if (row['source_sha256'], row['model'], row['region'], row['language'])
            == (source_sha, model, region, language)]


def _erratum_source_caption(erratum: dict | None, row: dict, meaning: str) -> str:
    if erratum is None:
        return meaning
    if (erratum.get('status') != 'operator-approved'
            or not erratum.get('operator_decision')
            or erratum['physical_page'] != row['physical_page']
            or erratum['caption_sha256'] != row['caption_sha256']
            or _text(erratum['reviewed_caption']) != _text(meaning)):
        raise ValueError('symbol caption erratum differs from reviewed source binding')
    return erratum['source_caption']


def _matching_erratum(errata: list[dict], row: dict) -> dict | None:
    matches = [entry for entry in errata
               if (entry['physical_page'], entry['caption_sha256'])
               == (row['physical_page'], row['caption_sha256'])]
    if len(matches) > 1:
        raise ValueError('duplicate trusted symbol caption erratum')
    return matches[0] if matches else None


def _reference(page, row: dict, meaning: str, erratum: dict | None = None) -> bytes:
    glyph, caption, band = (fitz.Rect(row[key]) for key in
                            ('glyph_bbox', 'caption_bbox', 'row_bbox'))
    if (band.is_empty or not page.rect.contains(band) or not band.contains(glyph)
            or not band.contains(caption) or glyph.intersects(caption)
            or abs(glyph.y0 + glyph.y1 - caption.y0 - caption.y1) > band.height * 2
            or min(abs(glyph.x1 - caption.x0), abs(caption.x1 - glyph.x0)) > glyph.width * 4):
        raise ValueError('symbol glyph/caption must belong to the same source row')
    source_text = page.get_text('text', clip=caption)
    if _text(row['caption_text']) != _text(meaning):
        raise ValueError('symbol meaning differs from bound source caption')
    expected_source = _erratum_source_caption(erratum, row, meaning)
    if source_text.strip():
        if _text(source_text) != _text(expected_source):
            raise ValueError('symbol meaning differs from source PDF row text')
    else:
        if erratum is not None:
            raise ValueError('symbol caption erratum requires actual source PDF row text')
        # Outlined captions have no extractable text. Bind the reviewed
        # transcription to actual source pixels; never pretend a hash is OCR.
        if not any(caption.contains(d['rect']) for d in page.get_drawings()):
            raise ValueError('outlined symbol caption has no source drawings')
    pixels = page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=caption, alpha=False)
    if hashlib.sha256(pixels.tobytes('png')).hexdigest() != row['caption_sha256']:
        raise ValueError('symbol caption pixels differ from source binding')
    return native_symbol_svg(page, row['drawing_indices'], row['glyph_bbox'])


def _component_rows(specs):
    expected = []
    for spec in specs:
        panels = next(slot.content for slot in spec.slots if slot.role == 'panels')
        for panel in panels:
            for item in panel:
                expected.append((spec.assets[item['asset_index']].asset_ref, item['meaning_text']))
    return expected


def require_symbol_asset_admission(markdown_dir: Path, source_root: Path,
                                   manifest: dict, language: str) -> list[dict]:
    """Require exact row coverage and independently reconstruct native references."""
    try:
        ir = read_manual_ir(markdown_dir / PathSegments.MANUAL_IR_JSON)
        specs = [s for page in ir.pages for block in page.blocks
                 for s in component_specs_in_flow([block.payload])
                 if s.component_id == 'HB-TABLE-SYMBOL-ICON']
        if not specs:
            return []
        admission = manifest.get('symbol_asset_admission', {})
        if admission.get('schema_version') != SCHEMA:
            raise ValueError('symbol table requires source-bound asset admission')
        rows = admission.get('locales', {}).get(language)
        expected = _component_rows(specs)
        if (not isinstance(rows, list) or len(rows) != len(expected)
                or [r.get('asset_ref') for r in rows] != [ref for ref, _ in expected]):
            raise ValueError('symbol admission must cover every actual component row in order')
        source = manifest['original_source']
        pdf = _file(source_root, source['filename'], source['sha256'])
        errata = _caption_errata(source['sha256'], ir.model, ir.region, language)
        report = []
        with fitz.open(pdf) as doc:
            for row, (ref, meaning) in zip(rows, expected, strict=True):
                candidate = _file(markdown_dir, ref, row['asset_sha256'])
                require_usable_symbol_file(candidate)
                require_shared_symbol_binding(row, candidate)
                page_number = row['physical_page']
                if not isinstance(page_number, int) or not 1 <= page_number <= len(doc):
                    raise ValueError('symbol physical page outside authoritative PDF')
                erratum = _matching_erratum(errata, row)
                reference = _reference(doc[page_number - 1], row, meaning,
                                       erratum)
                result = {'asset_ref': ref, 'physical_page': page_number,
                          **compare_symbol(candidate.read_bytes(), candidate.suffix, reference)}
                if erratum:
                    result['caption_erratum'] = erratum['id']
                report.append(result)
        return report
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
        raise RuntimeError('symbol asset admission failed: ' + str(exc)) from exc
