"""Arrange a base-art reference figure: frozen art, source lines on declared rects.

Only reference figures whose target contract selects ``base-art-live-copy``
reach this module. The registered art is the only image; the figure's captured
source lines (the line block that follows it in the page) render as live HTML
on the rectangles its ``base_art_layout`` declares. Rectangles are percentages
of the panel that holds the art: an optional top band of the art's own tone,
then the art. The layout is never measured here, and figure coverage binds its
``art_sha256`` to the frozen asset, as for base-art operation figures.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

_HEX_COLOR_RE = re.compile(r"#[0-9a-f]{6}")


def _css_number(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _percentages(
    raw: Any,
    *,
    count: int,
    field: str,
    source_path: Path,
    error_type: type[Exception],
) -> list[float]:
    if (
        not isinstance(raw, Sequence)
        or isinstance(raw, (str, bytes))
        or len(raw) != count
        or not all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            and 0.0 <= float(item) <= 100.0
            for item in raw
        )
    ):
        raise error_type(
            f"{source_path}: base_art_layout.{field} must be {count} percentages"
        )
    return [float(item) for item in raw]


def _tone(value: Any, *, field: str, source_path: Path, error_type: type[Exception]) -> str:
    tone = str(value or "")
    if not _HEX_COLOR_RE.fullmatch(tone):
        raise error_type(
            f"{source_path}: base_art_layout.{field} must be a measured #rrggbb tone"
        )
    return tone


def arrange_base_art_reference(
    soup: BeautifulSoup,
    *,
    semantic: Tag,
    image: Tag,
    label_block: Tag | None,
    spec: Mapping[str, Any],
    source_path: Path,
    error_type: type[Exception],
) -> None:
    """Place a reference figure's source lines on its declared art rectangles."""

    reference_id = str(spec.get("id") or "")
    layout = spec.get("base_art_layout")
    if not isinstance(layout, Mapping):
        raise error_type(
            f"{source_path}: base-art reference figure {reference_id!r} has no "
            "base_art_layout"
        )
    if label_block is None:
        raise error_type(
            f"{source_path}: base-art reference figure {reference_id!r} has no "
            "captured source lines"
        )
    lines = label_block.find_all(class_="line", recursive=False)
    labels = layout.get("labels")
    if not isinstance(labels, Sequence) or isinstance(labels, (str, bytes)):
        raise error_type(
            f"{source_path}: base_art_layout.labels must place every captured line"
        )
    placed: dict[int, Mapping[str, Any]] = {}
    for label in labels:
        line_index = label.get("line") if isinstance(label, Mapping) else None
        if (
            not isinstance(line_index, int)
            or isinstance(line_index, bool)
            or not 0 <= line_index < len(lines)
            or line_index in placed
        ):
            raise error_type(
                f"{source_path}: base_art_layout.labels must place each of the "
                f"{len(lines)} captured lines of {reference_id!r} exactly once"
            )
        placed[line_index] = label
    if len(placed) != len(lines):
        raise error_type(
            f"{source_path}: base_art_layout.labels must place each of the "
            f"{len(lines)} captured lines of {reference_id!r} exactly once"
        )

    (panel_top,) = _percentages(
        [layout.get("panel_top")],
        count=1,
        field="panel_top",
        source_path=source_path,
        error_type=error_type,
    )
    panel_fill = _tone(
        layout.get("panel_fill"),
        field="panel_fill",
        source_path=source_path,
        error_type=error_type,
    )

    # The art is decorative for assistive technology: the lines it carried in
    # the approved composite are live text on the panel, in source order.
    image["alt"] = ""
    panel = soup.new_tag(
        "div",
        attrs={
            "class": "hb-reference-art-panel",
            "style": (
                f"--hb-panel-top:{_css_number(panel_top)}%;"
                f"--hb-panel-fill:{panel_fill}"
            ),
        },
    )
    image.insert_before(panel)
    panel.append(image.extract())
    for line_index, line in enumerate(lines):
        label = placed[line_index]
        x, y, width, height = _percentages(
            label.get("rect"),
            count=4,
            field=f"labels[line={line_index}].rect",
            source_path=source_path,
            error_type=error_type,
        )
        classes = ["hb-reference-live-label"]
        style = (
            f"--hb-x:{_css_number(x)}%;--hb-y:{_css_number(y)}%;"
            f"--hb-width:{_css_number(width)}%;--hb-height:{_css_number(height)}%"
        )
        if "fill" in label:
            classes.append("hb-reference-live-pill")
            style += ";--hb-fill:" + _tone(
                label.get("fill"),
                field=f"labels[line={line_index}].fill",
                source_path=source_path,
                error_type=error_type,
            )
        span = soup.new_tag(
            "span",
            attrs={
                "class": classes,
                "style": style,
                "data-source-line": str(line_index),
            },
        )
        for child in list(line.contents):
            span.append(child.extract())
        panel.append(span)
    # Every governed line now lives on the panel; nothing is shown twice.
    label_block.decompose()
    if semantic.find(class_="hb-reference-art-panel") is not panel:
        raise error_type(
            f"{source_path}: base-art reference figure {reference_id!r} lost its art"
        )


__all__ = ["arrange_base_art_reference"]
