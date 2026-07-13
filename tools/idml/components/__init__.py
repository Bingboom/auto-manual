"""IDML component registry (componentization P2).

``REGISTRY`` maps a component spec ``kind`` (owned by the extractor,
tools/idml_rst_extract.py — parity is test-enforced) to its renderer.
``tailwarnbox`` has no extractor form: the safety+symbols page composer
synthesizes it from trailing safety warnboxes.

Adding a component = one module + one REGISTRY entry; stories and pages
dispatch through ``render`` and never grow per-kind branches again.
"""
from __future__ import annotations

from .base import ComponentRenderer, RenderContext, figure_paragraph
from .callout import (
    render_safetywarning,
    render_tailwarnbox,
    render_warnbox,
    render_warninglead,
)
from .fcc import render_fcc
from .emphasis import render_emphasispill
from .inbox import render_inbox
from .lcdmode import render_lcdmode
from .notice import render_notice
from .prose_image import render_image_block
from .prose_table import body_data_table_kind, render_table_block

from .langbadge import render_langtag
from .oppanel import render_oppanel
from .warranty import (
    render_warrantylead,
    render_warrantysection,
    render_warrantyyears,
)

REGISTRY: dict[str, ComponentRenderer] = {
    "inbox": render_inbox,
    "safetywarning": render_safetywarning,
    "safetyinstruction": render_safetywarning,
    "warninglead": render_warninglead,
    "tailwarnbox": render_tailwarnbox,
    "warnbox": render_warnbox,
    "notice": render_notice,
    "oppanel": render_oppanel,
    "langtag": render_langtag,
    "warrantyyears": render_warrantyyears,
    "warrantylead": render_warrantylead,
    "warrantysection": render_warrantysection,
    "fcc": render_fcc,
    "emphasispill": render_emphasispill,
    "lcdmode": render_lcdmode,
}


def render(spec: dict, ctx: RenderContext, *, tid: str, terminal: bool,
           span_columns: bool = True,
           measure_w: float | None = None) -> tuple[str, float]:
    """Dispatch a component spec to its registered renderer.

    Unknown kinds render as nothing — the historical contract: the story
    keeps flowing and the block is simply absent (the extractor counts
    unrecognized raw constructs separately as skipped_raw).
    """
    renderer = REGISTRY.get(str(spec.get("kind") or ""))
    if renderer is None:
        return "", 0.0
    return renderer(spec, ctx, tid=tid, terminal=terminal,
                    span_columns=span_columns, measure_w=measure_w)


__all__ = [
    "ComponentRenderer", "RenderContext", "REGISTRY", "render",
    "figure_paragraph", "render_image_block", "render_table_block",
    "body_data_table_kind",
]
