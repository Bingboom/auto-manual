"""Select original PDF vector paths without losing group opacity or transforms."""
from __future__ import annotations

from copy import deepcopy
import xml.etree.ElementTree as ET
import re

import fitz

SVG = '{http://www.w3.org/2000/svg}'


def _path_key(path: ET.Element) -> tuple[str, ...]:
    tokens = re.findall(r'[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',
                        path.get('d', '').rstrip('Zz '))
    # Compound paths can close each subpath explicitly for the stroke, while
    # the fill already returns to its starting point. Compare those no-op
    # closures too, without changing either original SVG path.
    starts = [i for i, token in enumerate(tokens) if token == 'M']
    for start, end in reversed(list(zip(starts, [*starts[1:], len(tokens)], strict=True))):
        if end - start >= 6 and tokens[end - 1] == 'Z':
            try:
                closed = tuple(map(float, tokens[end - 3:end - 1]))
                origin = tuple(map(float, tokens[start + 1:start + 3]))
            except ValueError:
                continue
            if closed == origin:
                del tokens[end - 1]
    # MuPDF sometimes closes a stroke explicitly and the fill implicitly.
    command = next((t for t in reversed(tokens) if t.isalpha()), '')
    if (len(tokens) > 5 and tokens[0] == 'M' and command in {'M', 'L'}
            and tokens[-2:] == tokens[1:3]):
        tokens = tokens[:-2]
        if tokens[-1] == 'L':
            tokens.pop()
    return tuple(tokens)


def _drawing_paths(drawings: list[dict], visible: list[ET.Element]) -> list[list[ET.Element]]:
    if len(visible) == len(drawings):
        return [[path] for path in visible]
    if len(visible) == sum(2 if d['type'] == 'fs' else 1 for d in drawings):
        # MuPDF may emit a fill-and-stroke drawing as two original SVG paths.
        # Retain both, including their ancestor opacity/transform groups.
        mapped = []
        offset = 0
        for drawing in drawings:
            count = 2 if drawing['type'] == 'fs' else 1
            paths = visible[offset:offset + count]
            if count == 2 and (
                paths[0].get('transform') != paths[1].get('transform')
                or _path_key(paths[0]) != _path_key(paths[1])
            ):
                raise ValueError('native PDF fill/stroke SVG mapping is unsupported')
            mapped.append(paths)
            offset += count
        return mapped
    raise ValueError('native PDF drawing/SVG path mapping is unsupported')


def native_symbol_svg(page: fitz.Page, indices: list[int], glyph_bbox: list[float]) -> bytes:
    """Keep source paths and ancestors; omit page/cell objects by geometry.

    Drawing indices refer to get_drawings() (not extended group records). The
    SVG mapping is checked before use. Bounding boxes are reviewed source
    coordinates, never inferred from candidate filenames or their semantics.
    """
    drawings = page.get_drawings()
    box = fitz.Rect(glyph_bbox)
    if box.is_empty or not page.rect.contains(box):
        raise ValueError('symbol glyph bounds outside source page')
    inside = [i for i, d in enumerate(drawings) if box.contains(d['rect'])]
    if not indices or sorted(set(indices)) != indices or indices != inside:
        raise ValueError('symbol selection must include every drawing inside glyph bounds')
    return _selected_svg(page, drawings, indices, box)


def native_art_svg(page: fitz.Page, indices: list[int], crop_bbox: list[float]) -> bytes:
    """Retain reviewed panel paths with original clipping, opacity and transforms.

    Unlike a symbol glyph, a panel may deliberately omit a caption frame and
    contain source paths that extend beyond the crop under a clipping group.
    This is not symbol admission; native_symbol_svg keeps its completeness rule.
    """
    drawings = page.get_drawings()
    box = fitz.Rect(crop_bbox)
    if box.is_empty or not page.rect.contains(box):
        raise ValueError("art crop bounds outside source page")
    if (not indices or sorted(set(indices)) != indices
            or any(not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < len(drawings)
                   for i in indices)):
        raise ValueError("art selection requires ordered valid drawing indices")
    return _selected_svg(page, drawings, indices, box, preserve_images=True)


def _selected_svg(page, drawings, indices, box, *, preserve_images=False) -> bytes:
    root = ET.fromstring(page.get_svg_image(text_as_path=False))
    visible = []
    image_ids = set()

    def collect(node, in_defs=False, matrix=None):
        matrix = fitz.Matrix(1, 0, 0, 1, 0, 0) if matrix is None else matrix
        raw_transform = node.get('transform', '')
        if raw_transform:
            match = re.fullmatch(r'matrix\(([^)]+)\)', raw_transform)
            if match is None:
                raise ValueError('native PDF SVG transform is unsupported')
            values = [float(v) for v in re.split(r'[\s,]+', match[1].strip())]
            if len(values) != 6:
                raise ValueError('native PDF SVG matrix is unsupported')
            matrix = fitz.Matrix(*values) * matrix
        in_defs = in_defs or node.tag == SVG + 'defs'
        if not in_defs and node.tag == SVG + 'path':
            visible.append(node)
        if preserve_images and not in_defs and node.tag == SVG + 'image':
            x, y, width, height = [float(node.get(k, '0')) for k in ('x', 'y', 'width', 'height')]
            bounds = fitz.Rect(x, y, x + width, y + height) * matrix
            if bounds.intersects(box):
                image_ids.add(id(node))
        for child in node:
            collect(child, in_defs, matrix)

    collect(root)
    mapped = _drawing_paths(drawings, visible)
    keep = {id(path) for i in indices for path in mapped[i]}

    def prune(node):
        if node.tag == SVG + 'defs':
            return deepcopy(node)
        if node.tag == SVG + 'path':
            return deepcopy(node) if id(node) in keep else None
        if node.tag == SVG + 'image':
            return deepcopy(node) if id(node) in image_ids else None
        if node.tag not in {SVG + 'svg', SVG + 'g'}:
            return None
        result = ET.Element(node.tag, node.attrib)
        for child in node:
            selected = prune(child)
            if selected is not None:
                result.append(selected)
        return result if len(result) else None

    selected = prune(root)
    if selected is None:
        raise ValueError('empty native artwork')
    # Crop the source geometry without repainting or flattening its clipping.
    selected.set('viewBox', f'{box.x0} {box.y0} {box.width} {box.height}')
    selected.set('width', str(box.width))
    selected.set('height', str(box.height))
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ET.tostring(selected, encoding='utf-8', xml_declaration=True)
