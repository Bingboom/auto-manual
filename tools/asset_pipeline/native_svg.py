"""Select original PDF vector paths without losing group opacity or transforms."""
from __future__ import annotations

from copy import deepcopy
import xml.etree.ElementTree as ET

import fitz

SVG = '{http://www.w3.org/2000/svg}'


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
                or paths[0].get('d', '').rstrip('Zz ') != paths[1].get('d', '').rstrip('Zz ')
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
    root = ET.fromstring(page.get_svg_image(text_as_path=False))
    visible = []

    def collect(node, in_defs=False):
        in_defs = in_defs or node.tag == SVG + 'defs'
        if not in_defs and node.tag == SVG + 'path':
            visible.append(node)
        for child in node:
            collect(child, in_defs)

    collect(root)
    mapped = _drawing_paths(drawings, visible)
    keep = {id(path) for i in indices for path in mapped[i]}

    def prune(node):
        if node.tag == SVG + 'defs':
            return deepcopy(node)
        if node.tag == SVG + 'path':
            return deepcopy(node) if id(node) in keep else None
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
        raise ValueError('empty native symbol')
    # Small margin is outside original drawing bounds. No white/gray overlay.
    selected.set('viewBox', f'{box.x0} {box.y0} {box.width} {box.height}')
    selected.set('width', str(box.width))
    selected.set('height', str(box.height))
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ET.tostring(selected, encoding='utf-8', xml_declaration=True)
