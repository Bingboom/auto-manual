"""Give every Web callout on a page one label-column width.

Callout tables size their label column from content, so a long localized label
(fr ``AVERTISSEMENT``, uk ``ПОПЕРЕДЖЕННЯ``) stays on one line instead of
breaking mid-word. To keep one first-column boundary across the page, each
label cell also carries the page's distinct labels as invisible width
references (``manual-callout-label-sizer``). The browser then sizes every label
column to the widest label in the reader's own font; Gilroy is not
redistributed, so no width is computed here.
"""
from __future__ import annotations

import html
import re

from bs4 import BeautifulSoup

LABEL_SIZER_CLASS = "manual-callout-label-sizer"

_CALLOUT_TABLE_RE = re.compile(
    r'<table\b(?=[^>]*\bclass=["\'][^"\']*\bmanual-callout-table\b)[^>]*>.*?</table>',
    re.IGNORECASE | re.DOTALL,
)
_LABEL_CELL_RE = re.compile(
    r'(<td\b(?=[^>]*\bclass=["\'][^"\']*\bmanual-callout-label\b)[^>]*>)(.*?)(</td>)',
    re.IGNORECASE | re.DOTALL,
)
_SIZER_RE = re.compile(
    rf'<span\b[^>]*\bclass=["\']{LABEL_SIZER_CLASS}["\'][^>]*>.*?</span>',
    re.IGNORECASE | re.DOTALL,
)


def _label_text(cell_html: str) -> str:
    return " ".join(BeautifulSoup(cell_html, "html.parser").get_text(" ").split())


def align_callout_label_columns(page_html: str) -> str:
    """Append the page's distinct callout labels to every label cell as width references.

    A page with fewer than two distinct labels is returned unchanged: its label
    columns already share one width. Existing references are replaced, so the
    transform is idempotent.
    """
    tables = list(_CALLOUT_TABLE_RE.finditer(page_html))
    labels: list[str] = []
    for table in tables:
        cell = _LABEL_CELL_RE.search(table.group(0))
        if cell is None:
            continue
        label = _label_text(_SIZER_RE.sub("", cell.group(2)))
        if label and label not in labels:
            labels.append(label)
    if len(labels) < 2:
        return page_html
    sizers = "".join(
        f'<span class="{LABEL_SIZER_CLASS}" aria-hidden="true">{html.escape(label, quote=False)}</span>'
        for label in labels
    )

    def rewrite_cell(cell: re.Match[str]) -> str:
        return cell.group(1) + _SIZER_RE.sub("", cell.group(2)) + sizers + cell.group(3)

    def rewrite_table(table: re.Match[str]) -> str:
        return _LABEL_CELL_RE.sub(rewrite_cell, table.group(0), count=1)

    return _CALLOUT_TABLE_RE.sub(rewrite_table, page_html)


__all__ = ["LABEL_SIZER_CLASS", "align_callout_label_columns"]
