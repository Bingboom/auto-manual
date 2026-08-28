"""Complete editable fixed-page FCC panel."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..character_metrics import with_character_metrics
from ..fcc_fallback import fcc_spec_from_blocks
from ..page_objects import (
    PANEL_OBJECT_STYLE,
    frame_with_background,
    page_rectangle_xml,
)
from ..params import param_pt
from .fixed_panel_contract import (
    FixedPanelDensity,
    FrameRect,
    normalize_language,
)
from .fixed_panel_primitives import add_story, image_paragraph


ROOT = Path(__file__).resolve().parents[3]
_FCC_LABEL_RE = re.compile(
    r"^(NOTE|REMARQUE|NOTA|MODIFICATION|MODIFICACIÓN|MODIFICACION)\s*:",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class FccPanelData:
    texts: tuple[str, str]

    @classmethod
    def from_blocks(
        cls,
        blocks: list[tuple[str, str]],
        *,
        sid: str,
        language: str,
    ) -> "FccPanelData":
        spec = fcc_spec_from_blocks(
            blocks,
            source_ref=f"idml:fixed-page:{sid}",
            language=language,
        )
        texts = ((spec.get("texts") or []) + ["", ""])[:2]
        return cls((str(texts[0]), str(texts[1])))


@dataclass(frozen=True)
class FccPanelContract:
    density: FixedPanelDensity
    language: str
    frame_rects: tuple[FrameRect, ...]


@dataclass(frozen=True)
class FccPanelRender:
    story_ids: tuple[str, ...]
    frames: tuple[str, ...]
    contract: FccPanelContract


def _labelled_paragraph(text: str) -> tuple[str, str]:
    candidate = text.replace("**", "").strip()
    match = _FCC_LABEL_RE.match(candidate)
    if match is None:
        return "", text.strip()
    label = candidate[:match.end()].strip()
    body = candidate[match.end():].strip()
    kind = (
        "modification"
        if match.group(1).casefold().startswith("modific")
        else "note"
    )
    rebuilt = f"**{label}**"
    if body:
        rebuilt += f" {body}"
    return kind, rebuilt


def _text_paragraphs(text: str) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        label_kind, line = _labelled_paragraph(line)
        if label_kind:
            kind = label_kind
        elif line.startswith(("•", "·")) or line.startswith("- "):
            kind = "list"
        else:
            kind = "body"
        paragraphs.append((kind, line))
    return paragraphs


def _text_story(
    writer,
    sid: str,
    title: str,
    text: str,
    *,
    region: str,
    density: FixedPanelDensity,
) -> str:
    paragraphs = _text_paragraphs(text.strip())
    paragraph_after = param_pt(
        writer.params, "idml_fcc_body_space_after", 1.0,
    )
    list_after = param_pt(writer.params, "idml_fcc_list_space_after", 0.0)
    list_indent = param_pt(writer.params, "idml_fcc_list_left_indent", 3.6)
    modification_before = param_pt(
        writer.params, "idml_fcc_modification_space_before", 1.8,
    )
    font_size = param_pt(
        writer.params,
        "idml_compact_fcc_font_size",
        param_pt(writer.params, "type_fcc_font_size", 5.6),
    )
    font_leading = param_pt(
        writer.params,
        "idml_compact_fcc_font_leading",
        param_pt(writer.params, "type_fcc_font_leading", 6.15),
    )
    horizontal_scale = param_pt(
        writer.params, "idml_compact_fcc_horizontal_scale", 100.0,
    )
    parts: list[str] = []
    for index, (kind, paragraph) in enumerate(paragraphs):
        next_kind = (
            paragraphs[index + 1][0]
            if index + 1 < len(paragraphs)
            else ""
        )
        attrs = ['Hyphenation="false"']
        if kind == "list":
            attrs.extend([
                f'LeftIndent="{list_indent:g}"',
                f'FirstLineIndent="{-list_indent:g}"',
                'RightIndent="0"',
                f'SpaceAfter="{list_after:g}"',
            ])
        elif kind == "modification":
            attrs.append(f'SpaceBefore="{modification_before:g}"')
        elif region != "lead" and next_kind not in {"", "list"}:
            attrs.append(f'SpaceAfter="{paragraph_after:g}"')
        xml = writer._psr(
            "HB FCC Text",
            paragraph,
            terminal=index == len(paragraphs) - 1,
        )
        if density == "compact":
            xml = with_character_metrics(
                xml,
                point_size=font_size,
                leading=font_leading,
                horizontal_scale=horizontal_scale,
            )
        xml = xml.replace(
            "<ParagraphStyleRange ",
            f'<ParagraphStyleRange {" ".join(attrs)} ',
            1,
        )
        parts.append(xml)
    return add_story(writer, sid, title, parts)


def _lead_and_body(text: str) -> tuple[str, str]:
    folded = text.casefold()
    markers = [
        index
        for token in (
            "**note:", "**remarque :", "**remarque:", "**nota:",
            "note:", "remarque :", "remarque:", "nota:",
        )
        if (index := folded.find(token)) >= 40
    ]
    if not markers:
        return "", text.strip()
    marker = min(markers)
    return text[:marker].strip(), text[marker:].strip()


def _text_frame_geometry(language: str) -> tuple[float, float, float]:
    lead_width = 103.0 if language in {"fr", "es"} else 97.0
    lead_height = {"fr": 62.0, "es": 56.0}.get(language, 50.0)
    return lead_width, lead_height, lead_height + 6.0


class FccPanel:
    """Own all stories and internal geometry of one fixed FCC panel."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: FccPanelData,
        language: str,
        density: FixedPanelDensity,
    ) -> None:
        if density not in {"standard", "compact"}:
            raise ValueError(f"unsupported FCC panel density: {density}")
        self.writer = writer
        self.sid = sid
        self.data = data
        self.language = normalize_language(language)
        self.density = density

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> FccPanelRender:
        writer = self.writer
        sid = self.sid
        texts = self.data.texts
        mark = ROOT / "docs" / "renderers" / "latex" / "assets" / "fcc_mark.png"
        mark_sid = f"{sid}_fcc_mark"
        emitted_story_ids: list[str] = []
        if mark.exists():
            add_story(
                writer,
                mark_sid,
                "FCC mark",
                [image_paragraph(writer, f"{mark_sid}_image", mark, 39.5)],
            )
            emitted_story_ids.append(mark_sid)

        lead_text, left_text = _lead_and_body(texts[0])
        lead_sid = f"{sid}_fcc_lead"
        if lead_text:
            _text_story(
                writer,
                lead_sid,
                "FCC notice lead",
                lead_text,
                region="lead",
                density=self.density,
            )
            emitted_story_ids.append(lead_sid)
        left_sid = f"{sid}_fcc_left"
        right_sid = f"{sid}_fcc_right"
        _text_story(
            writer,
            left_sid,
            "FCC notice left",
            left_text,
            region="left",
            density=self.density,
        )
        _text_story(
            writer,
            right_sid,
            "FCC notice right",
            texts[1],
            region="right",
            density=self.density,
        )
        emitted_story_ids.extend((left_sid, right_sid))

        panel_rect = (x, y, width, available_height)
        frames = [page_rectangle_xml(
            writer,
            f"bg_{sid}_fcc_panel",
            panel_rect,
            fill="Color/HB Bg K05",
            stroke_color="Swatch/None",
            stroke_weight=0,
            object_style=PANEL_OBJECT_STYLE,
        )]
        frame_rects: list[FrameRect] = [("panel", panel_rect)]
        if mark.exists():
            mark_rect = (x + 6.0, y + 7.0, 42.0, 34.0)
            frames.append(frame_with_background(
                writer,
                sid,
                "fcc_mark",
                mark_sid,
                mark_rect,
                {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
            ))
            frame_rects.append(("mark", mark_rect))
        if lead_text:
            lead_width, lead_height, left_y_offset = _text_frame_geometry(
                self.language,
            )
            lead_rect = (x + 52.0, y + 8.0, lead_width, lead_height)
            frames.append(frame_with_background(
                writer,
                sid,
                "fcc_lead",
                lead_sid,
                lead_rect,
                {"inset": (0, 0, 0, 0)},
            ))
            frame_rects.append(("lead", lead_rect))
        else:
            left_y_offset = 56.0
        left_rect = (
            x + 6.4,
            y + left_y_offset,
            150.0,
            available_height - left_y_offset,
        )
        right_rect = (
            x + 166.8,
            y + 8.0,
            width - 172.8,
            available_height - 8.0,
        )
        frames.extend([
            frame_with_background(
                writer,
                sid,
                "fcc_left",
                left_sid,
                left_rect,
                {"inset": (0, 0, 0, 0)},
            ),
            frame_with_background(
                writer,
                sid,
                "fcc_right",
                right_sid,
                right_rect,
                {"inset": (0, 0, 0, 0)},
            ),
        ])
        frame_rects.extend((("left", left_rect), ("right", right_rect)))
        return FccPanelRender(
            story_ids=tuple(emitted_story_ids),
            frames=tuple(frames),
            contract=FccPanelContract(
                density=self.density,
                language=self.language,
                frame_rects=tuple(frame_rects),
            ),
        )


__all__ = ["FccPanel", "FccPanelContract", "FccPanelData", "FccPanelRender"]
