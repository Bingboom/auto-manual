"""Coarse story-chain height estimates, separate from visible style XML."""
from __future__ import annotations

from dataclasses import dataclass, field

from .app_text_styles import estimated_metrics
from .line_metrics import estimated_line_count
from .params import param_pt

_SIZE = {"h1": 9.0, "h2": 8.6, "h3": 7.0, "label": 6.8}
_LEADING = {"h1": 16.0, "h2": 12.0, "h3": 9.0, "label": 12.0}


def paragraph_estimate(
    params: dict[str, tuple[str, str]],
    semantic_kind: str,
    source_kind: str,
    text: str,
    measure: float,
    *,
    is_preface: bool,
    operation_spacing: float | None,
) -> tuple[float, int]:
    size = _SIZE.get(semantic_kind, 6.2)
    leading = _LEADING.get(semantic_kind, 7.5)
    if metrics := estimated_metrics(params, semantic_kind):
        size, leading = metrics
    if is_preface and source_kind == "body":
        size = param_pt(params, "idml_preface_body_font_size", 7.2)
        leading = param_pt(params, "idml_preface_body_font_leading", 8.6)
    elif source_kind == "body_operation_energy_intro":
        leading = 8.1
    lines = estimated_line_count(
        text,
        measure,
        point_size=size,
        minimum_narrow_chars=20,
    )
    spacing = 0.0
    if is_preface and source_kind == "body":
        spacing = param_pt(
            params, "idml_preface_paragraph_space_after", 2.0,
        ) * len(text.split("\n"))
    if operation_spacing is not None:
        spacing = operation_spacing
    return leading * lines + spacing, lines


@dataclass
class StoryHeight:
    """A prose story's running height estimate.

    With ``frame_height`` it also counts the foot an unbreakable figure leaves:
    a figure line cannot break, so when a figure does not fit the space left
    in a frame, InDesign moves it to the next frame and the foot stays empty.
    Without it, heights simply add up.
    """

    frame_height: float | None = None
    total: float = 0.0
    _used: float = field(default=0.0, repr=False)

    def add(self, height: float, *, unbreakable: bool = False) -> None:
        frame = self.frame_height
        if frame:
            if unbreakable and 0.0 < self._used and self._used + height > frame:
                self.total += frame - self._used
                self._used = 0.0
            self._used = (self._used + height) % frame
        self.total += height

    def next_frame(self) -> None:
        """A forced break: the next block starts at the top of a frame."""
        self._used = 0.0
