"""Component rendering contract (componentization P2).

A component renderer is a function
``render(spec, ctx, *, tid, terminal, span_columns=True, measure_w=None)
-> (xml, est_height_pt)`` registered by its spec ``kind`` in
``tools.idml.components.REGISTRY``. The extractor
(tools/idml_rst_extract.py) owns the spec shapes; parity between the two
is test-enforced. This is the extension point for new manual components
(future non-power-station lines): add a module, register a kind, and the
prose story picks it up — no writer surgery.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..primitives import art_frame_size, resolve_bundle_image

# (spec, ctx, *, tid, terminal, span_columns, measure_w) -> (xml, est_height)
ComponentRenderer = Callable[..., tuple[str, float]]


@dataclass(frozen=True)
class RenderContext:
    """Everything a component needs from the outside world.

    Page geometry + layout params + the two asset roots (repo root for
    shared brand assets, bundle root for content-referenced art). Future
    asset indirection (Design_Asset_Registry) hooks in here, not in the
    individual renderers.
    """
    params: dict[str, tuple[str, str]]
    page_w: float
    m_l: float
    m_r: float
    root: Path
    bundle_root: Path

    @property
    def text_measure(self) -> float:
        return self.page_w - self.m_l - self.m_r

    def art_frame_size(self, img: Path, max_w: float = 120.0) -> tuple[float, float]:
        return art_frame_size(img, max_w, page_w=self.page_w, m_l=self.m_l, m_r=self.m_r)

    def resolve_bundle_image(self, ref: str) -> Path | None:
        return resolve_bundle_image(self.bundle_root, ref)


def figure_paragraph(inner: str, tail: str = "<Br/>") -> str:
    """An HB Figure paragraph wrapping inline art (icon / mark / LCD shot)."""
    return ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
            '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
            + inner + tail + '</CharacterStyleRange></ParagraphStyleRange>\n')
