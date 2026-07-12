"""Stable InDesign labels for source tracing and final-mile automation."""
from __future__ import annotations

import re


_LABELED_ELEMENTS = ("Spread", "Page", "TextFrame", "Rectangle", "Story")


def apply_stable_labels(xml: str) -> str:
    """Attach a deterministic Script Label to editable document objects."""
    for element in _LABELED_ELEMENTS:
        pattern = re.compile(rf"<{element} Self=\"([^\"]+)\"(?![^>]*\bLabel=)")
        xml = pattern.sub(
            lambda match: f'<{element} Self="{match.group(1)}" Label="hb:self={match.group(1)}"',
            xml,
        )
    return xml
