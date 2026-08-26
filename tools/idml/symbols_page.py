"""Meaning-of-symbols and combined safety-symbol page assemblers."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from xml.sax.saxutils import escape

from .language_contract import governed_languages
from .character_metrics import (
    fit_symbol_body_metrics,
    signal_label_metrics,
    with_character_metrics,
)
from .layout_est import est_table_height
from .params import IDPKG, component_param_pt, param_pt
from .style_names import paragraph_style_ref

ROOT = Path(__file__).resolve().parents[2]
SYMBOL_ICON_ART_SCALE = 0.9


def _symbol_icon_asset(figure: str | None) -> Path | None:
    """Resolve a symbol image, correcting the known WEEE source crop.

    The phase2 ``11_weee_*`` attachment contains the same artwork on a
    shifted, over-tall canvas.  That canvas makes proportional fitting shrink
    and offset the symbol inside the editable cell.  The shared template asset
    uses the stable geometry with the artwork restored to the same dark tone
    as the other symbol assets.
    """
    if not figure:
        return None
    source = Path(figure)
    if source.name.casefold().startswith("11_weee_"):
        canonical = ROOT / "docs" / "templates" / "word_template" / "common_assets" / "symbols" / "weee.png"
        if canonical.is_file():
            return canonical
    return source


@dataclass(frozen=True)
class SafetySymbolsPageStyle:
    """Token-driven vertical contract for the combined maintenance page."""

    page_top: float
    first_tail_height: float
    first_tail_gap: float
    second_tail_height: float
    second_tail_gap: float
    maintenance_body_height: float
    maintenance_body_gap: float
    signal_header_height: float
    signal_row_height: float
    signal_gap_after: float
    icon_header_height: float
    icon_row_height: float
    icon_last_row_height: float
    icon_long_last_row_height: float
    subbar_height: float
    maintenance_title_gap: float
    symbols_title_gap: float
    h1_optical_offset: float
    page_bottom_allowance: float
    table_frame_allowance: float
    fallback_import_allowance: float
    fallback_min_height: float
    fallback_text_width_ratio: float
    fallback_row_height: float

    @classmethod
    def from_writer(cls, writer, language: str) -> "SafetySymbolsPageStyle":
        normalized = language.split("-", 1)[0]

        def token(key: str, default: float) -> float:
            return component_param_pt(
                writer.params,
                key,
                default,
                strict=writer.strict_component_assets,
                owner="safety symbols page",
            )

        def localized(key: str, default: float) -> float:
            base = token(key, default)
            if normalized not in governed_languages():
                return base
            return token(f"lang_{normalized}_{key}", base)

        return cls(
            page_top=localized("idml_symbols_page_top", 27.7),
            first_tail_height=localized("idml_symbols_first_tail_height", 34.5),
            first_tail_gap=localized("idml_symbols_first_tail_gap", 4.4),
            second_tail_height=localized("idml_symbols_second_tail_height", 28.5),
            second_tail_gap=localized("idml_symbols_second_tail_gap", 6.8),
            maintenance_body_height=localized(
                "idml_symbols_maintenance_body_height", 21.5,
            ),
            maintenance_body_gap=localized(
                "idml_symbols_maintenance_body_gap", 0.0,
            ),
            signal_header_height=token(
                "idml_symbols_signal_header_height", 17.3,
            ),
            signal_row_height=token("idml_symbols_signal_row_height", 25.42),
            signal_gap_after=localized("idml_symbols_signal_gap_after", 4.1),
            icon_header_height=token("idml_symbols_icon_header_height", 15.0),
            icon_row_height=token("idml_symbols_icon_row_height", 30.7),
            icon_last_row_height=token(
                "idml_symbols_icon_last_row_height", 32.2,
            ),
            icon_long_last_row_height=token(
                "idml_symbols_icon_long_last_row_height", 64.9,
            ),
            subbar_height=token("comp_subbar_height", 13.9),
            maintenance_title_gap=token(
                "idml_symbols_maintenance_title_gap", 3.5,
            ),
            symbols_title_gap=token("idml_symbols_title_gap", 9.0),
            h1_optical_offset=token("idml_symbols_h1_optical_offset", 1.918),
            page_bottom_allowance=token(
                "idml_symbols_page_bottom_allowance", 2.0,
            ),
            table_frame_allowance=token(
                "idml_symbols_table_frame_allowance", 0.25,
            ),
            fallback_import_allowance=token(
                "idml_symbols_fallback_import_allowance", 3.0,
            ),
            fallback_min_height=token(
                "idml_symbols_fallback_min_height", 60.0,
            ),
            fallback_text_width_ratio=token(
                "idml_symbols_fallback_text_width_ratio", 0.73,
            ),
            fallback_row_height=token(
                "idml_symbols_fallback_row_height", 24.0,
            ),
        )


@dataclass(frozen=True)
class SymbolOverflow:
    """Source-authored symbol rows carried to the following composed page."""

    left: tuple[dict, ...]
    right: tuple[dict, ...]
    headers: tuple[str, str]

    def has_rows(self) -> bool:
        return bool(self.left or self.right)


def _localized_signal_label_bar(
    writer,
    tid: str,
    label: str,
    lang: str = "en",
    *,
    signal_key: str = "",
) -> str:
    style_ref = paragraph_style_ref("HB Notice Side Label")
    badge_w = component_param_pt(
        writer.params,
        "comp_symbol_signal_width",
        60.94,
        strict=writer.strict_component_assets,
        owner="symbol signal badge",
    )
    badge_h = component_param_pt(
        writer.params,
        "comp_symbol_signal_height",
        15.3,
        strict=writer.strict_component_assets,
        owner="symbol signal badge",
    )
    badge_raise = component_param_pt(
        writer.params,
        "idml_symbols_signal_badge_baseline_shift",
        1.5,
        strict=writer.strict_component_assets,
        owner="symbol signal badge vertical centering",
    )
    content_raise = component_param_pt(
        writer.params,
        "idml_symbols_signal_content_baseline_shift",
        1.5,
        strict=writer.strict_component_assets,
        owner="symbol signal badge content vertical centering",
    )
    asset = (
        ROOT / "docs" / "templates" / "word_template" / "common_assets"
        / "symbols" / "warning_triangle_white.svg"
    )
    normalized_key = signal_key.strip().casefold()
    show_icon = not normalized_key or normalized_key in {
        "warning", "danger", "caution",
    }
    icon_w = component_param_pt(
        writer.params,
        "idml_symbols_signal_icon_width",
        7.5,
        strict=writer.strict_component_assets,
        owner="symbol signal badge",
    )
    icon_h = component_param_pt(
        writer.params,
        "idml_symbols_signal_icon_height",
        7.0,
        strict=writer.strict_component_assets,
        owner="symbol signal badge",
    )
    icon = ""
    if show_icon and asset.exists():
        icon = writer._image_cell_content(f"{tid}icon", asset, icon_w, icon_h)
    elif show_icon and writer.strict_component_assets:
        raise FileNotFoundError(f"symbol signal badge asset missing: {asset}")
    language = (lang or "en").split("-", 1)[0].casefold()
    if language in {"fr", "es"}:
        label_size, label_leading, label_scale = signal_label_metrics(
            writer.params,
            language,
            label,
            badge_w - 3.0 - 2.0 - (icon_w + 2.0 if show_icon else 0.0),
        )
        content = (
            f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">\n'
            '    <CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'BaselineShift="{content_raise:g}">'
            f'{icon}</CharacterStyleRange>\n'
            '    <CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            'FillColor="Color/Paper" FontStyle="Bold" '
            f'PointSize="{label_size:g}" HorizontalScale="{label_scale:g}" '
            f'BaselineShift="{content_raise:g}">'
            f'<Properties><Leading type="unit">{label_leading:g}</Leading></Properties>'
            f'<Content> {escape(label)}</Content></CharacterStyleRange>\n'
            '  </ParagraphStyleRange>\n'
        )
    else:
        content = (
            f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">\n'
            '    <CharacterStyleRange '
            'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
            f'FillColor="Color/Paper" BaselineShift="{content_raise:g}">'
            f'{icon}<Content> {escape(label)}</Content>'
            '</CharacterStyleRange>\n  </ParagraphStyleRange>\n'
        )
    badge_cell = writer._cell(
        f"{tid}c0",
        "0:0",
        content,
        fill="Color/HB Brand Dark",
        stroke=False,
        top=0,
        bottom=0,
        left=3,
        right=2,
        valign="CenterAlign",
    )
    badge = writer._component_table(
        f"{tid}tbl",
        [badge_w],
        [badge_cell],
        outer_stroke=False,
        row_heights=[badge_h],
    )
    carrier = writer._wrap_table_paragraph(badge, True, span_columns=False)
    # The first character range is the inline table carrier.  Shift that
    # range independently from the icon/label ranges inside the nested badge
    # table: the outer shift centres the dark badge in its signal row, while
    # ``content_raise`` optically centres the visible artwork and glyphs in
    # the badge.  Rewriting every descendant range here would collapse those
    # two layout contracts back into one value.
    marker = (
        'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
    )
    return carrier.replace(
        marker,
        f'{marker} BaselineShift="{badge_raise:g}"',
        1,
    )


def _symbol_signal_bar(
    writer,
    tid: str,
    label: str,
    bundle_root: Path,
    lang: str = "en",
    *,
    signal_key: str = "",
) -> str:
    del bundle_root
    return _localized_signal_label_bar(
        writer, tid, label, lang, signal_key=signal_key,
    )


def _signal_row_fields(row: object) -> tuple[str, str, str]:
    """Normalize current semantic rows and legacy two-cell rows."""

    if isinstance(row, dict):
        return (
            str(row.get("signal_key") or "").casefold(),
            str(row.get("label") or ""),
            str(row.get("text") or ""),
        )
    if isinstance(row, (list, tuple)) and len(row) == 2:
        return "", str(row[0]), str(row[1])
    raise ValueError("symbol signal row must be a semantic object or two cells")


def _symbols_signal_table(writer, tid: str, signals: list[object],
                          width: float, bundle_root: Path,
                          lang: str = "en", *,
                          headers: tuple[str, str],
                          row_heights: list[float] | None = None,
                          left_col_width: float | None = None,
                          fit_body_to_row: bool = False,
                          cell_vertical_inset: float = 3.0,
                          disable_hyphenation: bool = False,
                          auto_grow_rows: bool = True) -> str:
    rows = [("", headers[0], headers[1], True)] + [
        (*_signal_row_fields(row), False) for row in signals
    ]
    left_col = left_col_width
    if left_col is None:
        left_col = component_param_pt(
            writer.params,
            "comp_symbol_signal_col_width",
            width * 0.24,
            strict=writer.strict_component_assets,
            owner="symbol signal table",
        )
    cols = [left_col, width - left_col]
    cells = []
    for ri, (signal_key, left, right, header) in enumerate(rows):
        if header:
            left_xml = writer._psr("HB Symbol Header", left, terminal=True)
            right_xml = writer._psr("HB Symbol Header", right, terminal=True)
        else:
            left_xml = writer._symbol_signal_bar(
                f"{tid}sig{ri}", left, bundle_root, lang,
                signal_key=signal_key,
            )
            right_xml = writer._psr("HB Spec Value", right, terminal=True)
            if fit_body_to_row and row_heights is not None:
                size, leading, scale = fit_symbol_body_metrics(
                    writer.params,
                    lang,
                    right,
                    width - left_col - 12.0,
                    row_heights[ri],
                )
                right_xml = with_character_metrics(
                    right_xml,
                    point_size=size,
                    leading=leading,
                    horizontal_scale=scale,
                )
            if disable_hyphenation:
                right_xml = right_xml.replace(
                    "<ParagraphStyleRange ",
                    '<ParagraphStyleRange Hyphenation="false" ',
                )
        cells.append(writer._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                  fill="Color/HB Bg K05",
                                  top=cell_vertical_inset,
                                  bottom=cell_vertical_inset,
                                  left=6 if header else 7.6,
                                  right=4,
                                  valign="CenterAlign"))
        cells.append(writer._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                  top=cell_vertical_inset,
                                  bottom=cell_vertical_inset,
                                  left=7, right=5,
                                  valign="CenterAlign"))
    table = writer._component_table(
        tid, cols, cells, n_rows=len(rows), role="data", outer_stroke=False)
    if row_heights is not None:
        if len(row_heights) != len(rows):
            raise ValueError("symbol signal row heights must match rendered rows")
        for row_index, height in enumerate(row_heights):
            before = f'<Row Self="{tid}r{row_index}" Name="{row_index}"/>'
            after = (
                f'<Row Self="{tid}r{row_index}" Name="{row_index}" '
                f'SingleRowHeight="{height:g}" MinimumHeight="{height:g}" '
                f'AutoGrow="{str(auto_grow_rows).lower()}"/>'
            )
            if before not in table:
                raise ValueError(f"symbol signal row anchor missing: {tid}r{row_index}")
            table = table.replace(before, after, 1)
    return table


def _symbols_icon_table(
    writer,
    tid: str,
    icons: list[dict],
    width: float,
    lang: str = "en",
    *,
    headers: tuple[str, str],
    include_header: bool = True,
    row_heights: list[float] | None = None,
    icon_col_width: float | None = None,
    icon_width: float | None = None,
    icon_height: float | None = None,
    fit_body_to_row: bool = False,
    disable_hyphenation: bool = False,
    auto_grow_rows: bool = True,
) -> str:
    header = [{"figure": "", "text": headers[1], "header": True}]
    rows = (header if include_header else []) + [
        {**row, "header": False} for row in icons
    ]
    left_col = icon_col_width
    if left_col is None:
        left_col = component_param_pt(
            writer.params,
            "idml_symbols_icon_col_width",
            component_param_pt(
                writer.params,
                "comp_symbol_icon_col_width",
                width * 0.27,
                strict=False,
                owner="symbol icon table fallback",
            ),
            strict=writer.strict_component_assets,
            owner="symbol icon table",
        )
    cols = [left_col, width - left_col]
    icon_w = icon_width
    if icon_w is None:
        icon_w = component_param_pt(
            writer.params,
            "idml_symbols_icon_width",
            component_param_pt(
                writer.params,
                "comp_symbol_icon_width",
                18.0,
                strict=False,
                owner="symbol icon table fallback",
            ),
            strict=writer.strict_component_assets,
            owner="symbol icon table",
        )
    icon_h = icon_height
    if icon_h is None:
        icon_h = component_param_pt(
            writer.params,
            "idml_symbols_icon_height",
            component_param_pt(
                writer.params,
                "comp_symbol_icon_height",
                18.0,
                strict=False,
                owner="symbol icon table fallback",
            ),
            strict=writer.strict_component_assets,
            owner="symbol icon table",
        )
    icon_w *= SYMBOL_ICON_ART_SCALE
    icon_h *= SYMBOL_ICON_ART_SCALE
    cells = []
    for ri, row in enumerate(rows):
        if row.get("header"):
            left_xml = writer._psr("HB Symbol Header", headers[0], terminal=True)
            right_xml = writer._psr("HB Symbol Header", row["text"], terminal=True)
        else:
            fig = _symbol_icon_asset(row.get("figure"))
            icon = ""
            if fig and fig.exists():
                icon = writer._image_cell_content(
                    f"{tid}img{ri}", fig, icon_w, icon_h,
                )
                image_anchor = (
                    f'<Image Self="{tid}img{ri}_img" '
                    'ItemTransform="1 0 0 1 0 0">'
                )
                icon = icon.replace(
                    image_anchor,
                    image_anchor
                    + '<TransparencySetting><BlendingSetting '
                    'BlendMode="Darken" Opacity="100"/>'
                    '</TransparencySetting>',
                    1,
                )
            figure_style_ref = paragraph_style_ref("HB Figure")
            left_xml = (
                f'  <ParagraphStyleRange AppliedParagraphStyle="{figure_style_ref}" '
                'Justification="CenterAlign">'
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                + icon + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
            right_xml = writer._psr("HB Symbol Body", row["text"], terminal=True)
            if fit_body_to_row and row_heights is not None:
                size, leading, scale = fit_symbol_body_metrics(
                    writer.params,
                    lang,
                    row["text"],
                    width - left_col - 9.0,
                    row_heights[ri],
                )
                right_xml = with_character_metrics(
                    right_xml,
                    point_size=size,
                    leading=leading,
                    horizontal_scale=scale,
                )
            elif lang in {"fr", "es"}:
                right_xml = right_xml.replace(
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"',
                    'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]" '
                    'PointSize="5.6" Leading="6.15" HorizontalScale="96"',
                    1,
                )
            if disable_hyphenation:
                right_xml = right_xml.replace(
                    "<ParagraphStyleRange ",
                    '<ParagraphStyleRange Hyphenation="false" ',
                )
        cells.append(writer._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                  fill="Color/HB Bg K05",
                                  top=2 if row.get("header") else 0,
                                  bottom=2 if row.get("header") else 0,
                                  left=4,
                                  right=2 if row.get("header") else 4,
                                  valign="CenterAlign"))
        cells.append(writer._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                  top=2, bottom=2, left=5, right=4,
                                  valign="CenterAlign"))
    table = writer._component_table(
        tid, cols, cells, n_rows=len(rows), role="data", outer_stroke=False)
    if row_heights is not None:
        if len(row_heights) != len(rows):
            raise ValueError("symbol table row heights must match rendered rows")
        for ri, height in enumerate(row_heights):
            before = f'<Row Self="{tid}r{ri}" Name="{ri}"/>'
            after = (
                f'<Row Self="{tid}r{ri}" Name="{ri}" '
                f'SingleRowHeight="{height:g}" MinimumHeight="{height:g}" '
                f'AutoGrow="{str(auto_grow_rows).lower()}"/>'
            )
            if before not in table:
                raise ValueError(f"symbol table row anchor missing: {tid}r{ri}")
            table = table.replace(before, after, 1)
    return table


def _table_story(writer, sid: str, title: str, table: str) -> str:
    style_ref = paragraph_style_ref("HB Body")
    marker_attrs = ""
    if "idml_table_marker_point_size" in writer.params:
        marker_size = param_pt(
            writer.params, "idml_table_marker_point_size", 0.1,
        )
        marker_attrs = f' PointSize="{marker_size:g}" Leading="{marker_size:g}"'
    return writer._add_story_parts(
        sid, title,
         [f'  <ParagraphStyleRange AppliedParagraphStyle="{style_ref}">\n'
         '    <CharacterStyleRange '
         'AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
         f'{marker_attrs}>\n'
         + table +
         '    <Content></Content></CharacterStyleRange>\n'
         '  </ParagraphStyleRange>\n'])


def add_safety_symbols_page(
    writer,
    sid: str,
    tail_blocks: list[tuple[str, str]],
    maintenance_blocks: list[tuple[str, str]],
    signals: list[object],
    icons: list[dict],
    bundle_root: Path,
    page_index: int,
    lang: str = "en",
    *,
    title: str,
    signal_headers: tuple[str, str],
    icon_headers: tuple[str, str],
) -> tuple[str, SymbolOverflow]:
    """Place the complete Safety/Maintenance/Symbols component."""
    from .components.safety_symbols_panel import (
        SafetySymbolsPanel,
        SafetySymbolsPanelData,
    )

    panel = SafetySymbolsPanel(
        writer,
        sid=sid,
        data=SafetySymbolsPanelData.from_source(
            tail_blocks=tail_blocks,
            maintenance_blocks=maintenance_blocks,
            title=title,
            signal_headers=signal_headers,
            icon_headers=icon_headers,
            signals=signals,
            icons=icons,
        ),
        bundle_root=bundle_root,
        language=lang,
    ).render(
        x=writer.m_l,
        y=0.0,
        width=writer.page_w - writer.m_l - writer.m_r,
        available_height=writer.page_h,
    )
    spread_id = f"sp_{page_index}"
    page_no = page_index + 1
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
        f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" '
        'ShowMasterItems="true">\n'
        f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
        'AppliedMaster="n" OverrideList="" TabOrder="" '
        'GridStartingPoint="TopOutside" '
        f'GeometricBounds="0 0 {writer.page_h:g} {writer.page_w:g}" '
        f'ItemTransform="1 0 0 1 {-writer.page_w / 2:g} '
        f'{-writer.page_h / 2:g}">\n'
        '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
        f'Top="{writer.m_t:g}" Bottom="{writer.m_b:g}" '
        f'Left="{writer.m_l:g}" Right="{writer.m_r:g}"/>\n'
        '  </Page>\n'
        + "".join(panel.frames)
        + '</Spread>\n'
        '</idPkg:Spread>\n'
    )
    writer.spreads.append((spread_id, xml))
    return spread_id, panel.overflow
