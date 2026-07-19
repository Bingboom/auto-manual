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
from ..style_names import paragraph_style_ref

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
    data_root: Path | None = None
    language: str | None = None
    # Approved flowing pages may move their whole host frame to match the
    # reference trim geometry. Components subtract that origin shift from
    # their absolute measured offset so the remaining paragraph indent is
    # non-negative and survives InDesign's inline-object left-edge clamp.
    inline_origin_shift: float = 0.0
    # writer._add_story_parts, for components that render rounded objects
    # as anchored frames (one sub-story per frame). None in pure/table-only
    # contexts; renderers must keep a table fallback for that case.
    add_story: Callable[[str, str, list[str]], str] | None = None

    @property
    def text_measure(self) -> float:
        return self.page_w - self.m_l - self.m_r

    def art_frame_size(self, img: Path, max_w: float = 120.0) -> tuple[float, float]:
        return art_frame_size(img, max_w, page_w=self.page_w, m_l=self.m_l, m_r=self.m_r)

    def resolve_bundle_image(self, ref: str) -> Path | None:
        # Flow IDML can carry images emitted from the phase2 data snapshot as
        # well as images copied into the prepared RST bundle.  Keep the
        # lookup contract in the render context so individual components do
        # not need to know which source plane supplied an asset.
        roots = [self.bundle_root]
        if self.data_root is not None:
            roots.append(self.data_root)
        roots.append(self.root)
        for base in roots:
            resolved = resolve_bundle_image(base, ref)
            if resolved is not None:
                return resolved
        return None


def figure_paragraph(inner: str, tail: str = "<Br/>") -> str:
    """An HB Figure paragraph wrapping inline art (icon / mark / LCD shot)."""
    style_ref = paragraph_style_ref("HB Figure")
    return (f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">'
            '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
            + inner + tail + '</CharacterStyleRange></ParagraphStyleRange>\n')
