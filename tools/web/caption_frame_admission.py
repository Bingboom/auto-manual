"""Reject baked contrasting caption fills at fresh frozen-Web sealing.

This bounded pixel check only examines declared ReferenceFigure CSS label
rectangles. It is not OCR or general-purpose shape recognition; bare-art and
browser QC still cover outlined frames, undeclared labels and artwork edges.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image

from tools.manual_ir import read_manual_ir
from tools.manual_ir.components import component_specs_in_flow
from tools.manual_ir.hashing import file_sha256
from tools.utils.path_utils import PathSegments
from tools.web.language_release_evidence import _safe_relative


def _rgb(tone: str) -> tuple[int, ...]:
    if not isinstance(tone, str) or len(tone) != 7 or not tone.startswith('#'):
        raise ValueError('caption frame requires a measured #rrggbb tone')
    return tuple(int(tone[i:i + 2], 16) for i in (1, 3, 5))


def _image(path: Path) -> Image.Image:
    if path.suffix.lower() == '.svg':
        with fitz.open(path) as document:
            page = document[0]
            scale = 1024 / max(page.rect.width, page.rect.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True)
            return Image.open(BytesIO(pix.tobytes('png'))).convert('RGBA')
    with Image.open(path) as image:
        return image.convert('RGBA')


def check_caption_frames(path: Path, layout: dict) -> list[dict]:
    """Reject a CSS fill already occupying >=85% of its inset art rectangle."""
    labels = [label for label in layout.get('labels', []) if 'fill' in label]
    if not labels:
        return []
    panel = _rgb(layout.get('panel_fill'))
    image = _image(path)
    report = []
    for label in labels:
        fill = _rgb(label['fill'])
        # A fill on a same-tone panel is not detectable by color occupancy.
        if max(abs(a - b) for a, b in zip(panel, fill, strict=True)) < 12:
            report.append({'line': label['line'], 'status': 'same-tone-visual-review'})
            continue
        x, y, width, height = label['rect']
        if (width <= 0 or height <= 0 or min(x, y) < 0
                or x + width > 100 or y + height > 100):
            raise ValueError('caption frame rectangle outside artwork')
        box = (round((x + width * .1) * image.width / 100),
               round((y + height * .1) * image.height / 100),
               round((x + width * .9) * image.width / 100),
               round((y + height * .9) * image.height / 100))
        pixels = list(image.crop(box).getdata())
        if not pixels:
            raise ValueError('caption frame region has no pixels')
        occupied = sum(pixel[3] >= 250 and max(abs(a - b) for a, b in
                       zip(pixel[:3], fill, strict=True)) <= 6 for pixel in pixels) / len(pixels)
        if occupied >= .85:
            raise ValueError('baked caption frame remains in base art; remove it and draw it with shared CSS')
        report.append({'line': label['line'], 'status': 'passed',
                       'baked_fill_fraction': round(occupied, 6)})
    return report


def require_caption_frame_admission(markdown_dir: Path) -> list[dict]:
    """Read actual frozen ReferenceFigure specs; never run on historical replay."""
    try:
        ir = read_manual_ir(markdown_dir / PathSegments.MANUAL_IR_JSON)
        report = []
        for page in ir.pages:
            for block in page.blocks:
                for spec in component_specs_in_flow([block.payload]):
                    if (spec.component_id != 'HB-SPECIAL-REFERENCE-FIGURE'
                            or spec.metadata.get('presentation_mode') != 'base-art-live-copy'):
                        continue
                    layout = spec.metadata.get('base_art_layout') or {}
                    if not any('fill' in label for label in layout.get('labels', [])):
                        continue
                    asset = next(a for a in spec.assets if a.role == 'source_art')
                    relative = _safe_relative(asset.asset_ref, field='caption artwork', source=markdown_dir)
                    path = markdown_dir / relative
                    if path.is_symlink() or not path.resolve().is_relative_to(markdown_dir.resolve()):
                        raise ValueError('caption artwork escapes package')
                    if file_sha256(path) != layout.get('art_sha256'):
                        raise ValueError('caption artwork SHA-256 differs from CSS layout binding')
                    report.append({'source_ref': spec.source_ref, 'asset_ref': asset.asset_ref,
                                   'labels': check_caption_frames(path, layout)})
        return report
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
        raise RuntimeError('caption frame admission failed: ' + str(exc)) from exc
