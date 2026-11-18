"""Native SVG comparison preserves source art and checks every drawing."""
from types import SimpleNamespace
import unittest
import xml.etree.ElementTree as ET

import fitz

from tools.asset_pipeline.native_svg import native_symbol_svg, SVG


def page_for(raw, drawings):
    return SimpleNamespace(
        rect=fitz.Rect(0, 0, 100, 100),
        get_drawings=lambda: drawings,
        get_svg_image=lambda **kwargs: raw,
    )


def svg_for(fill, stroke, *, transform="matrix(1,0,0,1,0,0)"):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
        'viewBox="0 0 100 100"><g opacity=".7">'
        f'<path d="{fill}" transform="{transform}" fill="#888"/>'
        f'<path d="{stroke}" transform="{transform}" fill="none" '
        'stroke="#222" stroke-width="1"/></g></svg>'
    )


class NativeClosedSubpathTests(unittest.TestCase):
    def test_implicit_lines_and_each_compound_closure_preserve_source_art(self):
        fill = 'M2 2 8 2 8 8 2 8ZM12 12H18V18H12Z'
        stroke = 'M2 2 8 2 8 8 2 8 2 2ZM12 12H18V18H12L12 12Z'
        raw = svg_for(fill, stroke)
        page = page_for(raw, [{'type': 'fs', 'rect': fitz.Rect(1, 1, 19, 19)}])
        selected = native_symbol_svg(page, [0], [0, 0, 20, 20])
        source_root, selected_root = ET.fromstring(raw), ET.fromstring(selected)
        self.assertEqual(
            [p.attrib for p in source_root.iter(SVG + 'path')],
            [p.attrib for p in selected_root.iter(SVG + 'path')],
        )
        self.assertEqual(next(selected_root.iter(SVG + 'g')).get('opacity'), '.7')
        # This is an equality-key fix, never a rewritten or flattened SVG.
        with fitz.open(stream=raw.encode(), filetype='svg') as original:
            with fitz.open(stream=selected, filetype='svg') as output:
                source_pixels = original[0].get_pixmap(
                    matrix=fitz.Matrix(3, 3), clip=fitz.Rect(0, 0, 20, 20), alpha=True,
                )
                output_pixels = output[0].get_pixmap(matrix=fitz.Matrix(3, 3), alpha=True)
                self.assertEqual(source_pixels.samples, output_pixels.samples)

    def test_implicit_repeated_cubics_compare_with_explicit_commands(self):
        fill = 'M2 2C3 2 4 4 5 4 6 4 7 2 8 2ZM12 12L18 12 18 18Z'
        stroke = 'M2 2C3 2 4 4 5 4C6 4 7 2 8 2L2 2ZM12 12L18 12L18 18L12 12Z'
        raw = svg_for(fill, stroke)
        page = page_for(raw, [{'type': 'fs', 'rect': fitz.Rect(1, 1, 19, 19)}])
        selected = ET.fromstring(native_symbol_svg(page, [0], [0, 0, 20, 20]))
        self.assertEqual([p.get('d') for p in selected.iter(SVG + 'path')], [fill, stroke])

    def test_unselected_fill_stroke_geometry_or_transform_must_still_match(self):
        fill = 'M42 42L48 42 48 48Z'
        for stroke, transform in [
            ('M42 42L48 42 48 48 42.001 42Z', 'matrix(1,0,0,1,0,0)'),
            ('M42 42L48 42 48 48 42 42Z', 'matrix(1,0,0,1,.001,0)'),
        ]:
            with self.subTest(stroke=stroke, transform=transform):
                raw = (
                    '<svg xmlns="http://www.w3.org/2000/svg">'
                    '<path d="M2 2H8V8H2Z" fill="#222"/>'
                    f'<path d="{fill}" transform="matrix(1,0,0,1,0,0)" fill="#888"/>'
                    f'<path d="{stroke}" transform="{transform}" fill="none" stroke="#222"/>'
                    '</svg>'
                )
                page = page_for(raw, [
                    {'type': 'f', 'rect': fitz.Rect(2, 2, 8, 8)},
                    {'type': 'fs', 'rect': fitz.Rect(42, 42, 48, 48)},
                ])
                # Only drawing0 is selected, but the entire mapping stays checked.
                with self.assertRaisesRegex(ValueError, 'fill/stroke SVG mapping'):
                    native_symbol_svg(page, [0], [0, 0, 10, 10])

    def test_terminal_close_is_not_discarded_from_an_open_contour(self):
        fill, stroke = 'M2 2L8 2 8 8Z', 'M2 2L8 2 8 8'
        page = page_for(svg_for(fill, stroke), [
            {'type': 'fs', 'rect': fitz.Rect(2, 2, 8, 8)},
        ])
        with self.assertRaisesRegex(ValueError, 'fill/stroke SVG mapping'):
            native_symbol_svg(page, [0], [0, 0, 10, 10])


if __name__ == '__main__':
    unittest.main()
