"""Keep native front matter and safety structure on the shared manual styles."""
from __future__ import annotations

from copy import deepcopy
import re

from tools.web.frozen_ai_flow import callout, heading, is_heading, node, paragraph, squash, text


def strong_paragraph(value):
    return node('paragraph', [node('strong', [text(value)])])


def preface_flow(raw, correct):
    """Separate the printed IMPORTANT label and join only print-wrapped lines."""
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if lines and re.fullmatch(r'[A-Z]{2}', lines[0]):
        lines.pop(0)
    if lines and re.fullmatch(r'[A-Z]{2}', lines[-1]):
        lines.pop()
    label = lines.pop() if lines and is_heading(lines[-1]) else None
    paragraphs, pending = [], []
    for line in lines:
        pending.append(line)
        if re.search(r'[.!?]$', line):
            paragraphs.append(correct(squash('\n'.join(pending))))
            pending = []
    if pending:
        paragraphs.append(correct(squash('\n'.join(pending))))
    return ([strong_paragraph(label)] if label else []) + [paragraph(p) for p in paragraphs]


def template_heading_levels(value):
    """Native H2 chapters/H3 subsections project to the template H1/H2 scale."""
    result = deepcopy(value)
    if result.get('kind') == 'component':
        return result  # Component-owned headings keep their registered contract.
    if result.get('kind') == 'heading':
        result['level'] = max(1, result['level'] - 1)
    if 'children' in result:
        result['children'] = [template_heading_levels(child) for child in result['children']]
    return result


def safety_flow(book):
    """Map the source warning, eight precautions and maintenance section once."""
    start, end = book.starts()[:2]
    blocks = [block for page in book.source['pages'] for block in page['blocks_visual_order']
              if start[:2] <= (page['physical_page'], block['bbox'][1]) < end[:2]]
    blocks.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
    values = [book.correct(squash(block['text'])) for block in blocks]
    if len(values) < 5 or values[0] != book.locale['titles'][0] or not is_heading(values[1]):
        raise ValueError('native safety heading and warning structure changed')
    warning, lead, *body = values[1:]
    headings = [index for index, value in enumerate(body) if is_heading(value)]
    if len(headings) != 1:
        raise ValueError('native safety must contain one maintenance heading')
    split = headings[0]
    items, continuation = [], []

    def flush():
        if continuation:
            if not items:
                raise ValueError('safety continuation has no owning precaution')
            items[-1]['children'].append(paragraph(' '.join(continuation)))
            continuation.clear()

    for value in body[:split]:
        if value.startswith('•'):
            flush()
            items.append(node('list_item', [paragraph(value.removeprefix('•').strip())]))
        else:
            continuation.append(value)
            if re.search(r'[.!?]$', value):
                flush()
    flush()
    if len(items) != 8 or not body[split + 1:]:
        raise ValueError('native safety precaution or maintenance coverage changed')
    notice = callout('⚠', [strong_paragraph(warning)], variant='warning', language=book.language,
                     source_ref=f'{book.language}/safety#source-warning-symbol')
    label = notice['carrier_flow'][0]['children'][0]['children'][0]['children'][0]
    label['children'] = [
        node('group', [text('⚠')], role='container',
             presentation={'html': {'attributes': {'style': 'display:none'}}}),
        node('image', source=book.assets['symbol.general_warning']['asset_ref'], alt='⚠',
             presentation={'html': {'attributes': {'style': 'width:2.5rem;height:auto'}}}),
    ]
    return [notice,
            strong_paragraph(lead), node('list', items, ordered=False),
            heading(body[split], level=2), *[paragraph(v) for v in body[split + 1:]]]


def positioned_safety_flow(book):
    """Use a target's native positioned safety leaves when PDF blocks merge bullets."""
    record = book.records['safety']
    notice = callout(record['warning'], [strong_paragraph(record['lead'])],
                     variant='warning', language=book.language,
                     source_ref=f'{book.language}/safety#native-warning')
    items = [node('list_item', [paragraph(book.correct(value))])
             for value in record['precautions']]
    return [notice, paragraph(book.correct(record['intro'])),
            node('list', items, ordered=False),
            heading(record['maintenance_heading'], level=2),
            paragraph(book.correct(record['maintenance_body']))]
