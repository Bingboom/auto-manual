"""Complete editable title, card, badge, and TIP panel for box contents."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from tools.component_specs.inbox import inbox_spec_from_payload
from tools.component_specs.inbox_adapters import idml_inbox_payload

from ..fcc_fallback import component_spec
from ..page_objects import (
    BADGE_OBJECT_STYLE,
    CARD_OBJECT_STYLE,
    PANEL_OBJECT_STYLE,
    frame_with_background,
    h1_frame_opts,
    heading_text,
    left_rounded_xml,
    page_rectangle_xml,
)
from ..params import param_pt, param_text
from .fixed_panel_contract import (
    FixedPanelDensity,
    FrameRect,
    normalize_language,
)
from .fixed_panel_primitives import (
    add_story,
    apply_character_attrs,
    centered_psr,
    image_paragraph,
)
from .notice import notice_box_layout, source_notice_label


TITLE_HEIGHT = 20.0
BADGE_DIAMETER = 13.785
BADGE_Y_OFFSET = 22.431
_LEGACY_IMAGE = re.compile(r"\.\.\s+image::\s+(\S+)")
_LEGACY_LABEL = re.compile(r"\*\*(.+?)\*\*")


def _legacy_inbox_payload(blocks: list[tuple[str, str]]) -> dict | None:
    """Adapt a three-cell RST list-table into the shared Inbox ComponentSpec."""

    raw = next((text for kind, text in blocks if kind == "table"), None)
    if raw is None:
        return None
    try:
        rows = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(rows, list) or len(rows) != 1 or len(rows[0]) != 3:
        return None
    items: list[dict[str, str]] = []
    for cell in rows[0]:
        image = _LEGACY_IMAGE.search(str(cell))
        label = _LEGACY_LABEL.search(str(cell))
        if image is None or label is None:
            return None
        items.append({
            "img": image.group(1),
            "label": label.group(1).strip(),
            "alt": label.group(1).strip(),
        })
    return {"kind": "inbox", "items": items}


@dataclass(frozen=True)
class InboxPanelData:
    title: str
    has_inbox: bool
    items: tuple[dict, ...]
    tip_spec: dict | None
    reference_profile: dict

    @classmethod
    def from_blocks(
        cls,
        blocks: list[tuple[str, str]],
        *,
        sid: str,
        language: str,
        density: FixedPanelDensity,
        reference_profile: dict | None = None,
    ) -> "InboxPanelData":
        title = next((
            text.strip()
            for kind, text in blocks
            if kind == "h1" and text.strip()
        ), "")
        if not title:
            raise ValueError("inbox title is required from source RST")
        inbox_spec = component_spec(blocks, "inbox") or _legacy_inbox_payload(blocks)
        tip_spec = component_spec(blocks, "notice")
        profile = dict(reference_profile or {})
        layout_variant = str(profile.get("layout_variant") or "").strip()
        if layout_variant and layout_variant != "compact_with_tip":
            raise ValueError(f"unsupported Inbox layout variant: {layout_variant}")
        require_tip = density == "standard" or layout_variant == "compact_with_tip"
        if inbox_spec is not None and require_tip and tip_spec is None:
            raise ValueError("inbox tip is required from source RST")
        items: tuple[dict, ...] = ()
        if inbox_spec is not None:
            tip_label = source_notice_label(tip_spec) if tip_spec else ""
            tip_body = "\n".join(
                str(value).strip()
                for value in (tip_spec or {}).get("texts", [])
                if str(value).strip()
            )
            payload = idml_inbox_payload(inbox_spec_from_payload(
                inbox_spec,
                source_ref=f"idml:page03:{sid}",
                language=language,
                accessibility_label=title,
                tip_label=tip_label,
                tip_body=tip_body,
                require_tip=require_tip,
            ))
            items = tuple(dict(item) for item in payload.get("items", [])[:3])
        return cls(
            title=title,
            has_inbox=inbox_spec is not None,
            items=items,
            tip_spec=tip_spec if require_tip else None,
            reference_profile=profile,
        )


@dataclass(frozen=True)
class InboxPanelContract:
    density: FixedPanelDensity
    language: str
    profile: str
    frame_rects: tuple[FrameRect, ...]


@dataclass(frozen=True)
class InboxPanelRender:
    story_ids: tuple[str, ...]
    frames: tuple[str, ...]
    contract: InboxPanelContract


def _badge_text(number: int) -> str:
    return centered_psr(
        "HB InBox Label",
        str(number),
        character_attrs=(
            'FillColor="Color/Paper" PointSize="10.912" '
            'FontStyle="Medium" BaselineShift="0.45"'
        ),
    )


def _card_story(
    writer,
    sid: str,
    item: dict,
    bundle_root: Path,
    max_image_width: float,
    *,
    image_space_after: float = 0.0,
) -> str:
    parts: list[str] = []
    image = writer._resolve_bundle_image(bundle_root, item.get("img", ""))
    if image is not None:
        parts.append(image_paragraph(
            writer,
            f"{sid}_img",
            image,
            max_image_width,
            space_after=image_space_after,
        ))
    parts.append(writer._psr(
        "HB InBox Label",
        item.get("label", ""),
        terminal=True,
    ))
    return add_story(writer, sid, "Inbox card", parts)


def _tip_label(
    label: str,
    *,
    point_size: float,
    leading: float,
    baseline_shift: float,
) -> str:
    return centered_psr(
        "HB Callout Label",
        label.strip(),
        character_attrs=(
            f'PointSize="{point_size:g}" Leading="{leading:g}" '
            f'FontStyle="Bold" BaselineShift="{baseline_shift:g}"'
        ),
    )


class InboxPanel:
    """Own all internal Inbox geometry; callers assign only its rectangle."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: InboxPanelData,
        bundle_root: Path,
        language: str,
        density: FixedPanelDensity,
        overflow_profile: bool = False,
    ) -> None:
        if density not in {"standard", "compact"}:
            raise ValueError(f"unsupported Inbox panel density: {density}")
        self.writer = writer
        self.sid = sid
        self.data = data
        self.bundle_root = bundle_root
        self.language = normalize_language(language)
        self.density = density
        self.overflow_profile = overflow_profile and density == "standard"
        self._title_sid: str | None = None

    @property
    def profile(self) -> str:
        if self.density == "compact":
            return "compact_"
        if self.overflow_profile:
            return "overflow_"
        return ""

    @property
    def layout_variant(self) -> str:
        return str(self.data.reference_profile.get("layout_variant") or "").strip()

    def _metric(self, name: str, fallback: float) -> float:
        key = f"idml_inbox_{self.profile}{name}"
        return param_pt(
            self.writer.params,
            f"lang_{self.language}_{key}",
            param_pt(self.writer.params, key, fallback),
        )

    def _baseline_title_y(self) -> float:
        if self.density == "compact":
            return param_pt(
                self.writer.params,
                "idml_compact_inbox_title_y",
                174.0,
            )
        if self.overflow_profile:
            return param_pt(
                self.writer.params,
                f"lang_{self.language}_idml_fcc_inbox_overflow_title_y",
                param_pt(
                    self.writer.params,
                    "idml_fcc_inbox_overflow_title_y",
                    245.0,
                ),
            )
        return 245.0

    def add_title_story(self) -> str:
        if self._title_sid is not None:
            return self._title_sid
        title_sid = (
            f"{self.sid}_inbox_title"
            if self.density == "compact"
            else f"{self.sid}_title"
        )
        story_title = self.data.title if self.density == "compact" else "Inbox title"
        add_story(
            self.writer,
            title_sid,
            story_title,
            [heading_text(self.writer, self.data.title, level=1)],
        )
        self._title_sid = title_sid
        return title_sid

    def _title_frame(
        self,
        *,
        x: float,
        y: float,
        width: float,
    ) -> tuple[str, FrameRect]:
        title_sid = self.add_title_story()
        rect = (x, y, width, TITLE_HEIGHT)
        if self.density == "compact":
            frame_name = "inbox_title"
        else:
            frame_name = "title"
        opts = h1_frame_opts(
            rect,
            left_inset=6.0 if self.density == "compact" else 6.4,
            right_inset=6.0 if self.density == "compact" else 6.4,
        )
        return (
            frame_with_background(
                self.writer,
                self.sid,
                frame_name,
                title_sid,
                rect,
                opts,
            ),
            ("title", rect),
        )

    def _card_objects(
        self,
        *,
        x: float,
        y: float,
        width: float,
    ) -> tuple[list[str], list[str], list[FrameRect]]:
        baseline_title_y = self._baseline_title_y()
        card_width = 99.5
        card_height = self._metric("card_height", 172.5)
        card_y = y + self._metric("card_y", 273.0) - baseline_title_y
        card_xs = (x, x + 106.0, x + 211.5)
        governed_widths = (
            (self.data.reference_profile.get("image_width_pt_by_language") or {})
            .get(self.language)
        )
        if governed_widths is not None and (
            not isinstance(governed_widths, list)
            or len(governed_widths) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or float(value) <= 0
                for value in governed_widths
            )
        ):
            raise ValueError(
                "inbox image widths must contain three positive numbers for "
                f"{self.language}"
            )
        image_widths = (
            tuple(float(value) for value in governed_widths)
            if governed_widths
            else (
                self._metric("image_1_width", 72.0),
                self._metric("image_2_width", 60.0),
                self._metric("image_3_width", 58.0),
            )
        )
        image_space_after = tuple(
            self._metric(f"card_{index}_image_space_after", fallback)
            for index, fallback in enumerate((12.6, 10.2, 19.2), start=1)
        )
        content_y_offsets = tuple(
            self._metric(f"card_{index}_content_y_offset", fallback)
            for index, fallback in enumerate((-3.9, -7.5, -8.4), start=1)
        )
        content_height = self._metric("content_height", card_height - 44.5)
        badge_y_offset = self._metric("badge_y_offset", BADGE_Y_OFFSET)
        stroke_color = str(
            self.data.reference_profile.get("stroke_color")
            or param_text(
                self.writer.params,
                f"idml_inbox_{self.profile}stroke_color",
                "Color/HB Line K40",
            )
        )
        stroke_weight = float(self.data.reference_profile.get(
            "stroke_weight",
            self._metric("stroke_weight", 0.75),
        ))
        story_ids: list[str] = []
        frames: list[str] = []
        frame_rects: list[FrameRect] = []
        for index, item in enumerate(self.data.items):
            card_x = card_xs[index]
            card_rect = (card_x, card_y, card_width, card_height)
            frames.append(page_rectangle_xml(
                self.writer,
                f"bg_{self.sid}_card_{index + 1}",
                card_rect,
                fill="Color/Paper",
                stroke_color=stroke_color,
                stroke_weight=stroke_weight,
                object_style=CARD_OBJECT_STYLE,
            ))
            frame_rects.append((f"card_{index + 1}_shell", card_rect))

            badge_rect = (
                card_x + card_width / 2.0 - BADGE_DIAMETER / 2.0,
                card_y + badge_y_offset,
                BADGE_DIAMETER,
                BADGE_DIAMETER,
            )
            frames.append(page_rectangle_xml(
                self.writer,
                f"bg_{self.sid}_badge_{index + 1}",
                badge_rect,
                fill="Color/HB Brand Dark",
                stroke_color="Swatch/None",
                stroke_weight=0,
                corner_radius=BADGE_DIAMETER / 2.0,
                object_style=BADGE_OBJECT_STYLE,
            ))
            frame_rects.append((f"badge_{index + 1}_shell", badge_rect))

            badge_sid = f"{self.sid}_badge_{index + 1}"
            add_story(
                self.writer,
                badge_sid,
                f"Inbox badge {index + 1}",
                [_badge_text(index + 1)],
            )
            story_ids.append(badge_sid)
            frames.append(frame_with_background(
                self.writer,
                self.sid,
                f"badge_{index + 1}",
                badge_sid,
                badge_rect,
                {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
            ))

            card_sid = f"{self.sid}_card_{index + 1}"
            _card_story(
                self.writer,
                card_sid,
                item,
                self.bundle_root,
                image_widths[index],
                image_space_after=image_space_after[index],
            )
            story_ids.append(card_sid)
            content_rect = (
                card_x + 8.0,
                card_y + 36.0 + content_y_offsets[index],
                card_width - 16.0,
                content_height,
            )
            frames.append(frame_with_background(
                self.writer,
                self.sid,
                f"card_{index + 1}",
                card_sid,
                content_rect,
                {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
            ))
            frame_rects.append((f"card_{index + 1}_content", content_rect))
        return story_ids, frames, frame_rects

    def _tip_objects(
        self,
        *,
        x: float,
        y: float,
        width: float,
    ) -> tuple[list[str], list[str], list[FrameRect]]:
        if not self.data.tip_spec:
            return [], [], []
        label = source_notice_label(self.data.tip_spec)
        texts = [
            str(text).strip()
            for text in self.data.tip_spec.get("texts", [])
            if str(text).strip()
        ]
        body = "\n".join(texts)
        layout = notice_box_layout(
            self.writer.params,
            width,
            label,
            texts,
            variant=str(self.data.tip_spec.get("variant", "")),
        )
        baseline_title_y = self._baseline_title_y()
        tip_y = y + self._metric("tip_y", 458.0) - baseline_title_y
        tip_height = self._metric("tip_height", layout.panel_height)
        tip_label_width = self._metric("tip_label_width", layout.plate_width)
        tip_rect = (x, tip_y, width, tip_height)
        plate_rect = (
            x + layout.plate_left,
            tip_y + layout.plate_left,
            tip_label_width,
            tip_height - 2 * layout.plate_left,
        )
        body_x = x + layout.plate_left + tip_label_width + layout.body_inset
        body_rect = (
            body_x,
            tip_y + layout.pad_tb,
            x + width - layout.right_inset - body_x,
            tip_height - 2 * layout.pad_tb,
        )
        label_sid = f"{self.sid}_tip_label"
        body_sid = f"{self.sid}_tip_body"
        add_story(self.writer, label_sid, "Inbox tip label", [_tip_label(
            label,
            point_size=layout.label_size,
            leading=layout.label_leading,
            baseline_shift=layout.label_baseline_shift,
        )])
        body_xml = apply_character_attrs(
            self.writer._psr(
                "HB Callout Body",
                body,
                terminal=True,
            ),
            f'PointSize="{layout.body_size:g}" '
            f'Leading="{layout.body_leading:g}" FontStyle="Medium" '
            f'HorizontalScale="{layout.body_horizontal_scale * 100:g}" '
            f'BaselineShift="{layout.body_baseline_shift:g}"',
        )
        add_story(self.writer, body_sid, "Inbox tip body", [body_xml])
        frames = [
            page_rectangle_xml(
                self.writer,
                f"bg_{self.sid}_tip_strip",
                tip_rect,
                fill="Color/HB Bg K05",
                stroke_color="Swatch/None",
                stroke_weight=0,
                corner_radius=layout.arc,
                object_style=PANEL_OBJECT_STYLE,
            ),
            left_rounded_xml(
                self.writer,
                f"bg_{self.sid}_tip_label",
                plate_rect,
                fill="Color/Paper",
                corner_radius=max(
                    0.0,
                    layout.arc - layout.plate_left / 2.0,
                ),
                object_style=PANEL_OBJECT_STYLE,
            ),
            frame_with_background(
                self.writer,
                self.sid,
                "tip_label",
                label_sid,
                plate_rect,
                {"inset": (0, 0, 0, 1.0), "valign": "CenterAlign"},
            ),
            frame_with_background(
                self.writer,
                self.sid,
                "tip_body",
                body_sid,
                body_rect,
                {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
            ),
        ]
        return (
            [label_sid, body_sid],
            frames,
            [
                ("tip_shell", tip_rect),
                ("tip_label", plate_rect),
                ("tip_body", body_rect),
            ],
        )

    def render_body(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> InboxPanelRender:
        del available_height  # The legacy contract is fully token-measured.
        title_sid = self.add_title_story()
        title_frame, title_rect = self._title_frame(x=x, y=y, width=width)
        card_story_ids, card_frames, card_rects = self._card_objects(
            x=x,
            y=y,
            width=width,
        )
        tip_story_ids, tip_frames, tip_rects = self._tip_objects(
            x=x,
            y=y,
            width=width,
        )
        return InboxPanelRender(
            story_ids=(title_sid, *card_story_ids, *tip_story_ids),
            frames=(title_frame, *card_frames, *tip_frames),
            contract=InboxPanelContract(
                density=self.density,
                language=self.language,
                profile=self.layout_variant or self.profile.rstrip("_"),
                frame_rects=(title_rect, *card_rects, *tip_rects),
            ),
        )

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> InboxPanelRender:
        self.add_title_story()
        return self.render_body(
            x=x,
            y=y,
            width=width,
            available_height=available_height,
        )


__all__ = [
    "InboxPanel",
    "InboxPanelContract",
    "InboxPanelData",
    "InboxPanelRender",
]
