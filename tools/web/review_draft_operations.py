"""Read a rendered operation panel back into its ComponentSpec and Web presentation.

A newer review draft copies the published Web manual, so its operation panels
are the shared operation renderer's own markup. This reader turns that markup
back into the panel's spec (steps, supporting copy, a prerequisite, a footer
mode or SOS label) and into the presentation the renderer reads again,
declared on the spec as ``web_presentation`` the way an authored
``hb-source-operation`` declares it:

- the layout variant (``hb-operation-layout-*``) and the step order;
- on a plain panel, the step and prerequisite rectangles the renderer wrote
  (``--hb-x`` … on each overlay);
- on base art, its ``base_art_layout``: each step's anchor and their shared
  width, the duration and supporting-panel anchors, a prerequisite pill's
  rectangle and tone, the footer offset, or the panel's art width and step
  markers.

The shared renderer replays the read presentation before it is kept. A panel
it cannot replay keeps the plain artwork-and-lines rendering, and the gap is
listed for the release gate. A plain panel replays, but stays listed: its copy
was written for a composite image (the template line's approved carrier), so
its overlay is a card over the art. Only base art places live copy on the
drawing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag

from tools.component_specs.model import ComponentSpec
from tools.component_specs.operation import operation_component_spec
from tools.operation_artwork_mode import BASE_ART_LIVE_COPY
from tools.web.base_art_operation import BASE_ART_CLASS
from tools.web.composite_presentation import WebCompositeContext
from tools.web.operation_component import render_operation_component
from tools.web.presentation import WebPresentationError
from tools.web.review_draft_blocks import (
    DraftChapter,
    attribute,
    classes_of,
    css_variables,
    heading_before,
    inner_html,
    need,
    percent,
    text_of,
)

_PAIR = ("label", "instruction")
_RECT = ("--hb-x", "--hb-y", "--hb-width", "--hb-height")
_MARKER = "hb-operation-marker-"
_PLAIN_PANEL = "a live-copy layout (a plain panel shows its copy on a card over the art; base art places it on the drawing)"


def _line(html: str) -> Tag:
    return need(BeautifulSoup(f'<div class="line">{html}</div>', "html.parser").div, "operation line")


def _strong_label(line: Tag) -> bool:
    """The renderer's own label test: the line's copy is exactly its ``<strong>``."""

    strong = line.find("strong")
    return isinstance(strong, Tag) and line.get_text(" ", strip=True) == strong.get_text(" ", strip=True)


def _summary(line: Tag) -> Tag:
    """A base-art summary, which the renderer split at its first colon, joined again."""

    spans = line.find_all(True, recursive=False)
    split = {name: line.find("span", class_=f"hb-operation-step-{name}", recursive=False) for name in _PAIR}
    loose = "".join(str(text) for text in line.find_all(string=True, recursive=False)).strip()
    instruction, label = split["instruction"], split["label"]
    if instruction is None or loose or len(spans) != (2 if label is not None else 1):
        return line
    joined = inner_html(instruction) if label is None else f"{inner_html(label)}: {inner_html(instruction)}"
    return _line(joined)


def _part(line: Tag) -> dict[str, str]:
    role = attribute(line, "data-step-part") or next(
        (name for name in _PAIR if f"hb-operation-step-{name}" in classes_of(line)), "summary")
    copy = _summary(line) if role == "summary" else line
    html = inner_html(copy)
    if role == "label" and not _strong_label(copy):
        html = f"<strong>{html}</strong>"  # the renderer pairs a step's lines only on a strong label
    return {"role": role, "html": html, "text": text_of(copy)}


def _rect(node: Tag, owner: str, names: tuple[str, ...] = _RECT) -> list[float]:
    style = css_variables(node)
    return [percent(style, name, owner) for name in names]


def _plain_layout(figure: Tag, owner: str) -> dict[str, Any]:
    """A plain panel's overlays, at the rectangles the renderer wrote on them."""

    placed: dict[str, Any] = {}
    for key, selector in (("steps_rect", ".hb-operation-steps"), ("prerequisite_rect", ".hb-operation-prerequisite")):
        node = figure.select_one(selector)
        if node is not None and css_variables(node):
            placed[key] = _rect(node, owner)
    return placed


def _status_right(figure: Tag, owner: str) -> dict[str, Any]:
    styles = [css_variables(step) for step in figure.select(".hb-operation-step")]
    widths = {percent(style, "--hb-step-width", owner) for style in styles}
    if len(widths) != 1:
        raise ValueError(f"{owner}: its steps do not share one width")
    layout: dict[str, Any] = {
        "step_anchors": [[percent(style, name, owner) for name in ("--hb-step-x", "--hb-step-y")] for style in styles],
        "step_width": widths.pop(),
    }
    duration = figure.select_one(".hb-operation-art-box > .hb-operation-duration")
    if duration is not None:
        layout["duration_anchor"] = _rect(duration, owner, ("--hb-x", "--hb-y"))
        if attribute(duration, "data-duration-icon"):
            layout["duration_icon"] = attribute(duration, "data-duration-icon")
    return layout


def _footer_overlay(figure: Tag, owner: str) -> dict[str, Any]:
    footer = need(figure.select_one(".hb-operation-footer"), "operation footer")
    return {"footer_x": percent(css_variables(footer), "--hb-footer-x", owner)}


def _footer_panel(figure: Tag, owner: str) -> dict[str, Any]:
    panel = need(figure.select_one(".hb-operation-panel"), "operation panel")
    markers: list[str] = []
    for step in figure.select(".hb-operation-step"):
        marker = step.find(class_="hb-operation-step-marker", recursive=False)
        kinds = [name.removeprefix(_MARKER) for name in classes_of(marker)
                 if name.startswith(_MARKER)] if isinstance(marker, Tag) else []
        if len(kinds) != 1:
            raise ValueError(f"{owner}: a step shows no marker")
        markers.append(kinds[0])
    return {"art_width": percent(css_variables(panel), "--hb-art-width", owner), "step_markers": markers}


_VARIANT_LAYOUTS = {"status-right": _status_right, "footer-overlay": _footer_overlay, "footer-panel": _footer_panel}


def _base_art_layout(figure: Tag, variant: str, owner: str) -> dict[str, Any]:
    read = _VARIANT_LAYOUTS.get(variant)
    if read is None:
        raise ValueError(f"{owner}: base art has no {variant!r} layout")
    layout = read(figure, owner)
    pill = figure.select_one(".hb-operation-art-box > .hb-operation-prerequisite")
    if pill is not None:
        style = css_variables(pill)
        layout.update(prerequisite_rect=_rect(pill, owner), prerequisite_fill=style.get("--hb-fill", ""))
        if "--hb-max-width" in style:
            layout["prerequisite_max_width"] = percent(style, "--hb-max-width", owner)
    panels = figure.select_one(".hb-operation-supporting-copy.hb-operation-supporting-panels")
    if panels is not None:
        layout["supporting_anchor"] = _rect(panels, owner, ("--hb-x", "--hb-y", "--hb-width"))
    return layout


def _presentation(chapter: DraftChapter, figure: Tag, base: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    owner = f"{chapter.page_id}: operation {base['id']}"
    if {tuple(part["role"] for part in step["parts"]) for step in steps} not in ({_PAIR}, {("summary",)}):
        raise ValueError(f"{owner}: its steps are neither all label and instruction pairs nor all single lines")
    if BASE_ART_CLASS not in classes_of(figure):
        return {**base, **_plain_layout(figure, owner)}
    layout = _base_art_layout(figure, base["layout"], owner)
    return {**base, "presentation_mode": BASE_ART_LIVE_COPY, "base_art_layout": layout}


def _refusal(chapter: DraftChapter, spec: ComponentSpec, carrier: list[Tag], config: dict[str, Any]) -> str:
    """Why the shared renderer refuses to replay ``config``; empty when it replays."""

    context = WebCompositeContext(None, None, None, chapter.language, WebPresentationError)
    try:
        render_operation_component(spec, "".join(str(node) for node in carrier),
                                   source_path=Path(f"{chapter.page_id}.html"), presentation=config,
                                   composites=context)
    except (ValueError, WebPresentationError) as error:
        return str(error)
    return ""


@dataclass
class _Panel:
    """One panel as read: its spec fields, its governed carrier and its base presentation."""

    fields: dict[str, Any]
    base: dict[str, Any]
    steps: list[dict[str, Any]]
    image: Tag
    block: Tag
    carrier: list[Tag]


def _operation_id(chapter: DraftChapter, figure: Tag) -> str:
    callout = attribute(figure.select_one("[data-callout-id]") or figure, "data-callout-id")
    return attribute(figure, "data-operation-id") or (
        callout.split(".")[1] if callout.count(".") >= 2 else f"{chapter.page_id}-operation")


def _lead(figure: Tag) -> Tag | None:
    """The prerequisite paragraph, which the carrier holds just before the art.

    A footer-panel lead shows its opening phrase bold through the first colon,
    which the renderer adds to a plain lead; that bold is undone here.
    """

    pill = figure.select_one(".hb-operation-prerequisite")
    if pill is None or not text_of(pill):
        return None
    lead = need(BeautifulSoup(f"<p>{inner_html(pill.select_one('p') or pill)}</p>", "html.parser").p, "prerequisite")
    opening = next(iter(lead.contents), None)
    if ("hb-operation-lead" in classes_of(pill) and isinstance(opening, Tag) and opening.name == "strong"
            and len(lead.find_all(["strong", "b"])) == 1 and text_of(opening).endswith((":", "\uff1a"))):
        opening.unwrap()
    return lead


def _read_panel(chapter: DraftChapter, figure: Tag) -> _Panel:
    variant = next((name.removeprefix("hb-operation-layout-") for name in classes_of(figure)
                    if name.startswith("hb-operation-layout-")), "")
    art = need(figure.select_one("img.hb-operation-art") or figure.find("img"), "operation artwork")
    operation_id = _operation_id(chapter, figure)
    label = attribute(art, "alt").strip() or heading_before(figure) or operation_id
    steps: list[dict[str, Any]] = [{"id": attribute(step, "data-step-id") or f"step-{index}",
                                    "parts": [_part(line) for line in step.select(".line")]}
                                   for index, step in enumerate(figure.select(".hb-operation-step"), start=1)]
    support = [inner_html(line) for line in figure.select(".hb-operation-supporting-copy .line")]
    lead = _lead(figure)
    shell = BeautifulSoup("", "html.parser")
    image = shell.new_tag("img", attrs={"alt": label, "src": attribute(art, "src")})
    block = shell.new_tag("div", attrs={"class": "line-block"})
    block.extend([_line(part["html"]) for step in steps for part in step["parts"]])
    fields: dict[str, Any] = {
        "operation_id": operation_id, "accessibility_label": label, "layout": variant, "steps": steps,
        "prerequisite_html": str(lead) if lead is not None else "", "supporting_copy": support,
        "artwork_ref": attribute(art, "src"), "source_ref": chapter.source_ref("operation"),
        "language": chapter.language, "artwork_locale_policy": "exact",
        "mode_label": text_of(figure.select_one(".hb-operation-mode-label")),
        "sos_label": text_of(figure.select_one(f".{_MARKER}sos")),
    }
    base = {"id": operation_id, "layout": variant, "step_ids": [step["id"] for step in steps],
            "image_key": f"{chapter.image_key_prefix}/{operation_id}",
            "capture_prerequisite": lead is not None, "capture_following_lines": len(support)}
    carrier = [node for node in (lead, image, block) if node is not None]
    return _Panel(fields=fields, base=base, steps=steps, image=image, block=block, carrier=carrier)


def _presented(chapter: DraftChapter, figure: Tag, panel: _Panel) -> tuple[ComponentSpec | None, str]:
    """The spec declaring the panel's read presentation, or why the renderer cannot replay it."""

    try:
        config = _presentation(chapter, figure, panel.base, panel.steps)
        mode = {"presentation_mode": BASE_ART_LIVE_COPY} if "presentation_mode" in config else {}
        spec = operation_component_spec(**panel.fields, metadata={**mode, "web_presentation": config})
    except ValueError as error:
        return None, str(error)
    refusal = _refusal(chapter, spec, panel.carrier, config)
    return (None, refusal) if refusal else (spec, "")


def _operation(chapter: DraftChapter, figure: Tag) -> None:
    panel = _read_panel(chapter, figure)
    spec, refusal = _presented(chapter, figure, panel)
    # the duration is a shorthand the steps state; mode and SOS labels show only with the layout
    carried = [text_of(node) for node in figure.select(
        ".hb-operation-step .line, .hb-operation-supporting-copy .line, .hb-operation-prerequisite, "
        ".hb-operation-duration")]
    if spec is None:
        # the renderer re-inserts supporting copy from the spec; a plain carrier shows it itself
        panel.block.extend([_line(html) for html in panel.fields["supporting_copy"]])
        spec = operation_component_spec(**panel.fields)
        missing = f"its Web presentation ({refusal})"
    else:
        carried += [text_of(node) for node in figure.select(".hb-operation-mode-label, .hb-operation-step-marker")]
        missing = "" if spec.metadata.get("presentation_mode") else _PLAIN_PANEL
    operation = f"operation {panel.base['id']}"
    if missing:
        chapter.presentation_gaps.append({"page_id": chapter.page_id, "component": operation, "missing": missing})
    chapter.keep_copy(figure, carried, operation)
    figure.replace_with(*panel.carrier)
    chapter.claim(spec, panel.carrier, (("artwork", panel.image),))


def operations(chapter: DraftChapter) -> None:
    for figure in chapter.root.select('[data-component-id="HB-SPECIAL-OPERATION"]'):
        _operation(chapter, figure)


__all__ = ["operations"]
