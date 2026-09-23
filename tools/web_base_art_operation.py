"""Arrange a base-art operation figure: frozen artwork, live copy on declared anchors.

Only figures whose target contract selects ``base-art-live-copy`` reach this
module.  The artwork is never measured here: every anchor comes from the
figure's ``base_art_layout``, and figure coverage binds that layout's
``art_sha256`` to the frozen asset, so a new art version cannot silently reuse
coordinates measured on the old one.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

BASE_ART_CLASS = "hb-base-art-live-copy"
# Compact duration token shown beside a clock, taken from the localized step
# copy the same way the IDML operation panel derives its editable duration.
_DURATION_RE = re.compile(
    r"\b(\d+)\s*(?:seconds?|secondes?|segundos?|s)\b",
    re.IGNORECASE,
)


def _percentages(
    value: Any,
    *,
    count: int,
    field: str,
    source_path: Path,
    error_type: type[Exception],
) -> tuple[float, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != count
        or not all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            and 0.0 <= float(item) <= 100.0
            for item in value
        )
    ):
        raise error_type(
            f"{source_path}: base_art_layout.{field} must be {count} percentages"
        )
    return tuple(float(item) for item in value)


def _css_number(value: float) -> str:
    return f"{value:g}"


def _add_class(tag: Tag, name: str) -> None:
    classes = list(tag.get("class", []))
    if name not in classes:
        tag["class"] = [*classes, name]


def _node_text(node: Any) -> str:
    return node.get_text() if isinstance(node, Tag) else str(node)


def _wrap_contents(soup: BeautifulSoup, line: Tag, class_name: str) -> None:
    wrapper = soup.new_tag("span", attrs={"class": class_name})
    for node in list(line.contents):
        wrapper.append(node.extract())
    line.append(wrapper)


def _split_summary(soup: BeautifulSoup, line: Tag) -> None:
    """Turn ``On: Press once.`` into a label and an instruction, in place.

    The split mirrors the IDML row projection: the first colon separates the
    label from its instruction.  A summary without a top-level colon, or with
    an empty side, stays one instruction so no copy is ever dropped.
    """

    contents = list(line.contents)
    split_at = next(
        (
            index
            for index, node in enumerate(contents)
            if isinstance(node, NavigableString) and ":" in str(node)
        ),
        None,
    )
    if split_at is None:
        _wrap_contents(soup, line, "hb-operation-step-instruction")
        return
    before, _, after = str(contents[split_at]).partition(":")
    label_text = "".join(_node_text(node) for node in contents[:split_at]) + before
    instruction_text = after + "".join(
        _node_text(node) for node in contents[split_at + 1 :]
    )
    if not label_text.strip() or not instruction_text.strip():
        _wrap_contents(soup, line, "hb-operation-step-instruction")
        return
    label = soup.new_tag("span", attrs={"class": "hb-operation-step-label"})
    instruction = soup.new_tag("span", attrs={"class": "hb-operation-step-instruction"})
    for node in contents[:split_at]:
        label.append(node.extract())
    if before.rstrip():
        label.append(before.rstrip())
    contents[split_at].extract()
    if after.lstrip():
        instruction.append(after.lstrip())
    for node in contents[split_at + 1 :]:
        instruction.append(node.extract())
    line.append(label)
    line.append(instruction)


def _mark_step_parts(soup: BeautifulSoup, steps: Tag) -> list[Tag]:
    step_tags = [
        step
        for step in steps.find_all(class_="hb-operation-step", recursive=False)
        if isinstance(step, Tag)
    ]
    for step in step_tags:
        for line in step.find_all(class_="line", recursive=False):
            part = str(line.get("data-step-part") or "")
            if part == "label":
                _add_class(line, "hb-operation-step-label")
            elif part == "instruction":
                _add_class(line, "hb-operation-step-instruction")
            elif part == "summary":
                _split_summary(soup, line)
    return step_tags


def _duration_token(steps: Tag) -> str:
    for step in steps.find_all(class_="hb-operation-step", recursive=False):
        match = _DURATION_RE.search(step.get_text(" ", strip=True))
        if match is not None:
            return f"{match.group(1)}s"
    return ""


def _duration_tag(soup: BeautifulSoup, token: str) -> Tag:
    # A visual shorthand for copy the steps already state, so assistive
    # technology reads the instruction once.
    duration = soup.new_tag(
        "div",
        attrs={"class": "hb-operation-duration", "aria-hidden": "true"},
    )
    duration.append(token)
    return duration


def arrange_base_art_operation(
    soup: BeautifulSoup,
    *,
    figure: Tag,
    stage: Tag,
    spec: Mapping[str, Any],
    source_path: Path,
    error_type: type[Exception],
) -> None:
    """Place live copy on the figure's declared anchors over its frozen art."""

    operation_id = str(spec.get("id") or "")
    layout = spec.get("base_art_layout")
    if not isinstance(layout, Mapping):
        raise error_type(
            f"{source_path}: base-art operation {operation_id!r} has no base_art_layout"
        )
    image = stage.find("img", class_="hb-operation-art")
    if not isinstance(image, Tag):
        raise error_type(f"{source_path}: base-art operation {operation_id!r} has no art")
    steps = stage.find(class_="hb-operation-steps", recursive=False)
    if not isinstance(steps, Tag):
        raise error_type(f"{source_path}: base-art operation {operation_id!r} has no steps")
    prerequisite = stage.find(class_="hb-operation-prerequisite", recursive=False)
    supporting = stage.find(class_="hb-operation-supporting-copy", recursive=False)

    # The live copy carries the instruction; like the approved composite it
    # replaces, the illustration itself is decorative for assistive technology.
    image["alt"] = ""
    # The art box is exactly the art: copy anchored to drawn features lives in
    # it. Steps sit beside it in the canvas, so when they stack under the art on
    # narrow screens they never stretch the box those anchors resolve against.
    canvas = soup.new_tag("div", attrs={"class": "hb-operation-canvas"})
    art_box = soup.new_tag("div", attrs={"class": "hb-operation-art-box"})
    image.insert_before(canvas)
    art_box.append(image.extract())
    canvas.append(art_box)

    if isinstance(prerequisite, Tag):
        x, y, width, height = _percentages(
            layout.get("prerequisite_rect"),
            count=4,
            field="prerequisite_rect",
            source_path=source_path,
            error_type=error_type,
        )
        style = (
            f"--hb-x:{_css_number(x)}%;--hb-y:{_css_number(y)}%;"
            f"--hb-width:{_css_number(width)}%;--hb-height:{_css_number(height)}%"
        )
        if "prerequisite_max_width" in layout:
            # Blank art area a narrow-screen pill may grow into; see the CSS.
            (max_width,) = _percentages(
                [layout.get("prerequisite_max_width")],
                count=1,
                field="prerequisite_max_width",
                source_path=source_path,
                error_type=error_type,
            )
            style += f";--hb-max-width:{_css_number(max_width)}%"
        prerequisite["style"] = style
        art_box.append(prerequisite.extract())

    step_tags = _mark_step_parts(soup, steps)
    if steps.has_attr("style"):
        del steps["style"]
    token = _duration_token(steps)
    variant = str(spec.get("layout") or "")
    if variant == "status-right":
        raw_anchors = layout.get("step_anchors")
        if not isinstance(raw_anchors, Sequence) or len(raw_anchors) != len(step_tags):
            raise error_type(
                f"{source_path}: base_art_layout.step_anchors must name one anchor "
                f"per step for {operation_id!r}"
            )
        (step_width,) = _percentages(
            [layout.get("step_width")],
            count=1,
            field="step_width",
            source_path=source_path,
            error_type=error_type,
        )
        for step, raw_anchor in zip(step_tags, raw_anchors, strict=True):
            x, y = _percentages(
                raw_anchor,
                count=2,
                field="step_anchors[]",
                source_path=source_path,
                error_type=error_type,
            )
            step["style"] = (
                f"--hb-step-x:{_css_number(x)}%;--hb-step-y:{_css_number(y)}%;"
                f"--hb-step-width:{_css_number(step_width)}%"
            )
        canvas.append(steps.extract())
        if "duration_anchor" in layout:
            if not token:
                raise error_type(
                    f"{source_path}: base-art operation {operation_id!r} declares a "
                    "duration anchor but its steps state no duration"
                )
            x, y = _percentages(
                layout.get("duration_anchor"),
                count=2,
                field="duration_anchor",
                source_path=source_path,
                error_type=error_type,
            )
            duration = _duration_tag(soup, token)
            duration["style"] = f"--hb-x:{_css_number(x)}%;--hb-y:{_css_number(y)}%"
            art_box.append(duration)
        footer = None
    elif variant == "footer-overlay":
        (footer_x,) = _percentages(
            [layout.get("footer_x")],
            count=1,
            field="footer_x",
            source_path=source_path,
            error_type=error_type,
        )
        footer = soup.new_tag(
            "div",
            attrs={
                "class": "hb-operation-footer",
                "style": f"--hb-footer-x:{_css_number(footer_x)}%",
            },
        )
        if token:
            footer.append(_duration_tag(soup, token))
        copy = soup.new_tag("div", attrs={"class": "hb-operation-footer-copy"})
        mode_label = str(spec.get("mode_label") or "").strip()
        if mode_label:
            label = soup.new_tag("div", attrs={"class": "hb-operation-mode-label"})
            label.append(mode_label)
            copy.append(label)
        copy.append(steps.extract())
        footer.append(copy)
    else:
        raise error_type(
            f"{source_path}: base-art operation {operation_id!r} has unsupported "
            f"layout {variant!r}"
        )

    # The art, prerequisite and steps already moved into the canvas/footer; any
    # other stage content (the supporting copy today) stays, after them.
    stage.insert(0, canvas)
    if footer is not None:
        canvas.insert_after(footer)
    if isinstance(supporting, Tag) and supporting.parent is stage:
        stage.append(supporting.extract())


__all__ = ["BASE_ART_CLASS", "arrange_base_art_operation"]
