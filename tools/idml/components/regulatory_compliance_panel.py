"""Editable bottom-card regulatory composition shared by target assemblies."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

from ..page_objects import capsule_opts, frame_with_background, heading_text
from ..params import param_pt
from ..source_copy import source_text
from .fixed_panel_contract import FrameRect, normalize_language
from .fixed_panel_primitives import apply_character_attrs


@dataclass(frozen=True)
class RegulatoryCompliancePanelData:
    title: str
    declaration_heading: str
    declaration_copy: str
    manufacturer_heading: str
    company: str
    address: str
    contacts: tuple[str, ...]

    @classmethod
    def from_blocks(
        cls,
        blocks: list[tuple[str, str]],
    ) -> "RegulatoryCompliancePanelData":
        title = source_text(
            next((text for kind, text in blocks if kind == "h1"), ""),
            owner="Regulatory page title",
        )
        h2_indices = [
            index for index, (kind, _text) in enumerate(blocks)
            if kind == "h2"
        ]
        if not title or len(h2_indices) != 2:
            raise ValueError(
                "regulatory_compliance requires one H1 and two H2 sections"
            )
        first_h2, second_h2 = h2_indices
        declaration = [
            source_text(text, owner="Regulatory declaration copy")
            for kind, text in blocks[first_h2 + 1:second_h2]
            if kind == "body"
        ]
        manufacturer = [
            source_text(text, owner="Regulatory manufacturer copy")
            for kind, text in blocks[second_h2 + 1:]
            if kind == "body"
        ]
        if not declaration or len(manufacturer) < 3:
            raise ValueError(
                "regulatory_compliance requires declaration, company, address, "
                "and contact source blocks"
            )
        contacts = tuple(
            line.strip()
            for line in manufacturer[-1].splitlines()
            if line.strip()
        )
        if len(contacts) != 3:
            raise ValueError(
                "regulatory_compliance requires phone, email, and web contacts"
            )
        return cls(
            title=title,
            declaration_heading=source_text(
                blocks[first_h2][1], owner="Regulatory declaration heading"
            ),
            declaration_copy=" ".join(declaration),
            manufacturer_heading=source_text(
                blocks[second_h2][1], owner="Regulatory manufacturer heading"
            ),
            company=manufacturer[0],
            address=" ".join(manufacturer[1:-1]),
            contacts=contacts,
        )


@dataclass(frozen=True)
class RegulatoryCompliancePanelContract:
    language: str
    layout_variant: str = "bottom_card"
    contact_count: int = 3
    has_qr: bool = False


@dataclass(frozen=True)
class RegulatoryCompliancePanelRender:
    story_ids: tuple[str, ...]
    frames: tuple[str, ...]
    frame_rects: tuple[FrameRect, ...]
    contract: RegulatoryCompliancePanelContract


def _styled_psr(
    writer,
    text: str,
    *,
    point_size: float,
    leading: float,
    bold: bool = False,
    horizontal_scale: float = 100.0,
) -> str:
    attrs = (
        f'PointSize="{point_size:g}" Leading="{leading:g}" '
        f'HorizontalScale="{horizontal_scale:g}"'
    )
    if bold:
        attrs += ' FontStyle="Bold"'
    return apply_character_attrs(
        writer._psr("HB Body", text, terminal=True),
        attrs,
    )


def _graphic_frame(
    writer,
    *,
    frame_id: str,
    asset: Path,
    rect: tuple[float, float, float, float],
) -> str:
    if not asset.is_file():
        raise ValueError(f"regulatory QR asset is missing: {asset}")
    x1, y1, x2, y2 = writer._page_rect(*rect)
    uri = escape(asset.resolve().as_uri(), quote=True)
    return (
        f'  <Rectangle Self="{frame_id}" ContentType="GraphicType" '
        'AppliedObjectStyle="ObjectStyle/$ID/[None]" '
        'StrokeColor="Swatch/None" StrokeWeight="0" '
        'ItemTransform="1 0 0 1 0 0">\n'
        + writer._path_geometry(x1, y1, x2, y2)
        + f'    <Image Self="{frame_id}_img" '
        f'ItemTransform="1 0 0 1 {x1:g} {y1:g}">\n'
        f'      <Link Self="{frame_id}_lnk" LinkResourceURI="{uri}"/>\n'
        '    </Image>\n'
        '    <FrameFittingOption FittingOnEmptyFrame="Proportionally" '
        'FittingAlignment="CenterAnchor" AutoFit="true"/>\n'
        '  </Rectangle>\n'
    )


class RegulatoryCompliancePanel:
    """Own the compact bottom-card geometry without target/model branches."""

    def __init__(
        self,
        writer,
        *,
        sid: str,
        data: RegulatoryCompliancePanelData,
        language: str,
        qr_asset: Path | None = None,
    ) -> None:
        self.writer = writer
        self.sid = sid
        self.data = data
        self.language = normalize_language(language)
        self.qr_asset = qr_asset

    def render(
        self,
        *,
        x: float,
        y: float,
        width: float,
        available_height: float,
    ) -> RegulatoryCompliancePanelRender:
        if available_height <= 125.0:
            raise ValueError("regulatory bottom card has insufficient height")
        writer = self.writer
        title_sid = f"{self.sid}_title"
        declaration_sid = f"{self.sid}_declaration"
        manufacturer_sid = f"{self.sid}_manufacturer"
        ce_sid = f"{self.sid}_ce"
        contact_sids = tuple(
            f"{self.sid}_contact_{index}" for index in range(3)
        )

        title_size = param_pt(
            writer.params, "idml_regulatory_title_font_size", 7.5
        )
        writer._add_story_parts(
            title_sid,
            self.data.title,
            [
                heading_text(
                    writer,
                    self.data.title,
                    level=2,
                    point_size=title_size,
                )
            ],
        )
        writer._add_story_parts(
            declaration_sid,
            self.data.declaration_heading,
            [
                _styled_psr(
                    writer,
                    self.data.declaration_heading,
                    point_size=6.7,
                    leading=7.2,
                    bold=True,
                ),
                _styled_psr(
                    writer,
                    self.data.declaration_copy,
                    point_size=5.6,
                    leading=6.1,
                    horizontal_scale=97.0,
                ),
            ],
        )
        writer._add_story_parts(
            manufacturer_sid,
            self.data.manufacturer_heading,
            [
                _styled_psr(
                    writer,
                    f"{self.data.manufacturer_heading} {self.data.company}",
                    point_size=6.5,
                    leading=7.0,
                    bold=True,
                    horizontal_scale=95.0,
                ),
                _styled_psr(
                    writer,
                    self.data.address,
                    point_size=5.2,
                    leading=5.8,
                    horizontal_scale=96.0,
                ),
            ],
        )
        writer._add_story_parts(
            ce_sid,
            "CE",
            [
                _styled_psr(
                    writer,
                    "CE",
                    point_size=27.0,
                    leading=27.0,
                    bold=True,
                    horizontal_scale=86.0,
                )
            ],
        )
        contact_icons = ("☎", "✉", "◉")
        for story_id, icon, contact in zip(
            contact_sids,
            contact_icons,
            self.data.contacts,
            strict=True,
        ):
            writer._add_story_parts(
                story_id,
                contact,
                [
                    _styled_psr(
                        writer,
                        f"{icon} {contact}",
                        point_size=5.8,
                        leading=6.4,
                        horizontal_scale=95.0,
                    )
                ],
            )

        title_rect = (
            x,
            y,
            param_pt(writer.params, "idml_regulatory_title_width", 78.0),
            param_pt(writer.params, "idml_regulatory_title_height", 13.0),
        )
        declaration_rect = (x, y + 17.5, width - 42.0, 59.0)
        manufacturer_rect = (x, y + 80.0, width - 42.0, 39.0)
        ce_rect = (x + width - 36.0, y - 4.0, 36.0, 30.0)
        contact_widths = (80.0, 98.0, width - 178.0)
        contact_x = (x, x + 80.0, x + 178.0)
        contact_rects = tuple(
            (left, y + 120.0, contact_width, 10.5)
            for left, contact_width in zip(
                contact_x,
                contact_widths,
                strict=True,
            )
        )
        frames = [
            frame_with_background(
                writer,
                self.sid,
                "regulatory_title",
                title_sid,
                title_rect,
                {
                    **capsule_opts((1.0, 5.0, 1.0, 5.0)),
                    "text_rect": (
                        title_rect[0] + 5.0,
                        title_rect[1],
                        title_rect[2] - 10.0,
                        title_rect[3],
                    ),
                },
            ),
            frame_with_background(
                writer,
                self.sid,
                "regulatory_declaration",
                declaration_sid,
                declaration_rect,
                {"inset": (0, 0, 0, 0)},
            ),
            frame_with_background(
                writer,
                self.sid,
                "regulatory_manufacturer",
                manufacturer_sid,
                manufacturer_rect,
                {"inset": (0, 0, 0, 0)},
            ),
            frame_with_background(
                writer,
                self.sid,
                "regulatory_ce",
                ce_sid,
                ce_rect,
                {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
            ),
        ]
        for index, (story_id, rect) in enumerate(
            zip(contact_sids, contact_rects, strict=True)
        ):
            frames.append(
                frame_with_background(
                    writer,
                    self.sid,
                    f"regulatory_contact_{index}",
                    story_id,
                    rect,
                    {"inset": (0, 0, 0, 0), "valign": "CenterAlign"},
                )
            )
        frame_rects: list[FrameRect] = [
            ("title", title_rect),
            ("declaration", declaration_rect),
            ("manufacturer", manufacturer_rect),
            ("ce", ce_rect),
            *[
                (f"contact_{index}", rect)
                for index, rect in enumerate(contact_rects)
            ],
        ]
        if self.qr_asset is not None:
            qr_rect = (x + width - 38.0, y + 93.0, 38.0, 38.0)
            frames.append(
                _graphic_frame(
                    writer,
                    frame_id=f"rc_{self.sid}_qr",
                    asset=self.qr_asset,
                    rect=qr_rect,
                )
            )
            frame_rects.append(("qr", qr_rect))
        return RegulatoryCompliancePanelRender(
            story_ids=(
                title_sid,
                declaration_sid,
                manufacturer_sid,
                ce_sid,
                *contact_sids,
            ),
            frames=tuple(frames),
            frame_rects=tuple(frame_rects),
            contract=RegulatoryCompliancePanelContract(
                language=self.language,
                has_qr=self.qr_asset is not None,
            ),
        )


__all__ = [
    "RegulatoryCompliancePanel",
    "RegulatoryCompliancePanelContract",
    "RegulatoryCompliancePanelData",
    "RegulatoryCompliancePanelRender",
]
