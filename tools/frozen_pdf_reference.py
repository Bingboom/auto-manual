"""Bind native PDF figure labels to the existing shared live-copy renderer."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path

from bs4 import BeautifulSoup

from tools.component_specs.reference_figure_html import parse_reference_figure_html
from tools.frozen_ai_flow import node, root, squash, text
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web_presentation_contract import _validate_reference_base_art_layout


def bind_reference_labels(book, bindings):
    """Resolve each declared label once within its PDF figure, before copying assets."""
    for figure in book.figures:
        binding = bindings[figure['slug']]
        labels = binding.get('live_labels')
        layout = binding.get('base_art_layout')
        if labels is None and layout is None:
            continue
        if isinstance(labels, Mapping):
            labels = labels.get(book.language)
        if not isinstance(labels, list) or not labels or not all(
                isinstance(value, str) and value.strip() for value in labels):
            raise ValueError('reference live_labels must declare non-empty source strings')
        config = {'capture_following_lines': len(labels), 'base_art_layout': layout}
        _validate_reference_base_art_layout(config, field=figure['slug'])
        if layout['art_sha256'] != book.assets[figure['asset_key']]['sha256']:
            raise ValueError('reference label layout artwork SHA-256 mismatch')
        page = next(p for p in book.source['pages']
                    if p['physical_page'] == figure['physical_page'])
        x0, y0, x1, y1 = figure['clip_points']
        available = [b for b in page['blocks_visual_order']
                     if x0 <= b['bbox'][0] < x1 and y0 <= b['bbox'][1] < y1]
        resolved = []
        for expected in labels:
            matches = [b for b in available if squash(b['text']) == expected]
            if len(matches) != 1 or any(b['bbox'] == matches[0]['bbox'] for b in resolved):
                raise ValueError(f"{figure['slug']}: reference label must match exactly once: {expected}")
            block = matches[0]
            resolved.append({'text': book.correct(squash(block['text'])), 'bbox': block['bbox']})
        figure.update(live_captions=resolved, base_art_layout=deepcopy(layout))


def reference_label_regions(figures):
    """Consume only matched label blocks; neighboring charging copy stays prose."""
    return [{'physical_page': figure['physical_page'], 'section': figure['section_id'],
             'consume_bbox': label['bbox']}
            for figure in figures for label in figure.get('live_captions', [])]


def labeled_artwork_node(figure, asset_ref, language):
    """Create a frozen ReferenceFigure spec through the shared HTML intake adapter."""
    identity = figure['slug']
    labels = figure['live_captions']
    lines = [node('group', [text(label['text'])], role='container',
                  presentation={'html': {'attributes': {'class': 'line'}}}) for label in labels]
    carrier = (root(node('image', source=asset_ref, alt=identity)),
               root(node('group', lines, role='container',
                         presentation={'html': {'attributes': {'class': 'line-block'}}})))
    soup = BeautifulSoup(flow_nodes_to_html(carrier), 'html.parser')
    spec, _, _, _ = parse_reference_figure_html(
        soup, image=soup.img,
        config={'id': identity, 'image_key': identity, 'asset_scope': 'shared',
                'capture_following_lines': len(labels),
                'presentation_mode': 'base-art-live-copy',
                'base_art_layout': figure['base_art_layout']},
        source_path=Path(language) / f"pdf-page-{figure['physical_page']}",
        language=language, composite_locale=None, approved_entry=None, approved_path=None,
    )
    return component_flow_node(spec, carrier_flow=carrier, root=True)
