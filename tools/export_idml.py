"""IDML exporter — route B of the InDesign handoff plan.

Produces an editable .idml (InDesign Markup Language) package so designers
can fine-tune pipeline output in InDesign instead of retouching PDFs:

- page geometry and paragraph styles are mapped 1:1 from data/layout_params.csv
- brand colors are emitted as CMYK swatches (from the brand_color_* keys)
- the SPECIFICATIONS page is exported as real IDML tables fed straight from
  the phase2 Spec_Master snapshot (section titles + label/value rows)
- body sections flow through linked text frames so InDesign reflows freely

MVP scope (M1-M3): valid package + style system + spec tables/story.
Not yet covered: image frames, two-column safety layout, full page set.

Usage:
  python tools/export_idml.py --model JE-1000F --region US [--lang en]
      [--data-root data/phase2] [--out docs/_build/.../manual.idml]
  python tools/export_idml.py --check <file.idml>   # structural validation
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

try:
    from tools.idml_rst_extract import bundle_page_order, extract_page
    from tools.script_bootstrap import bootstrap_repo_root
except ImportError:  # pragma: no cover - direct script execution fallback
    from idml_rst_extract import bundle_page_order, extract_page  # type: ignore
    from script_bootstrap import bootstrap_repo_root

ROOT = bootstrap_repo_root(__file__, parent_count=1)

MIMETYPE = "application/vnd.adobe.indesign-idml-package"
IDPKG = "http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging"

MM_TO_PT = 72.0 / 25.4

SYMBOL_COPY = {
    "en": {
        "title": "MEANING OF SYMBOLS",
        "symbol": "Symbol",
        "meaning": "Meaning",
        "warning": "WARNING",
    },
    "fr": {
        "title": "SIGNIFICATION DES SYMBOLES",
        "symbol": "Symbole",
        "meaning": "Signification",
        "warning": "AVERTISSEMENT",
    },
    "es": {
        "title": "SIGNIFICADO DE LOS SÍMBOLOS",
        "symbol": "Símbolo",
        "meaning": "Significado",
        "warning": "ADVERTENCIA",
    },
}


def normalize_lang(lang: str | None) -> str:
    lang = (lang or "en").strip()
    aliases = {"ja": "jp", "pt-br": "pt-BR", "pt_BR": "pt-BR"}
    return aliases.get(lang, aliases.get(lang.lower(), lang.lower() or "en"))


def symbol_copy(lang: str | None) -> dict[str, str]:
    return SYMBOL_COPY.get(normalize_lang(lang), SYMBOL_COPY["en"])


# ---------------------------------------------------------------------------
# layout params
# ---------------------------------------------------------------------------

def load_layout_params(csv_path: Path) -> dict[str, tuple[str, str]]:
    """key -> (value, unit)"""
    out: dict[str, tuple[str, str]] = {}
    with csv_path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row.get("key") or "").strip()
            if not key:
                continue
            out[key] = ((row.get("value") or "").strip(), (row.get("unit") or "").strip())
    return out


def param_pt(params: dict[str, tuple[str, str]], key: str, default: float) -> float:
    value, unit = params.get(key, ("", ""))
    if not value:
        return default
    try:
        v = float(value)
    except ValueError:
        return default
    if unit == "mm":
        return v * MM_TO_PT
    return v  # pt / em treated as pt at this level


def brand_cmyk(params: dict[str, tuple[str, str]], key: str, default: str) -> tuple[float, float, float, float]:
    value, unit = params.get(key, (default, "cmyk"))
    parts = [p.strip() for p in (value or default).split(",")]
    try:
        c, m, y, k = (float(p) for p in parts)
    except (ValueError, TypeError):
        c, m, y, k = 0.0, 0.0, 0.0, 1.0
    return c * 100, m * 100, y * 100, k * 100


# ---------------------------------------------------------------------------
# spec data
# ---------------------------------------------------------------------------

def load_spec_sections(data_root: Path, model: str, region: str) -> list[dict]:
    doc_key = f"{model}_{region}"
    path = data_root / "Spec_Master.csv"
    rows = [
        r for r in csv.DictReader(path.open(encoding="utf-8"))
        if r.get("document_key") == doc_key
        and r.get("Is_Latest") == "TRUE"
        and r.get("Page") == "specifications"
    ]
    rows.sort(key=lambda r: (float(r.get("Section_order") or 0),
                             float(r.get("Row_order") or 0),
                             float(r.get("Line_order") or 0)))
    sections: list[dict] = []
    # rows sharing (Section, Row_order) merge into one multi-line value cell
    for r in rows:
        title = (r.get("Section") or "").strip()
        if not sections or sections[-1]["title"] != title:
            sections.append({"title": title, "rows": []})
        label = (r.get("Row_label_source") or "").strip()
        param = (r.get("Param_source") or "").strip()
        value = (r.get("Value_source") or "").strip()
        line = f"{param}: {value}" if param else value
        sec_rows = sections[-1]["rows"]
        if sec_rows and sec_rows[-1][0] == label and float(r.get("Line_order") or 1) > 1:
            sec_rows[-1] = (label, sec_rows[-1][1] + "\n" + line)
        else:
            sec_rows.append((label, line))
    return sections


def load_lcd_rows(data_root: Path, model: str) -> list[dict]:
    """LCD icon table rows for one model: no / icon path / name / description."""
    path = data_root / "lcd_icons_blocks.csv"
    out: list[dict] = []
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r.get("Is_latest") != "TRUE":
            continue
        models = [m.strip() for m in (r.get("Model") or "").split(",")]
        if model not in models:
            continue
        out.append({
            "no": (r.get("No.") or "").strip(),
            "figure": (r.get("figure") or "").strip(),
            "name": (r.get("icon_en") or "").strip(),
            "desc": (r.get("icon_desc_en") or "").strip(),
        })
    out.sort(key=lambda x: float(x["no"] or 0))
    return out


def load_spec_annotations(data_root: Path, model: str, region: str) -> list[str]:
    """Spec-page footnotes + notes for the target — the master prints them
    under the spec tables (user-reported as missing)."""
    out: list[str] = []
    for fname, order_col in (("Spec_Footnotes.csv", "Footnote_order"),
                             ("Spec_Notes.csv", "Note_order")):
        path = data_root / fname
        if not path.exists():
            continue
        rows: list[tuple[float, str]] = []
        for r in csv.DictReader(path.open(encoding="utf-8")):
            if r.get("Is_Latest") != "TRUE" or r.get("Enabled", "TRUE") == "FALSE":
                continue
            models = [m.strip() for m in (r.get("Model") or "").split(",") if m.strip()]
            if models and model not in models and "ALL" not in models:
                continue
            regions = [x.strip() for x in (r.get("Region") or "").split(",") if x.strip()]
            if regions and region not in regions and "ALL" not in regions:
                continue
            text = (r.get("Text_en") or "").strip()
            if text:
                rows.append((float(r.get(order_col) or 0), text))
        out.extend(t for _, t in sorted(rows))
    return out


def load_symbols_rows(data_root: Path, lang: str = "en") -> tuple[list[tuple[str, str]], list[dict]]:
    """symbols_blocks.csv -> localized (signal rows [label, meaning], icon rows)."""
    path = data_root / "symbols_blocks.csv"
    signals: list[tuple[str, str]] = []
    icons: list[dict] = []
    lang = normalize_lang(lang)
    label_col = f"label_{lang}"
    text_col = f"text_{lang}"
    rows = [r for r in csv.DictReader(path.open(encoding="utf-8"))
            if r.get("Is_Latest", r.get("Is_latest")) == "TRUE"]
    rows.sort(key=lambda r: float(r.get("order") or 0))
    for r in rows:
        text = ((r.get(text_col) or "").strip()
                or (r.get("text_en") or "").strip())
        if r.get("block_type") == "signal_row":
            if text:
                label = ((r.get(label_col) or "").strip()
                         or (r.get("label_en") or "").strip())
                signals.append((label, text))
        elif r.get("block_type") == "table_row":
            icons.append({"figure": (r.get("image_path") or "").strip(), "text": text})
    return signals, icons


def load_trouble_rows(data_root: Path, model: str, region: str) -> list[tuple[str, str]]:
    path = data_root / "troubleshooting_blocks.csv"
    out: list[tuple[str, str]] = []
    for r in csv.DictReader(path.open(encoding="utf-8")):
        if r.get("Is_latest") != "TRUE":
            continue
        models = [m.strip() for m in (r.get("Model") or "").split(",") if m.strip()]
        if models and model not in models and "ALL" not in models:
            continue
        regions = [x.strip() for x in (r.get("Region") or "").split(",") if x.strip()]
        if regions and region not in regions and "ALL" not in regions:
            continue
        out.append(((r.get("error_code") or "").strip(),
                    (r.get("corrective_measures_en") or "").strip()))
    return out


# ---------------------------------------------------------------------------
# IDML package writer
# ---------------------------------------------------------------------------

class IdmlWriter:
    def __init__(self, params: dict[str, tuple[str, str]]):
        self.params = params
        self.page_w = param_pt(params, "page_paperwidth", 368.79)
        self.page_h = param_pt(params, "page_paperheight", 524.69)
        self.m_l = param_pt(params, "page_margin_left", 28.35)
        self.m_r = param_pt(params, "page_margin_right", 28.35)
        self.m_t = param_pt(params, "page_margin_top", 14.17)
        self.m_b = param_pt(params, "page_margin_bottom", 36.85)
        self.stories: list[tuple[str, str]] = []   # (id, xml)
        self.spreads: list[tuple[str, str]] = []

    # -- styles ------------------------------------------------------------
    def para_styles(self) -> list[tuple[str, float, float, str, str]]:
        """(name, size, leading, font_style, extras)"""
        p = self.params
        def sz(key, d): return param_pt(p, key, d)
        return [
            ("HB H1", sz("type_h1_font_size", 9.0), sz("type_h1_font_leading", 10.8), "Bold", ""),
            ("HB Title L2", sz("type_title_l2_font_size", 8.6), sz("type_title_l2_font_leading", 9.4), "Bold", ""),
            ("HB Title L3", sz("type_title_l3_font_size", 7.0), sz("type_title_l3_font_leading", 8.0), "Medium", ""),
            ("HB Notice Label", sz("type_notice_label_font_size", 6.8), sz("type_notice_label_font_leading", 7.4), "Bold", "label"),
            ("HB Notice Side Label", sz("type_notice_label_font_size", 6.8), sz("type_notice_label_font_leading", 7.4), "Bold", "center"),
            ("HB Card Number", sz("type_inbox_label_font_size", 6.5), sz("type_inbox_label_font_leading", 7.0), "Bold", "card_number"),
            ("HB InBox Label", sz("type_inbox_label_font_size", 6.3), sz("type_inbox_label_font_leading", 7.0), "Bold", "center"),
            ("HB Capsule Text", sz("type_title_l2_font_size", 8.6), sz("type_title_l2_font_leading", 9.4), "Bold", "capsule_text"),
            ("HB Figure", sz("type_body_font_size", 6.2), 0.0, "Regular", "figure"),
            ("HB Body", sz("type_body_font_size", 6.2), sz("type_body_font_leading", 7.5), "Regular", ""),
            ("HB List", sz("type_list_font_size", 5.4), sz("type_list_font_leading", 6.4), "Regular", ""),
            ("HB Spec Section", sz("type_spec_section_font_size", 8.8), sz("type_spec_section_font_leading", 9.6), "Bold", ""),
            ("HB Spec Label", sz("type_spec_label_font_size", 6.0), sz("type_spec_label_font_leading", 6.6), "Regular", ""),
            ("HB Spec Value", sz("type_spec_value_font_size", 6.0), sz("type_spec_value_font_leading", 6.6), "Regular", ""),
            ("HB Spec Note", sz("type_spec_note_font_size", 5.4), sz("type_spec_note_font_leading", 6.0), "Regular", ""),
        ]

    def styles_xml(self) -> str:
        styles = []
        for name, size, leading, weight, kind in self.para_styles():
            self_id = "ParagraphStyle/" + name.replace(" ", "%20")
            # V2.0 master: H1 is a white-on-brand-dark bar; notice labels are
            # compact dark pills. Both map to paragraph shading in IDML.
            shaded = name == "HB H1" or kind in {"label", "card_number"}
            fill = "Color/Paper" if shaded or kind == "capsule_text" else "Color/HB Brand Dark"
            # NOTE the Paragraph* prefix: bare ShadingOn/ShadingColor are
            # silently ignored by InDesign (designer-reported: no H1 bar,
            # invisible white labels/numerals)
            if kind == "card_number":
                shading = (
                    'ParagraphShadingOn="true" '
                    'ParagraphShadingColor="Color/HB Brand Dark" '
                    'ParagraphShadingTint="100" '
                    'ParagraphShadingWidth="TextWidth" '
                    'ParagraphShadingTopOrigin="AscentTopOrigin" '
                    'ParagraphShadingBottomOrigin="DescentBottomOrigin" '
                    'ParagraphShadingTopOffset="2" ParagraphShadingBottomOffset="2" '
                    'ParagraphShadingLeftOffset="3" ParagraphShadingRightOffset="3" '
                    'SpaceBefore="7" SpaceAfter="6" '
                )
            elif shaded:
                shading = (
                'ParagraphShadingOn="true" '
                'ParagraphShadingColor="Color/HB Brand Dark" '
                'ParagraphShadingTint="100" '
                'ParagraphShadingWidth="ColumnWidth" '
                'ParagraphShadingTopOrigin="AscentTopOrigin" '
                'ParagraphShadingBottomOrigin="DescentBottomOrigin" '
                'ParagraphShadingTopOffset="2" ParagraphShadingBottomOffset="2" '
                'ParagraphShadingLeftOffset="3" ParagraphShadingRightOffset="3" '
                'SpaceBefore="4" SpaceAfter="3" '
                )
            else:
                shading = ""
            justification = "CenterAlign" if kind in {"center", "card_number"} else "LeftAlign"
            styles.append(
                f'  <ParagraphStyle Self="{self_id}" Name="{name}" '
                f'PointSize="{size:g}" FillColor="{fill}" {shading}'
                f'Justification="{justification}">\n'
                f'    <Properties>\n'
                f'      <AppliedFont type="string">Gilroy</AppliedFont>\n'
                f'      <FontStyle type="string">{weight}</FontStyle>\n'
                # fixed leading does not grow for inline anchored objects —
                # figure paragraphs need Auto so art doesn't shoot out the top
                + (f'      <Leading type="unit">{leading:g}</Leading>\n'
                   if kind != "figure" else
                   '      <Leading type="enum">Auto</Leading>\n') +
                f'    </Properties>\n'
                f'  </ParagraphStyle>'
            )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Styles xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            '  <RootCharacterStyleGroup Self="rcsg">\n'
            '    <CharacterStyle Self="CharacterStyle/$ID/[No character style]" Name="$ID/[No character style]"/>\n'
            '  </RootCharacterStyleGroup>\n'
            '  <RootParagraphStyleGroup Self="rpsg">\n'
            '    <ParagraphStyle Self="ParagraphStyle/$ID/[No paragraph style]" Name="$ID/[No paragraph style]"/>\n'
            '    <ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" Name="$ID/NormalParagraphStyle"/>\n'
            + "\n".join(styles) + "\n"
            '  </RootParagraphStyleGroup>\n'
            '  <RootCellStyleGroup Self="rcellsg">\n'
            '    <CellStyle Self="CellStyle/$ID/[None]" Name="$ID/[None]"/>\n'
            '  </RootCellStyleGroup>\n'
            '  <RootTableStyleGroup Self="rtsg">\n'
            '    <TableStyle Self="TableStyle/$ID/[Basic Table]" Name="$ID/[Basic Table]"/>\n'
            '  </RootTableStyleGroup>\n'
            '  <RootObjectStyleGroup Self="rosg">\n'
            '    <ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]"/>\n'
            '    <ObjectStyle Self="ObjectStyle/$ID/[Normal Text Frame]" Name="$ID/[Normal Text Frame]"/>\n'
            '  </RootObjectStyleGroup>\n'
            '</idPkg:Styles>\n'
        )

    def graphic_xml(self) -> str:
        p = self.params
        colors = []
        for name, key, default in (
            ("HB Brand Dark", "brand_color_branddark", "0,0,0,0.90"),
            ("HB Text Gray", "brand_color_textgray", "0,0,0,0.90"),
            ("HB Line K40", "brand_color_linek40", "0,0,0,0.80"),
            ("HB Bg K05", "brand_color_bgk05", "0,0,0,0.05"),
        ):
            c, m, y, k = brand_cmyk(p, key, default)
            colors.append(
                f'  <Color Self="Color/{name}" Model="Process" Space="CMYK" '
                f'ColorValue="{c:g} {m:g} {y:g} {k:g}" Name="{name}"/>'
            )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Graphic xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            '  <Color Self="Color/Black" Model="Process" Space="CMYK" ColorValue="0 0 0 100" Name="Black"/>\n'
            '  <Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" Name="Paper"/>\n'
            + "\n".join(colors) + "\n"
            '  <Swatch Self="Swatch/None" Name="None"/>\n'
            '</idPkg:Graphic>\n'
        )

    def fonts_xml(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Fonts xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            '  <FontFamily Self="ff_gilroy" Name="Gilroy">\n'
            '    <Font Self="ff_gilroy_r" FontFamily="Gilroy" Name="Gilroy Regular" PostScriptName="Gilroy-Regular" Status="Installed" FontStyleName="Regular" FontType="OpenTypeCFF"/>\n'
            '    <Font Self="ff_gilroy_m" FontFamily="Gilroy" Name="Gilroy Medium" PostScriptName="Gilroy-Medium" Status="Installed" FontStyleName="Medium" FontType="OpenTypeCFF"/>\n'
            '    <Font Self="ff_gilroy_sb" FontFamily="Gilroy" Name="Gilroy Semibold" PostScriptName="Gilroy-SemiBold" Status="Installed" FontStyleName="Semibold" FontType="OpenTypeCFF"/>\n'
            '    <Font Self="ff_gilroy_b" FontFamily="Gilroy" Name="Gilroy Bold" PostScriptName="Gilroy-Bold" Status="Installed" FontStyleName="Bold" FontType="OpenTypeCFF"/>\n'
            '  </FontFamily>\n'
            '</idPkg:Fonts>\n'
        )

    def preferences_xml(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Preferences xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'  <DocumentPreference PageWidth="{self.page_w:g}" PageHeight="{self.page_h:g}" '
            'PagesPerDocument="1" FacingPages="true" PageOrientation="Portrait" '
            'DocumentBleedTopOffset="8.5" DocumentBleedBottomOffset="8.5" '
            'DocumentBleedInsideOrLeftOffset="8.5" DocumentBleedOutsideOrRightOffset="8.5"/>\n'
            '  <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
            '</idPkg:Preferences>\n'
        )

    # -- content -----------------------------------------------------------

    # Characters Gilroy has no glyph for — same policy as the PDF path's
    # FRAGILE_UNICODE_REPLACEMENTS in patch_latex_fonts.py. Without this,
    # InDesign shows pink missing-glyph boxes (designer-reported).
    GLYPH_FALLBACKS = (
        ("⎓", " DC "),   # ⎓ direct-current symbol
        ("※", "*"),      # ※ reference mark
        ("₄", "4"),      # ₄ subscript four (LiFePO4)
    )

    @classmethod
    def _clean_text(cls, text: str) -> str:
        for raw, replacement in cls.GLYPH_FALLBACKS:
            text = text.replace(raw, replacement)
        return text

    @classmethod
    def _psr(cls, style: str, text: str, *, terminal: bool = False,
             span_columns: bool = False) -> str:
        """One ParagraphStyleRange.

        IDML paragraphs are delimited by explicit <Br/> characters in the
        content stream, NOT by ParagraphStyleRange boundaries — without a
        trailing <Br/> adjacent ranges fuse into one paragraph
        ("SPECIFICATIONSGENERAL INFO", designer-reported). Every range
        therefore ends with <Br/> unless it is the story's last one.
        """
        lines = cls._clean_text(text).split("\n")
        line_xmls = []
        for line in lines:
            runs = cls._bold_runs(line)
            line_xmls.append("".join(
                '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"'
                + (' FontStyle="Bold"' if bold else "")
                + f'><Content>{escape(seg)}</Content></CharacterStyleRange>'
                for seg, bold in runs
            ) or '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                 '<Content></Content></CharacterStyleRange>')
        br = ('<CharacterStyleRange AppliedCharacterStyle='
              '"CharacterStyle/$ID/[No character style]"><Br/></CharacterStyleRange>')
        content = br.join(line_xmls)
        if not terminal:
            content += br
        sid = "ParagraphStyle/" + style.replace(" ", "%20")
        span_attr = ' SpanColumnType="SpanColumns"' if span_columns else ""
        return (
            f'  <ParagraphStyleRange AppliedParagraphStyle="{sid}"{span_attr}>\n'
            f'    {content}\n'
            '  </ParagraphStyleRange>\n'
        )

    @staticmethod
    def _bold_runs(line: str) -> list[tuple[str, bool]]:
        """Split rst inline strong markup (**x**) into (text, bold) runs.

        Designer-reported: literal ** asterisks in body text. Bare *
        emphasis is left alone (rare in the bundles and ambiguous with
        footnote markers).
        """
        runs: list[tuple[str, bool]] = []
        parts = re.split(r"\*\*(.+?)\*\*", line)
        for i, part in enumerate(parts):
            if part:
                runs.append((part, i % 2 == 1))
        return runs

    def _table(self, tid: str, rows: list[tuple[str, str]],
               label_style: str = "HB Spec Label") -> str:
        left_ratio = float(self.params.get("comp_spec_table_left_ratio", ("0.315", ""))[0])
        body_w = self.page_w - self.m_l - self.m_r
        col1 = body_w * left_ratio
        col2 = body_w - col1
        cells = []
        for ri, (label, value) in enumerate(rows):
            for ci, (txt, style) in enumerate(((label, label_style), (value, "HB Spec Value"))):
                cells.append(
                    f'    <Cell Self="{tid}c{ri}_{ci}" Name="{ci}:{ri}" RowSpan="1" ColumnSpan="1" '
                    'AppliedCellStyle="CellStyle/$ID/[None]" '
                    'TopInset="2" BottomInset="2" LeftInset="3" RightInset="3">\n'
                    + self._psr(style, txt, terminal=True) +
                    '    </Cell>'
                )
        row_els = "\n".join(
            f'    <Row Self="{tid}r{ri}" Name="{ri}" SingleRowHeight="10.3"/>' for ri in range(len(rows))
        )
        return (
            f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
            f'BodyRowCount="{len(rows)}" ColumnCount="2" HeaderRowCount="0" FooterRowCount="0">\n'
            f'{row_els}\n'
            f'    <Column Self="{tid}col0" Name="0" SingleColumnWidth="{col1:g}"/>\n'
            f'    <Column Self="{tid}col1" Name="1" SingleColumnWidth="{col2:g}"/>\n'
            + "\n".join(cells) + "\n"
            '  </Table>\n'
        )

    def frame_height(self) -> float:
        return self.page_h - self.m_t - self.m_b

    @staticmethod
    def estimate_spec_height(sections: list[dict]) -> float:
        """Rough content height in pt for page-count estimation.

        Deliberately coarse: if it underestimates, InDesign shows the
        standard overset indicator and the designer drags the chain one
        frame longer — a trailing blank page is worse than that.
        """
        h = 16.0  # H1
        for sec in sections:
            h += 14.0  # section title
            for _, value in sec["rows"]:
                h += 11.0 * max(1, value.count("\n") + 1)
        return h

    def pages_for_height(self, height_pt: float) -> int:
        import math
        return max(1, math.ceil(height_pt / self.frame_height()))

    def _image_cell_content(self, rect_id: str, image_path: Path, w_pt: float, h_pt: float) -> str:
        """Anchored image frame for a table cell, linked to a file on disk.

        The Link keeps the file external (URI), so the designer relinks or
        edits assets through InDesign's Links panel — the same contract as
        a hand-built document.
        """
        uri = image_path.resolve().as_uri()
        # Inline anchored objects hang from the text baseline: the path must
        # span y in [-h, 0]. A [0, h] path drops below the line and overlaps
        # the following text (designer-reported).
        x1, y1, x2, y2 = 0.0, -h_pt, w_pt, 0.0
        pts = ((x1, y1), (x1, y2), (x2, y2), (x2, y1))
        anchors = "".join(
            f'<PathPointType Anchor="{x:g} {y:g}" LeftDirection="{x:g} {y:g}" '
            f'RightDirection="{x:g} {y:g}"/>' for x, y in pts
        )
        return (
            f'<Rectangle Self="{rect_id}" ContentType="GraphicType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0" '
            'AnchoredPosition="InlinePosition">'
            '<Properties><PathGeometry><GeometryPathType PathOpen="false">'
            f'<PathPointArray>{anchors}</PathPointArray>'
            '</GeometryPathType></PathGeometry></Properties>'
            f'<Image Self="{rect_id}_img" ItemTransform="1 0 0 1 0 0">'
            f'<Link Self="{rect_id}_lnk" LinkResourceURI="{escape(uri)}"/>'
            '</Image>'
            '<FrameFittingOption FittingOnEmptyFrame="Proportionally"/>'
            '</Rectangle>'
        )

    _PROSE_STYLE = {"h1": "HB H1", "h2": "HB Title L2", "h3": "HB Title L3",
                    "label": "HB Notice Label", "body": "HB Body", "list": "HB List"}

    def _resolve_bundle_image(self, bundle_root: Path, ref: str) -> Path | None:
        """Resolve an image reference from a bundle page.

        Refs are either bundle-relative paths (_assets/..., _repo_assets/...)
        or bare basenames from component macro args (main_unit1.png).
        """
        cand = bundle_root / ref
        if cand.exists():
            return cand
        name = Path(ref).name
        for base in (bundle_root / "_assets", bundle_root / "_repo_assets"):
            if base.is_dir():
                hits = sorted(base.rglob(name))
                if hits:
                    return hits[0]
        return None

    def _art_frame_size(self, img: Path, max_w: float = 120.0) -> tuple[float, float]:
        """Frame size honoring the image's real aspect ratio (Pillow when
        available; 0.62 heuristic keeps working without it)."""
        w_pt = min(max_w, self.page_w - self.m_l - self.m_r)
        try:
            from PIL import Image as _PILImage
            with _PILImage.open(img) as im:
                iw, ih = im.size
            if iw > 0:
                return w_pt, w_pt * ih / iw
        except Exception:
            pass
        return w_pt, w_pt * 0.62

    def _cell(self, cid: str, name: str, content: str, *, fill: str | None = None,
              stroke: bool = True, top: float = 3, bottom: float = 3,
              left: float = 4, right: float = 4) -> str:
        # cell fill is FillColor in IDML; CellFillColor is silently ignored
        # (designer-reported: no gray FCC/notice panels)
        fill_attr = f'FillColor="{fill}" ' if fill else ""
        stroke_attr = "" if stroke else (
            'LeftEdgeStrokeWeight="0" RightEdgeStrokeWeight="0" '
            'TopEdgeStrokeWeight="0" BottomEdgeStrokeWeight="0" ')
        return (
            f'    <Cell Self="{cid}" Name="{name}" RowSpan="1" ColumnSpan="1" '
            f'AppliedCellStyle="CellStyle/$ID/[None]" {fill_attr}{stroke_attr}'
            f'TopInset="{top:g}" BottomInset="{bottom:g}" '
            f'LeftInset="{left:g}" RightInset="{right:g}">\n'
            + content + '    </Cell>')

    def _component_table(self, tid: str, cols: list[float], cells: list[str],
                         n_rows: int = 1) -> str:
        row_els = "\n".join(f'    <Row Self="{tid}r{ri}" Name="{ri}"/>'
                             for ri in range(n_rows))
        col_els = "\n".join(
            f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{wd:g}"/>'
            for ci, wd in enumerate(cols))
        return (
            f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
            f'BodyRowCount="{n_rows}" ColumnCount="{len(cols)}" HeaderRowCount="0" FooterRowCount="0">\n'
            f'{row_els}\n{col_els}\n' + "\n".join(cells) + "\n  </Table>\n")

    def _wrap_table_paragraph(self, table: str, terminal: bool,
                              span_columns: bool = True) -> str:
        # SpanColumns: component tables run full measure across multi-column
        # frames (V2.0 master: warning boxes span the two-column safety text;
        # designer-reported overlap otherwise). No effect in single-column
        # frames.
        span_attr = ' SpanColumnType="SpanColumns"' if span_columns else ""
        return (
            '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body"'
            f'{span_attr}>\n'
            '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table +
            ('    <Content></Content></CharacterStyleRange>\n' if terminal else
             '    <Br/></CharacterStyleRange>\n')
            + '  </ParagraphStyleRange>\n')

    def _render_component(self, sid: str, n: int, spec: dict,
                          bundle_root: Path, terminal: bool,
                          span_columns: bool = True,
                          measure_w: float | None = None) -> tuple[str, float]:
        """Component spec -> (xml, est_height). Table-based fidelity layer."""
        kind = spec.get("kind")
        body_w = measure_w or (self.page_w - self.m_l - self.m_r)
        tid = f"{sid}_cmp{n}"
        warning_icon_asset = (
            ROOT / "docs" / "templates" / "word_template" / "common_assets"
            / "symbols" / "warning_triangle.png"
        )
        if kind == "inbox":
            items = spec.get("items", [])[:3]
            cols = [body_w / 3.0] * 3
            cells = []
            for ci, item in enumerate(items):
                img = self._resolve_bundle_image(bundle_root, item.get("img", ""))
                icon_w = body_w / 3.0 - 14
                icon = ""
                if img is not None:
                    iw, ih = self._art_frame_size(img, max_w=min(icon_w, 60.0))
                    icon = self._image_cell_content(f"{tid}i{ci}", img, iw, ih)
                content = (
                    self._psr("HB Card Number", str(ci + 1)) +
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + icon + '<Br/></CharacterStyleRange></ParagraphStyleRange>\n'
                    + self._psr("HB InBox Label", item.get("label", ""), terminal=True))
                cells.append(self._cell(
                    f"{tid}c0_{ci}", f"{ci}:0", content,
                    top=9, bottom=10, left=6, right=6,
                ))
            table = self._component_table(tid, cols, cells)
            return self._wrap_table_paragraph(table, terminal, span_columns), 110.0
        if kind == "safetywarning":
            texts = spec.get("texts", [])
            body = "\n".join(texts)
            icon = ""
            if warning_icon_asset.exists():
                iw, ih = self._art_frame_size(warning_icon_asset, max_w=18.0)
                icon = ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                        + self._image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih)
                        + '<Br/></CharacterStyleRange></ParagraphStyleRange>\n')
            cols = [24.0, max(24.0, body_w - 24.0)]
            cells = [
                self._cell(f"{tid}c0", "0:0", icon),
                self._cell(f"{tid}c1", "1:0",
                           self._psr("HB Title L3", body, terminal=True)),
            ]
            table = self._component_table(tid, cols, cells)
            return self._wrap_table_paragraph(table, terminal, span_columns), 28.0
        if kind == "warninglead":
            label = spec.get("label", "")
            texts = spec.get("texts", [])
            icon = ""
            if warning_icon_asset.exists():
                iw, ih = self._art_frame_size(warning_icon_asset, max_w=24.0)
                icon = ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                        + self._image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih)
                        + '<Br/></CharacterStyleRange></ParagraphStyleRange>\n')
            body = "\n".join(texts)
            right = self._psr("HB Title L2", label) + self._psr("HB Body", body, terminal=True)
            icon_w = min(36.0, max(28.0, body_w * 0.25))
            cols = [icon_w, max(36.0, body_w - icon_w)]
            cells = [
                self._cell(f"{tid}c0", "0:0", icon,
                           top=4, bottom=4, left=4, right=4),
                self._cell(f"{tid}c1", "1:0", right,
                           top=4, bottom=4, left=5, right=4),
            ]
            table = self._component_table(tid, cols, cells)
            per_line = max(12, int((body_w - icon_w) / (0.52 * 6.6)))
            lines = sum(max(1, (len(t) + per_line - 1) // per_line) for t in texts) or 1
            return self._wrap_table_paragraph(table, terminal, span_columns), max(36.0, 7.4 * (lines + 1) + 10)
        if kind == "tailwarnbox":
            label = spec.get("label", "")
            texts = spec.get("texts", [])
            icon = ""
            if warning_icon_asset.exists():
                iw, ih = self._art_frame_size(warning_icon_asset, max_w=24.0)
                icon = ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                        + self._image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih)
                        + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
            body = " ".join(t.strip() for t in texts if str(t).strip())
            label_w = 58.0
            icon_w = 32.0
            cols = [icon_w, label_w, max(80.0, body_w - icon_w - label_w)]
            cells = [
                self._cell(f"{tid}c0", "0:0", icon,
                           top=1, bottom=1, left=4, right=3),
                self._cell(f"{tid}c1", "1:0",
                           self._psr("HB Title L2", label, terminal=True),
                           top=1, bottom=1, left=3, right=3),
                self._cell(f"{tid}c2", "2:0",
                           self._psr("HB Body", body, terminal=True),
                           top=1, bottom=1, left=3, right=4),
            ]
            table = self._component_table(tid, cols, cells)
            per_line = max(20, int((body_w - icon_w - label_w) / (0.52 * 6.2)))
            lines = max(1, (len(body) + per_line - 1) // per_line)
            return self._wrap_table_paragraph(table, terminal, span_columns), max(30.0, 7.5 * lines + 8)
        if kind == "warnbox":
            label = spec.get("label", "")
            texts = spec.get("texts", [])
            icon = ""
            if warning_icon_asset.exists():
                iw, ih = self._art_frame_size(warning_icon_asset, max_w=28.0)
                icon = ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                        + self._image_cell_content(f"{tid}wi", warning_icon_asset, iw, ih)
                        + '<Br/></CharacterStyleRange></ParagraphStyleRange>\n')
            body = "\n".join(texts)
            right = self._psr("HB Title L2", label) + self._psr("HB Body", body, terminal=True)
            cols = [36.0, max(36.0, body_w - 36.0)]
            cells = [
                self._cell(f"{tid}c0", "0:0", icon),
                self._cell(f"{tid}c1", "1:0", right),
            ]
            table = self._component_table(tid, cols, cells)
            per_line = max(20, int((body_w - 36.0) / (0.52 * 6.6)))
            lines = sum(max(1, (len(t) + per_line - 1) // per_line) for t in texts) or 1
            return self._wrap_table_paragraph(table, terminal, span_columns), max(34.0, 7.4 * (lines + 1) + 12)
        if kind == "notice":
            fill = "Color/HB Bg K05"
            label = spec.get("label", "")
            texts = spec.get("texts", [])
            left = self._psr("HB Notice Side Label", label, terminal=True)
            body = "\n".join(texts)
            if spec.get("list"):
                items = [t.strip() for t in texts if str(t).strip()]
                right = "".join(
                    self._psr("HB List", "• " + item, terminal=i == len(items) - 1)
                    for i, item in enumerate(items)
                )
            else:
                right = self._psr("HB Body", body, terminal=True)
            label_w = max(34.0, body_w * 0.14)
            cols = [label_w, body_w - label_w]
            cells = [
                self._cell(f"{tid}c0", "0:0", left, fill="Color/Paper",
                           stroke=False, top=10, bottom=10, left=6, right=6),
                self._cell(f"{tid}c1", "1:0", right, fill=fill,
                           stroke=False, top=10, bottom=10, left=6, right=6),
            ]
            table = self._component_table(tid, cols, cells)
            per_line = max(20, int((body_w - label_w) / (0.52 * 6.6)))
            lines = sum(max(1, (len(t) + per_line - 1) // per_line) for t in texts) or 1
            return self._wrap_table_paragraph(table, terminal, span_columns), max(24.0, 7.4 * lines + 10)
        if kind == "fcc":
            texts = spec.get("texts", ["", ""])[:2]
            mark = ROOT / "docs" / "renderers" / "latex" / "assets" / "fcc_mark.pdf"
            icon = ""
            if mark.exists():
                icon = ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                        '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                        + self._image_cell_content(f"{tid}fm", mark, 32.0, 22.0)
                        + '<Br/></CharacterStyleRange></ParagraphStyleRange>\n')
            cols = [body_w / 2.0] * 2
            cells = [
                self._cell(f"{tid}c0", "0:0",
                           icon + self._psr("HB Body", texts[0], terminal=True),
                           fill="Color/HB Bg K05", stroke=False),
                self._cell(f"{tid}c1", "1:0",
                           self._psr("HB Body", texts[1] if len(texts) > 1 else "", terminal=True),
                           fill="Color/HB Bg K05", stroke=False),
            ]
            table = self._component_table(tid, cols, cells)
            per_line = max(20, int(body_w / 2 / (0.52 * 6.2)))
            lines = max((len(t) + per_line - 1) // per_line for t in texts) if texts else 1
            return self._wrap_table_paragraph(table, terminal, span_columns), 7.5 * lines + 30
        if kind == "lcdmode":
            # LCD screen mode table (the last annotated-insert holdout):
            # state | action | description rows, LCD art above the table
            groups = spec.get("groups", [])
            img_ref = spec.get("img", "")
            art = ""
            img = self._resolve_bundle_image(bundle_root, img_ref) if img_ref else None
            if img is not None:
                iw, ih = self._art_frame_size(img, max_w=110.0)
                art = ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                       '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                       + self._image_cell_content(f"{tid}art", img, iw, ih)
                       + '<Br/></CharacterStyleRange></ParagraphStyleRange>\n')
            cols = [body_w * 0.22, body_w * 0.18, body_w * 0.60]
            cells = []
            ri = 0
            for g in groups:
                for ai, (action, desc) in enumerate(g.get("actions", [])):
                    state_txt = g.get("state", "") if ai == 0 else ""
                    cells.append(self._cell(f"{tid}c{ri}_0", f"0:{ri}",
                                            self._psr("HB Spec Label", state_txt, terminal=True)))
                    cells.append(self._cell(f"{tid}c{ri}_1", f"1:{ri}",
                                            self._psr("HB Spec Label", action, terminal=True)))
                    cells.append(self._cell(f"{tid}c{ri}_2", f"2:{ri}",
                                            self._psr("HB Spec Value", desc, terminal=True)))
                    ri += 1
            table = self._component_table(tid, cols, cells, n_rows=ri)
            xml = art + self._wrap_table_paragraph(table, terminal, span_columns)
            return xml, 70.0 + 12.0 * ri
        return "", 0.0

    def add_prose_story(self, sid: str, title: str, blocks: list[tuple[str, str]],
                        bundle_root: Path) -> tuple[str, float]:
        """Story from extracted prose blocks; returns (sid, est_height_pt)."""
        parts: list[str] = []
        est = 0.0
        img_n = 0
        content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
        last_idx = content_indices[-1] if content_indices else -1
        in_twocol = False
        has_twocol_layout = any(kind == "layout" for kind, _ in blocks)
        text_measure = self.page_w - self.m_l - self.m_r
        column_measure = (text_measure - 11.0) / 2.0
        for bi, (kind, text) in enumerate(blocks):
            if kind == "layout":
                if text == "twocol_start":
                    in_twocol = True
                elif text == "twocol_end":
                    in_twocol = False
                continue
            terminal = bi == last_idx
            if kind == "component":
                import json as _json
                spec = _json.loads(text)
                span_columns = not in_twocol
                measure_w = column_measure if in_twocol else None
                xml_part, h = self._render_component(
                    sid, bi, spec, bundle_root, terminal,
                    span_columns=span_columns, measure_w=measure_w)
                if xml_part:
                    parts.append(xml_part)
                    est += h
                continue
            if kind == "table":
                import json as _json
                raw_rows = _json.loads(text)
                img_n += 1
                n_cols = max(len(r) for r in raw_rows)
                if n_cols <= 2:
                    rows2 = [(r[0], r[1] if len(r) > 1 else "") for r in raw_rows]
                    table = self._table(f"{sid}_t{img_n}",
                                        [(str(a), str(b)) for a, b in rows2])
                else:
                    # N-column prose tables (e.g. KEY COMBINATIONS): first
                    # column narrow-ish, rest evenly split
                    body_w2 = self.page_w - self.m_l - self.m_r
                    cols = [body_w2 * 0.3] + [body_w2 * 0.7 / (n_cols - 1)] * (n_cols - 1)
                    tid = f"{sid}_t{img_n}"
                    cells = []
                    for ri, r in enumerate(raw_rows):
                        for ci in range(n_cols):
                            txt = str(r[ci]) if ci < len(r) else ""
                            style = "HB Spec Label" if ri == 0 else "HB Spec Value"
                            cells.append(self._cell(
                                f"{tid}c{ri}_{ci}", f"{ci}:{ri}",
                                self._psr(style, txt, terminal=True)))
                    table = self._component_table(tid, cols, cells, n_rows=len(raw_rows))
                parts.append(self._wrap_table_paragraph(
                    table, terminal, span_columns=not in_twocol))
                est += 11.0 * (len(raw_rows) + 1)
                continue
            if kind == "image":
                img = self._resolve_bundle_image(bundle_root, text)
                if img is None:
                    continue
                img_n += 1
                w_pt, h_pt = self._art_frame_size(img)
                rect = self._image_cell_content(f"{sid}_im{img_n}", img, w_pt, h_pt)
                parts.append(
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + rect + ("<Content></Content>" if terminal else "<Br/>")
                    + "</CharacterStyleRange></ParagraphStyleRange>\n")
                est += h_pt + 4
                continue
            style = self._PROSE_STYLE.get(kind, "HB Body")
            span_columns = has_twocol_layout and not in_twocol and kind in {"h1", "h2"}
            parts.append(self._psr(
                style, text, terminal=terminal, span_columns=span_columns))
            # width-aware: chars/line ~ frame_width / (0.52 * font size)
            size = {"h1": 9.0, "h2": 8.6, "h3": 7.0, "label": 6.8}.get(kind, 6.2)
            leading = {"h1": 16.0, "h2": 12.0, "h3": 9.0, "label": 12.0}.get(kind, 7.5)
            measure = column_measure if in_twocol else text_measure
            per_line = max(20, int(measure / (0.52 * size)))
            lines = sum(max(1, (len(seg) + per_line - 1) // per_line)
                        for seg in text.split("\n"))
            est += leading * lines
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title)}">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid, est

    def add_lcd_story(self, rows: list[dict], data_root: Path) -> str:
        """LCD icon table: circled-no / icon image / name / description."""
        sid = "st_lcd"
        body_w = self.page_w - self.m_l - self.m_r
        cols = (body_w * 0.08, body_w * 0.12, body_w * 0.28, body_w * 0.52)
        tid = "tbl_lcd"
        cells = []
        icon_pt = 24.0
        for ri, row in enumerate(rows):
            # figure paths are repo-relative in both live and fixture snapshots
            fig = (ROOT / row["figure"]) if row["figure"] else None
            img = (self._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
                   if fig and fig.exists() else "")
            cell_defs = (
                (self._psr("HB Spec Label", row["no"], terminal=True), 0),
                ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                 '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                 + img + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n', 1),
                (self._psr("HB Spec Label", row["name"], terminal=True), 2),
                (self._psr("HB Spec Value", row["desc"], terminal=True), 3),
            )
            for content, ci in cell_defs:
                cells.append(
                    f'    <Cell Self="{tid}c{ri}_{ci}" Name="{ci}:{ri}" RowSpan="1" ColumnSpan="1" '
                    'AppliedCellStyle="CellStyle/$ID/[None]" '
                    'TopInset="2" BottomInset="2" LeftInset="3" RightInset="3">\n'
                    + content + '    </Cell>'
                )
        row_els = "\n".join(
            f'    <Row Self="{tid}r{ri}" Name="{ri}"/>' for ri in range(len(rows))
        )
        col_els = "\n".join(
            f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{wd:g}"/>'
            for ci, wd in enumerate(cols)
        )
        table = (
            f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
            f'BodyRowCount="{len(rows)}" ColumnCount="{len(cols)}" HeaderRowCount="0" FooterRowCount="0">\n'
            f'{row_els}\n{col_els}\n' + "\n".join(cells) + "\n  </Table>\n"
        )
        parts = [
            self._psr("HB H1", "LCD DISPLAY"),
            '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
            '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table +
            '    <Content></Content></CharacterStyleRange>\n'
            '  </ParagraphStyleRange>\n',
        ]
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="LCD DISPLAY">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def add_symbols_story(self, signals: list[tuple[str, str]],
                          icons: list[dict], data_root: Path, lang: str = "en") -> str:
        sid = "st_symbols"
        copy = symbol_copy(lang)
        parts = [self._psr("HB H1", copy["title"])]
        if signals:
            table = self._table("tbl_sym_sig", signals, label_style="HB Notice Label")
            parts.append(
                '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
                '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
                + table + '    <Br/></CharacterStyleRange>\n  </ParagraphStyleRange>\n')
        if icons:
            body_w = self.page_w - self.m_l - self.m_r
            cols = (body_w * 0.18, body_w * 0.82)
            tid = "tbl_sym_ico"
            cells = []
            icon_pt = 20.0
            for ri, row in enumerate(icons):
                fig = (ROOT / row["figure"]) if row["figure"] else None
                img = (self._image_cell_content(f"{tid}img{ri}", fig, icon_pt, icon_pt)
                       if fig and fig.exists() else "")
                img_cell = (
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + img + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
                for ci, content in ((0, img_cell),
                                    (1, self._psr("HB Spec Value", row["text"], terminal=True))):
                    cells.append(
                        f'    <Cell Self="{tid}c{ri}_{ci}" Name="{ci}:{ri}" RowSpan="1" ColumnSpan="1" '
                        'AppliedCellStyle="CellStyle/$ID/[None]" '
                        'TopInset="2" BottomInset="2" LeftInset="3" RightInset="3">\n'
                        + content + '    </Cell>')
            row_els = "\n".join(f'    <Row Self="{tid}r{ri}" Name="{ri}"/>' for ri in range(len(icons)))
            col_els = "\n".join(
                f'    <Column Self="{tid}col{ci}" Name="{ci}" SingleColumnWidth="{wd:g}"/>'
                for ci, wd in enumerate(cols))
            table2 = (
                f'  <Table Self="{tid}" AppliedTableStyle="TableStyle/$ID/[Basic Table]" '
                f'BodyRowCount="{len(icons)}" ColumnCount="2" HeaderRowCount="0" FooterRowCount="0">\n'
                f'{row_els}\n{col_els}\n' + "\n".join(cells) + "\n  </Table>\n")
            parts.append(
                '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
                '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
                + table2 + '    <Content></Content></CharacterStyleRange>\n  </ParagraphStyleRange>\n')
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="MEANING OF SYMBOLS">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def add_trouble_story(self, rows: list[tuple[str, str]]) -> str:
        sid = "st_trouble"
        parts = [self._psr("HB H1", "TROUBLESHOOTING")]
        table = self._table("tbl_trouble", rows)
        parts.append(
            '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
            '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
            + table +
            '    <Content></Content></CharacterStyleRange>\n'
            '  </ParagraphStyleRange>\n'
        )
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="TROUBLESHOOTING">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def add_spec_story(self, sections: list[dict],
                       annotations: list[str] | None = None) -> str:
        sid = "st_spec"
        parts = [self._psr("HB H1", "SPECIFICATIONS")]
        for si, sec in enumerate(sections):
            parts.append(self._psr("HB Spec Section", sec["title"]))
            # table anchored in its own paragraph; the paragraph still needs
            # its own <Br/> so the next section title starts a new paragraph
            table = self._table(f"tbl_spec{si}", sec["rows"])
            last = si == len(sections) - 1 and not annotations
            parts.append(
                '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
                '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
                + table +
                ('    <Content></Content></CharacterStyleRange>\n' if last else
                 '    <Br/></CharacterStyleRange>\n')
                + '  </ParagraphStyleRange>\n'
            )
        # footnotes + notes under the tables (master parity)
        for ai, note in enumerate(annotations or []):
            parts.append(self._psr("HB Spec Note", note,
                                   terminal=(ai == len(annotations) - 1)))
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="SPECIFICATIONS">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) +
            '</Story>\n'
            '</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def add_text_story(self, sid: str, title: str, blocks: list[tuple[str, str]]) -> str:
        parts = [
            self._psr(style, text, terminal=(i == len(blocks) - 1))
            for i, (style, text) in enumerate(blocks)
        ]
        return self._add_story_parts(sid, title, parts)

    def _add_story_parts(self, sid: str, title: str, parts: list[str]) -> str:
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title)}">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) +
            '</Story>\n'
            '</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def _frame_xml(self, frame_id: str, story_id: str,
                   x1: float, y1: float, x2: float, y2: float, *,
                   columns: int = 1, fill: str | None = None,
                   rounded: bool = False, balance_columns: bool = False,
                   inset: tuple[float, float, float, float] | None = None) -> str:
        fill_attr = f'FillColor="{fill}" ' if fill else ""
        stroke_attr = (
            'StrokeColor="Swatch/None" StrokeWeight="0" '
            if fill else ""
        )
        corner_attr = 'CornerOption="RoundedCorner" CornerRadius="7" ' if rounded else ""
        balance_attr = ' VerticalBalanceColumns="true"' if balance_columns else ""
        inset_attr = ""
        if inset is not None:
            inset_attr = ' InsetSpacing="' + " ".join(f"{v:g}" for v in inset) + '"'
        return (
            f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" '
            'PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
            f'{fill_attr}{stroke_attr}{corner_attr}'
            'ItemTransform="1 0 0 1 0 0">\n'
            + self._path_geometry(x1, y1, x2, y2) +
            f'    <TextFramePreference TextColumnCount="{columns}" '
            f'TextColumnGutter="11" AutoSizingType="Off"{balance_attr}{inset_attr}/>\n'
            '  </TextFrame>\n'
        )

    def _page_rect(self, x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
        return (
            -self.page_w / 2 + x,
            -self.page_h / 2 + y,
            -self.page_w / 2 + x + w,
            -self.page_h / 2 + y + h,
        )

    def _safety_section_story(self, sid: str, title: str,
                              blocks: list[tuple[str, str]],
                              bundle_root: Path) -> str:
        parts: list[str] = []
        text_measure = self.page_w - self.m_l - self.m_r
        column_measure = (text_measure - 11.0) / 2.0
        content_indices = [i for i, (kind, _) in enumerate(blocks) if kind != "layout"]
        last_idx = content_indices[-1] if content_indices else -1
        for bi, (kind, text) in enumerate(blocks):
            terminal = bi == last_idx
            if kind == "component":
                import json as _json
                xml_part, _ = self._render_component(
                    sid, bi, _json.loads(text), bundle_root, terminal,
                    span_columns=False, measure_w=column_measure)
                parts.append(xml_part)
            elif kind == "body":
                parts.append(self._psr("HB Title L2", text, terminal=terminal))
            elif kind == "list":
                parts.append(self._psr("HB List", text, terminal=terminal))
            elif kind in {"h1", "h2", "h3"}:
                parts.append(self._psr(self._PROSE_STYLE[kind], text, terminal=terminal))
        return self._add_story_parts(sid, title, parts)

    def add_safety_page(self, sid: str, title: str, blocks: list[tuple[str, str]],
                        bundle_root: Path, page_index: int) -> str:
        """V2.0 US safety page 01: fixed component regions, not one flow."""
        h1 = next((t for k, t in blocks if k == "h1"), title)
        top_warning = next((t for k, t in blocks
                            if k == "component" and '"kind": "safetywarning"' in t), None)
        subbar = next((t for k, t in blocks if k == "h2"), "OPERATING INSTRUCTIONS")

        sections: list[list[tuple[str, str]]] = []
        cur: list[tuple[str, str]] | None = None
        for kind, text in blocks:
            if kind == "layout" and text == "twocol_start":
                cur = []
            elif kind == "layout" and text == "twocol_end":
                if cur is not None:
                    sections.append(cur)
                cur = None
            elif cur is not None:
                cur.append((kind, text))

        title_sid = f"{sid}_title"
        self._add_story_parts(
            title_sid, f"{title} title",
            [self._psr("HB Capsule Text", h1, terminal=True)])
        warning_sid = f"{sid}_top_warning"
        if top_warning:
            import json as _json
            xml_part, _ = self._render_component(
                warning_sid, 0, _json.loads(top_warning), bundle_root,
                terminal=True, span_columns=False)
            self._add_story_parts(warning_sid, f"{title} warning", [xml_part])
        bar_sid = f"{sid}_subbar"
        self._add_story_parts(
            bar_sid, f"{title} subbar",
            [self._psr("HB Capsule Text", subbar, terminal=True)])
        section_sids = []
        for idx, section in enumerate(sections[:2]):
            sec_sid = f"{sid}_section{idx + 1}"
            self._safety_section_story(sec_sid, f"{title} section {idx + 1}",
                                       section, bundle_root)
            section_sids.append(sec_sid)

        spread_id = f"sp_{page_index}"
        page_no = page_index + 1
        body_x = 27.4
        body_w = self.page_w - body_x * 2
        frames = []
        for frame_id, story_id, rect, opts in (
            ("title", title_sid, (body_x, 27.5, body_w, 18.8),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (1, 5, 1, 6)}),
            ("warning", warning_sid, (body_x, 55.5, body_w, 31.5),
             {"inset": (0, 0, 0, 0)}),
            ("section1", section_sids[0] if section_sids else "", (body_x, 93.5, body_w, 162.0),
             {"columns": 2, "balance_columns": True, "inset": (0, 0, 0, 0)}),
            ("subbar", bar_sid, (body_x, 263.5, body_w, 17.2),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (0.5, 5, 0.5, 6)}),
            ("section2", section_sids[1] if len(section_sids) > 1 else "",
             (body_x, 286.0, body_w, 205.0),
             {"columns": 2, "balance_columns": True, "inset": (0, 0, 0, 0)}),
        ):
            if not story_id:
                continue
            x1, y1, x2, y2 = self._page_rect(*rect)
            frames.append(self._frame_xml(
                f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))

        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" '
            f'Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
            '  </Page>\n'
            + "".join(frames) +
            '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        self.spreads.append((spread_id, xml))
        return spread_id

    def _single_component_story(self, sid: str, title: str, spec: dict,
                                bundle_root: Path, measure_w: float) -> str:
        xml_part, _ = self._render_component(
            sid, 0, spec, bundle_root,
            terminal=True, span_columns=False, measure_w=measure_w)
        return self._add_story_parts(sid, title, [xml_part])

    def add_fcc_inbox_page(
        self,
        sid: str,
        fcc_blocks: list[tuple[str, str]],
        inbox_blocks: list[tuple[str, str]],
        bundle_root: Path,
        page_index: int,
    ) -> str:
        """V2.0 page 03: FCC notice and inbox cards share one page."""
        import json as _json

        body_x = 27.4
        body_w = self.page_w - body_x * 2
        fcc_spec = next(
            (
                _json.loads(text) for kind, text in fcc_blocks
                if kind == "component" and _json.loads(text).get("kind") == "fcc"
            ),
            {"kind": "fcc", "texts": ["", ""]},
        )
        inbox_title = next((text for kind, text in inbox_blocks if kind == "h1"),
                           "WHAT'S IN THE BOX")
        inbox_spec = next(
            (
                _json.loads(text) for kind, text in inbox_blocks
                if kind == "component" and _json.loads(text).get("kind") == "inbox"
            ),
            None,
        )
        tip_spec = next(
            (
                _json.loads(text) for kind, text in inbox_blocks
                if kind == "component" and _json.loads(text).get("kind") == "notice"
            ),
            None,
        )

        fcc_sid = f"{sid}_fcc"
        self._single_component_story(
            fcc_sid, "FCC notice", fcc_spec, bundle_root, body_w)
        title_sid = f"{sid}_title"
        self._add_story_parts(
            title_sid, "Inbox title",
            [self._psr("HB Capsule Text", inbox_title, terminal=True)])
        frame_specs: list[tuple[str, str, tuple[float, float, float, float], dict]] = [
            ("fcc", fcc_sid, (body_x, 34.0, body_w, 184.0),
             {"fill": "Color/HB Bg K05", "rounded": True, "inset": (0, 0, 0, 0)}),
            ("title", title_sid, (body_x, 250.0, body_w, 21.5),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (1, 5, 1, 6)}),
        ]
        if inbox_spec:
            inbox_sid = f"{sid}_inbox"
            self._single_component_story(
                inbox_sid, "Inbox cards", inbox_spec, bundle_root, body_w)
            frame_specs.append(
                ("inbox", inbox_sid, (body_x, 278.0, body_w, 160.0),
                 {"inset": (0, 0, 0, 0)})
            )
        if tip_spec:
            tip_sid = f"{sid}_tip"
            self._single_component_story(
                tip_sid, "Inbox tip", tip_spec, bundle_root, body_w)
            frame_specs.append(
                ("tip", tip_sid, (body_x, 456.0, body_w, 42.0),
                 {"inset": (0, 0, 0, 0)})
            )

        spread_id = f"sp_{page_index}"
        page_no = page_index + 1
        frames = []
        for frame_id, story_id, rect, opts in frame_specs:
            x1, y1, x2, y2 = self._page_rect(*rect)
            frames.append(self._frame_xml(
                f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))

        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" '
            f'Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
            '  </Page>\n'
            + "".join(frames) +
            '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        self.spreads.append((spread_id, xml))
        return spread_id

    def _symbol_signal_bar(self, tid: str, label: str, bundle_root: Path) -> str:
        asset_name = f"{label.lower()}_bar.png"
        asset = (
            ROOT / "docs" / "templates" / "word_template" / "common_assets"
            / "symbols" / asset_name
        )
        if asset.exists():
            return ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + self._image_cell_content(tid, asset, 61.2, 16.2)
                    + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
        return self._psr("HB Capsule Text", label, terminal=True)

    def _symbols_signal_table(self, tid: str, signals: list[tuple[str, str]],
                              width: float, bundle_root: Path,
                              lang: str = "en") -> str:
        copy = symbol_copy(lang)
        rows = [(copy["symbol"], copy["meaning"], True)] + [
            (label, text, False) for label, text in signals
        ]
        cols = [width * 0.24, width * 0.76]
        cells = []
        for ri, (left, right, header) in enumerate(rows):
            if header:
                left_xml = self._psr("HB Spec Label", left, terminal=True)
                right_xml = self._psr("HB Spec Label", right, terminal=True)
            else:
                left_xml = self._symbol_signal_bar(f"{tid}sig{ri}", left, bundle_root)
                right_xml = self._psr("HB Spec Value", right, terminal=True)
            cells.append(self._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                    top=3, bottom=3, left=6, right=4))
            cells.append(self._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                    top=3, bottom=3, left=7, right=5))
        return self._component_table(tid, cols, cells, n_rows=len(rows))

    def _symbols_icon_table(self, tid: str, icons: list[dict], width: float,
                            lang: str = "en") -> str:
        copy = symbol_copy(lang)
        rows = [{"figure": "", "text": copy["meaning"], "header": True}] + [
            {**row, "header": False} for row in icons
        ]
        cols = [width * 0.27, width * 0.73]
        cells = []
        for ri, row in enumerate(rows):
            if row.get("header"):
                left_xml = self._psr("HB Spec Label", copy["symbol"], terminal=True)
                right_xml = self._psr("HB Spec Label", row["text"], terminal=True)
            else:
                fig = (ROOT / row["figure"]) if row.get("figure") else None
                icon = ""
                if fig and fig.exists():
                    icon = self._image_cell_content(f"{tid}img{ri}", fig, 28.0, 28.0)
                left_xml = (
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Figure">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + icon + '<Content></Content></CharacterStyleRange></ParagraphStyleRange>\n')
                right_xml = self._psr("HB Spec Value", row["text"], terminal=True)
            cells.append(self._cell(f"{tid}c{ri}_0", f"0:{ri}", left_xml,
                                    top=3, bottom=3, left=4, right=4))
            cells.append(self._cell(f"{tid}c{ri}_1", f"1:{ri}", right_xml,
                                    top=3, bottom=3, left=5, right=4))
        return self._component_table(tid, cols, cells, n_rows=len(rows))

    def _table_story(self, sid: str, title: str, table: str) -> str:
        return self._add_story_parts(
            sid, title,
            ['  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
             '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
             + table +
             '    <Content></Content></CharacterStyleRange>\n'
             '  </ParagraphStyleRange>\n'])

    def add_safety_symbols_page(
        self,
        sid: str,
        tail_blocks: list[tuple[str, str]],
        maintenance_blocks: list[tuple[str, str]],
        signals: list[tuple[str, str]],
        icons: list[dict],
        bundle_root: Path,
        page_index: int,
        lang: str = "en",
    ) -> str:
        """V2.0 page 02: safety tail + maintenance + symbols on one page."""
        import json as _json
        copy = symbol_copy(lang)

        tail_sids: list[str] = []
        for bi, (kind, text) in enumerate(tail_blocks):
            if kind != "component":
                continue
            spec = _json.loads(text)
            if spec.get("kind") == "safetywarning":
                spec = {
                    "kind": "tailwarnbox",
                    "label": copy["warning"],
                    "texts": spec.get("texts", []),
                }
            elif spec.get("kind") == "warnbox":
                spec = {
                    **spec,
                    "kind": "tailwarnbox",
                }
            tail_sid = f"{sid}_tail_{spec.get('label', bi).lower()}"
            xml_part, _ = self._render_component(
                tail_sid, bi, spec, bundle_root,
                terminal=True, span_columns=False)
            self._add_story_parts(tail_sid, f"Safety tail {bi}", [xml_part])
            tail_sids.append(tail_sid)

        maint_title = next((t for k, t in maintenance_blocks if k == "h1"),
                           "USER MAINTENANCE INSTRUCTIONS")
        maint_text = "\n".join(t for k, t in maintenance_blocks if k == "body")
        maint_title_sid = f"{sid}_maintenance_title"
        self._add_story_parts(
            maint_title_sid, "Maintenance title",
            [self._psr("HB Capsule Text", maint_title, terminal=True)])
        maint_body_sid = f"{sid}_maintenance_body"
        self._add_story_parts(
            maint_body_sid, "Maintenance body",
            [self._psr("HB Body", maint_text, terminal=True)])

        symbols_title_sid = f"{sid}_symbols_title"
        self._add_story_parts(
            symbols_title_sid, "Symbols title",
            [self._psr("HB Capsule Text", copy["title"], terminal=True)])

        body_x = 27.4
        body_w = self.page_w - body_x * 2
        icon_gap = 6.0
        icon_table_w = (body_w - icon_gap) / 2.0
        left_icons = icons[:6]
        right_icons = icons[6:]
        signal_sid = f"{sid}_signals"
        self._table_story(
            signal_sid, "Signal words",
            self._symbols_signal_table(
                f"{sid}_sig_tbl", signals, body_w, bundle_root, lang))
        left_sid = f"{sid}_icons_left"
        self._table_story(
            left_sid, "Symbol icons left",
            self._symbols_icon_table(f"{sid}_icons_l_tbl", left_icons, icon_table_w, lang))
        right_sid = f"{sid}_icons_right"
        self._table_story(
            right_sid, "Symbol icons right",
            self._symbols_icon_table(
                f"{sid}_icons_r_tbl", right_icons, icon_table_w, lang))

        frame_specs = (
            ("tail_warning", tail_sids[0] if tail_sids else "", (body_x, 18.0, body_w, 46.0),
             {"inset": (0, 0, 0, 0)}),
            ("tail_danger", tail_sids[1] if len(tail_sids) > 1 else "", (body_x, 68.0, body_w, 38.0),
             {"inset": (0, 0, 0, 0)}),
            ("maint_title", maint_title_sid, (body_x, 113.0, body_w, 16.5),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (0.5, 5, 0.5, 6)}),
            ("maint_body", maint_body_sid, (body_x, 132.5, body_w, 34.0),
             {"inset": (0, 0, 0, 0)}),
            ("symbols_title", symbols_title_sid, (body_x, 173.5, body_w, 27.0),
             {"fill": "Color/HB Brand Dark", "rounded": True, "inset": (2, 5, 1, 6)}),
            ("signals", signal_sid, (body_x, 211.5, body_w, 111.0),
             {"inset": (0, 0, 0, 0)}),
            ("icons_left", left_sid, (body_x, 329.0, icon_table_w, 179.0),
             {"inset": (0, 0, 0, 0)}),
            ("icons_right", right_sid, (body_x + icon_table_w + icon_gap, 329.0, icon_table_w, 179.0),
             {"inset": (0, 0, 0, 0)}),
        )

        spread_id = f"sp_{page_index}"
        page_no = page_index + 1
        frames = []
        for frame_id, story_id, rect, opts in frame_specs:
            if not story_id:
                continue
            x1, y1, x2, y2 = self._page_rect(*rect)
            frames.append(self._frame_xml(
                f"tf_{sid}_{frame_id}", story_id, x1, y1, x2, y2, **opts))
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
            f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
            f'  <Page Self="{spread_id}_pg" Name="{page_no}" '
            'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
            f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
            f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
            '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
            f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" '
            f'Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
            '  </Page>\n'
            + "".join(frames) +
            '</Spread>\n'
            '</idPkg:Spread>\n'
        )
        self.spreads.append((spread_id, xml))
        return spread_id

    @staticmethod
    def _path_geometry(x1: float, y1: float, x2: float, y2: float) -> str:
        """Rectangle as IDML PathGeometry.

        Spline items (TextFrame etc.) do NOT take a GeometricBounds
        attribute — that is a scripting-DOM property. InDesign silently
        ignores it and instantiates a degenerate (invisible) frame, which
        is exactly the "opens fine but every page is blank" failure mode.
        The geometry must be a four-anchor closed path in Properties.
        """
        pts = ((x1, y1), (x1, y2), (x2, y2), (x2, y1))
        anchors = "\n".join(
            f'            <PathPointType Anchor="{x:g} {y:g}" '
            f'LeftDirection="{x:g} {y:g}" RightDirection="{x:g} {y:g}"/>'
            for x, y in pts
        )
        return (
            '    <Properties>\n'
            '      <PathGeometry>\n'
            '        <GeometryPathType PathOpen="false">\n'
            '          <PathPointArray>\n'
            f'{anchors}\n'
            '          </PathPointArray>\n'
            '        </GeometryPathType>\n'
            '      </PathGeometry>\n'
            '    </Properties>\n'
        )

    def add_spread_chain(self, story_id: str, n_pages: int, start_index: int,
                         columns: int = 1) -> None:
        """One spread per page, each holding one frame of a linked chain.

        Spread coordinates: origin at the spread center; the page's
        top-left corner sits at (-w/2, -h/2), so the type area is that
        corner offset by the page margins.
        """
        x1 = -self.page_w / 2 + self.m_l
        x2 = self.page_w / 2 - self.m_r
        y1 = -self.page_h / 2 + self.m_t
        y2 = self.page_h / 2 - self.m_b
        for i in range(n_pages):
            spread_id = f"sp_{start_index + i}"
            frame_id = f"tf_{story_id}_{i}"
            prev = f'PreviousTextFrame="tf_{story_id}_{i-1}"' if i > 0 else 'PreviousTextFrame="n"'
            nxt = f'NextTextFrame="tf_{story_id}_{i+1}"' if i < n_pages - 1 else 'NextTextFrame="n"'
            xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="15.0">\n'
                f'<Spread Self="{spread_id}" PageCount="1" BindingLocation="0" ShowMasterItems="true">\n'
                f'  <Page Self="{spread_id}_pg" Name="{start_index + i + 1}" '
                'AppliedMaster="n" OverrideList="" TabOrder="" GridStartingPoint="TopOutside" '
                f'GeometricBounds="0 0 {self.page_h:g} {self.page_w:g}" '
                f'ItemTransform="1 0 0 1 {-self.page_w / 2:g} {-self.page_h / 2:g}">\n'
                '    <MarginPreference ColumnCount="1" ColumnGutter="12" '
                f'Top="{self.m_t:g}" Bottom="{self.m_b:g}" Left="{self.m_l:g}" Right="{self.m_r:g}"/>\n'
                '  </Page>\n'
                f'  <TextFrame Self="{frame_id}" ParentStory="{story_id}" {prev} {nxt} '
                'ContentType="TextType" AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]" '
                'ItemTransform="1 0 0 1 0 0">\n'
                + self._path_geometry(x1, y1, x2, y2) +
                f'    <TextFramePreference TextColumnCount="{columns}" TextColumnGutter="11" AutoSizingType="Off"/>\n'
                '  </TextFrame>\n'
                '</Spread>\n'
                '</idPkg:Spread>\n'
            )
            self.spreads.append((spread_id, xml))

    # -- assembly ----------------------------------------------------------
    def designmap_xml(self) -> str:
        spread_refs = "\n".join(
            f'  <idPkg:Spread src="Spreads/Spread_{sid}.xml"/>' for sid, _ in self.spreads
        )
        story_refs = "\n".join(
            f'  <idPkg:Story src="Stories/Story_{sid}.xml"/>' for sid, _ in self.stories
        )
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<?aid style="50" type="document" readerVersion="15.0" featureSet="257" product="15.0(100)"?>\n'
            f'<Document xmlns:idPkg="{IDPKG}" DOMVersion="15.0" Self="doc" '
            'StoryList="' + " ".join(sid for sid, _ in self.stories) + '" Name="manual">\n'
            '  <Language Self="Language/$ID/English%3a USA" Name="$ID/English: USA" '
            'SingleQuotes="&#8216;&#8217;" DoubleQuotes="&#8220;&#8221;"/>\n'
            f'  <idPkg:Graphic src="Resources/Graphic.xml"/>\n'
            f'  <idPkg:Fonts src="Resources/Fonts.xml"/>\n'
            f'  <idPkg:Styles src="Resources/Styles.xml"/>\n'
            f'  <idPkg:Preferences src="Resources/Preferences.xml"/>\n'
            f'{spread_refs}\n'
            f'{story_refs}\n'
            '</Document>\n'
        )

    def write(self, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out_path, "w") as zf:
            # mimetype must be first and stored uncompressed
            zf.writestr(zipfile.ZipInfo("mimetype"), MIMETYPE, compress_type=zipfile.ZIP_STORED)
            def add(name: str, data: str) -> None:
                zf.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
            add("designmap.xml", self.designmap_xml())
            add("META-INF/container.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">\n'
                '  <rootfiles><rootfile full-path="designmap.xml" media-type="text/xml"/></rootfiles>\n'
                '</container>\n')
            add("Resources/Graphic.xml", self.graphic_xml())
            add("Resources/Fonts.xml", self.fonts_xml())
            add("Resources/Styles.xml", self.styles_xml())
            add("Resources/Preferences.xml", self.preferences_xml())
            for sid, xml in self.spreads:
                add(f"Spreads/Spread_{sid}.xml", xml)
            for sid, xml in self.stories:
                add(f"Stories/Story_{sid}.xml", xml)


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------

def check_idml(path: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        for name in duplicates:
            issues.append(f"duplicate package part: {name}")
        if names[0] != "mimetype":
            issues.append("mimetype is not the first zip entry")
        info = zf.getinfo("mimetype")
        if info.compress_type != zipfile.ZIP_STORED:
            issues.append("mimetype entry is compressed (must be STORED)")
        if zf.read("mimetype").decode() != MIMETYPE:
            issues.append("mimetype content mismatch")
        for name in names:
            if name.endswith(".xml"):
                try:
                    ET.fromstring(zf.read(name))
                except ET.ParseError as exc:
                    issues.append(f"{name}: XML parse error: {exc}")
        # designmap references must resolve
        dm = zf.read("designmap.xml").decode("utf-8")
        root = ET.fromstring(dm)
        for el in root.iter():
            src = el.attrib.get("src")
            if src and src not in names:
                issues.append(f"designmap references missing part: {src}")
        # spline items must carry PathGeometry — a GeometricBounds
        # attribute is silently ignored by InDesign and yields invisible
        # frames ("opens fine but blank pages")
        for name in names:
            if not name.startswith("Spreads/"):
                continue
            spread = ET.fromstring(zf.read(name))
            for frame in spread.iter("TextFrame"):
                if "GeometricBounds" in frame.attrib:
                    issues.append(f"{name}: TextFrame {frame.get('Self')} uses "
                                  "GeometricBounds (ignored by InDesign; use PathGeometry)")
                if frame.find("./Properties/PathGeometry") is None:
                    issues.append(f"{name}: TextFrame {frame.get('Self')} has no PathGeometry")
    return issues


def split_safety_first_page(
    blocks: list[tuple[str, str]],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Keep the V2.0 safety page-01 composition aligned with the master.

    The source template places the two main ``safetytwocol`` sections on page
    01. The trailing WARNING/DANGER boxes continue at the top of page 02 before
    the next prose section. Split at the second ``twocol_end`` marker rather
    than keying off copy text, so localized safety pages keep the same layout
    contract.
    """
    ends = 0
    for idx, (kind, text) in enumerate(blocks):
        if kind == "layout" and text == "twocol_end":
            ends += 1
            if ends == 2:
                return blocks[:idx + 1], blocks[idx + 1:]
    return blocks, []


def default_bundle_root(model: str, region: str, lang: str) -> Path:
    """Pick the prepared RST bundle path used by the current target layout."""
    lang_bundle = ROOT / "docs" / "_build" / model / region / lang / "rst"
    region_bundle = ROOT / "docs" / "_build" / model / region / "rst"
    return lang_bundle if lang_bundle.is_dir() else region_bundle


def default_output_path(model: str, region: str, lang: str, bundle_root: Path) -> Path:
    """Match the IDML output location to the prepared bundle layout."""
    region_bundle = ROOT / "docs" / "_build" / model / region / "rst"
    model_slug = model.replace("-", "").lower()
    region_slug = region.lower()
    try:
        is_region_bundle = bundle_root.resolve() == region_bundle.resolve()
    except FileNotFoundError:
        is_region_bundle = bundle_root == region_bundle
    if is_region_bundle:
        return (
            ROOT / "docs" / "_build" / model / region / "idml"
            / f"manual_{model_slug}_{region_slug}.idml"
        )
    return (
        ROOT / "docs" / "_build" / model / region / lang / "idml"
        / f"manual_{model_slug}_{region_slug}_{lang}.idml"
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="JE-1000F")
    ap.add_argument("--region", default="US")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--data-root", default="data/phase2")
    ap.add_argument("--out", default=None)
    ap.add_argument("--bundle-root", default=None,
                    help="Prepared rst bundle dir (default: docs/_build/<model>/<region>/<lang>/rst); prose pages are skipped if absent")
    ap.add_argument("--check", default=None, help="validate an existing .idml and exit")
    args = ap.parse_args()

    if args.check:
        issues = check_idml(Path(args.check))
        for i in issues:
            print(f"[idml-check] FAIL {i}")
        print(f"[idml-check] {'OK' if not issues else f'{len(issues)} issue(s)'}: {args.check}")
        return 1 if issues else 0

    params = load_layout_params(ROOT / "data" / "layout_params.csv")
    data_root = (ROOT / args.data_root) if not Path(args.data_root).is_absolute() else Path(args.data_root)
    sections = load_spec_sections(data_root, args.model, args.region)
    if not sections:
        print(f"[export-idml] ERROR: no specifications rows for {args.model}_{args.region} in {data_root}")
        return 1

    w = IdmlWriter(params)
    lcd_rows = load_lcd_rows(data_root, args.model)
    trouble_rows = load_trouble_rows(data_root, args.model, args.region)
    spec_annotations = load_spec_annotations(data_root, args.model, args.region)
    symbol_cache: dict[str, tuple[list[tuple[str, str]], list[dict]]] = {}

    def symbol_rows_for(lang: str) -> tuple[list[tuple[str, str]], list[dict]]:
        lang = normalize_lang(lang)
        if lang not in symbol_cache:
            symbol_cache[lang] = load_symbols_rows(data_root, lang)
        return symbol_cache[lang]

    bundle_root = Path(args.bundle_root) if args.bundle_root else (
        default_bundle_root(args.model, args.region, args.lang))
    tags = {
        "latex",
        f"region_{args.region.lower()}",
        f"lang_{args.lang.lower()}",
        "model_" + args.model.lower().replace("-", "_"),
    }
    page_cursor = 0
    skipped_raw = 0
    prose_pages = 0

    def chain(story_id: str, est_h: float, columns: int = 1) -> None:
        nonlocal page_cursor
        # A two-column frame holds twice the height. Do not add an extra
        # safety multiplier here: when the estimate already fits, that creates
        # trailing blank linked frames in InDesign.
        pages = w.pages_for_height(est_h / max(1, columns))
        w.add_spread_chain(story_id, pages, page_cursor, columns=columns)
        page_cursor += pages

    DATA_PAGES = {"spec": "spec_", "lcd": "lcd_icons_", "trouble": "troubleshooting_"}
    ordered = bundle_page_order(bundle_root) if bundle_root.is_dir() else []
    if not ordered:
        print(f"[export-idml] NOTE: no prepared bundle at {bundle_root}; "
              "exporting data pages only (run `build.py rst` first for full prose)")

    emitted = {"spec": False, "lcd": False, "trouble": False, "symbols": False}
    pending_prefix_blocks: list[tuple[str, str]] = []
    pending_fcc_blocks: list[tuple[str, str]] = []
    pending_fcc_title = ""

    def page_lang(page: Path) -> str:
        try:
            text = page.read_text(encoding="utf-8")
        except OSError:
            text = ""
        match = re.search(r"\\HBApplyLang\{([^}]+)\}", text)
        if match:
            return normalize_lang(match.group(1))
        suffix = page.stem.rsplit("_", 1)[-1]
        return normalize_lang(suffix if len(suffix) <= 5 else args.lang)

    def page_stem_has(page: Path, suffix: str) -> bool:
        return page.stem == suffix or page.stem.endswith("_" + suffix)

    def slug_stem(stem: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")

    def flush_pending_prefix() -> None:
        nonlocal pending_prefix_blocks, prose_pages
        if not pending_prefix_blocks:
            return
        sid = f"st_pending_{page_cursor}"
        _, est = w.add_prose_story(sid, sid, pending_prefix_blocks, bundle_root)
        chain(sid, est)
        prose_pages += 1
        pending_prefix_blocks = []

    def flush_pending_fcc() -> None:
        nonlocal pending_fcc_blocks, pending_fcc_title, prose_pages
        if not pending_fcc_blocks:
            return
        sid = "st_" + slug_stem(pending_fcc_title or f"fcc_{page_cursor}")
        _, est = w.add_prose_story(
            sid, pending_fcc_title or sid, pending_fcc_blocks, bundle_root)
        chain(sid, est)
        prose_pages += 1
        pending_fcc_blocks = []
        pending_fcc_title = ""

    def emit_data_page(kind: str) -> None:
        flush_pending_fcc()
        flush_pending_prefix()
        if emitted[kind]:
            return
        emitted[kind] = True
        if kind == "spec":
            sid = w.add_spec_story(sections, spec_annotations)
            chain(sid, w.estimate_spec_height(sections) + 10.0 * len(spec_annotations))
        elif kind == "lcd" and lcd_rows:
            sid = w.add_lcd_story(lcd_rows, data_root)
            chain(sid, 16.0 + sum(max(28.0, 11.0 * (r["desc"].count("\n") + 1)) for r in lcd_rows))
        elif kind == "trouble" and trouble_rows:
            sid = w.add_trouble_story(trouble_rows)
            chain(sid, 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in trouble_rows))
        elif kind == "symbols":
            sym_signals, sym_icons = symbol_rows_for(args.lang)
            if not (sym_signals or sym_icons):
                return
            sid = w.add_symbols_story(sym_signals, sym_icons, data_root, args.lang)
            chain(sid, 16.0 + 14.0 * len(sym_signals) + 26.0 * len(sym_icons))

    for page in ordered:
        if page.name.startswith("symbols_") and emitted["symbols"] \
                and not pending_prefix_blocks and not pending_fcc_blocks:
            continue
        matched = next((k for k, prefix in DATA_PAGES.items()
                        if page.name.startswith(prefix)), None)
        if matched:
            emit_data_page(matched)
            continue
        res = extract_page(page, tags)
        skipped_raw += res.skipped_raw
        blocks = res.blocks
        if pending_prefix_blocks and "user_maintenance" in page.stem:
            lang = page_lang(page)
            sym_signals, sym_icons = symbol_rows_for(lang)
            if not (sym_signals or sym_icons):
                flush_pending_fcc()
                blocks = pending_prefix_blocks + blocks
                pending_prefix_blocks = []
            else:
                sid = "st_safety_symbols_" + re.sub(
                    r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
                w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, blocks, sym_signals, sym_icons,
                    bundle_root, page_cursor, lang)
                emitted["symbols"] = True
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
        if pending_fcc_blocks and page_stem_has(page, "02_whats_in_the_box"):
            sid = "st_fcc_inbox_" + slug_stem(page.stem)
            w.add_fcc_inbox_page(
                sid, pending_fcc_blocks, blocks, bundle_root, page_cursor)
            pending_fcc_blocks = []
            pending_fcc_title = ""
            page_cursor += 1
            prose_pages += 1
            continue
        flush_pending_fcc()
        if page_stem_has(page, "01_fcc"):
            flush_pending_prefix()
            if blocks:
                pending_fcc_blocks = blocks
                pending_fcc_title = page.stem
            continue
        if page.name.startswith("symbols_"):
            if emitted["symbols"]:
                continue
            lang = page_lang(page)
            sym_signals, sym_icons = symbol_rows_for(lang)
            if pending_prefix_blocks and (sym_signals or sym_icons):
                sid = "st_safety_symbols_" + re.sub(
                    r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
                w.add_safety_symbols_page(
                    sid, pending_prefix_blocks, [], sym_signals, sym_icons,
                    bundle_root, page_cursor, lang)
                emitted["symbols"] = True
                pending_prefix_blocks = []
                page_cursor += 1
                prose_pages += 1
                continue
            emit_data_page("symbols")
            continue
        if pending_prefix_blocks:
            blocks = pending_prefix_blocks + blocks
            pending_prefix_blocks = []
        if not blocks:
            continue
        if page.name.startswith("safety_") and res.twocol:
            blocks, pending_prefix_blocks = split_safety_first_page(blocks)
            sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
            w.add_safety_page(sid, page.stem, blocks, bundle_root, page_cursor)
            page_cursor += 1
            prose_pages += 1
            continue
        sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
        _, est = w.add_prose_story(sid, page.stem, blocks, bundle_root)
        chain(sid, est, columns=2 if res.twocol else 1)
        prose_pages += 1

    # data pages always ship, bundle or not
    for kind in ("spec", "lcd", "trouble", "symbols"):
        emit_data_page(kind)

    out = Path(args.out) if args.out else (
        default_output_path(args.model, args.region, args.lang, bundle_root))
    w.write(out)
    issues = check_idml(out)
    for i in issues:
        print(f"[export-idml] SELF-CHECK FAIL: {i}")
    n_rows = sum(len(s["rows"]) for s in sections)
    print(f"[export-idml] {'OK' if not issues else 'WROTE WITH ISSUES'}: {out}")
    print(f"[export-idml] stories={len(w.stories)} spreads={len(w.spreads)} "
          f"prose pages={prose_pages} skipped raw blocks={skipped_raw} | "
          f"spec rows={n_rows} lcd rows={len(lcd_rows)} trouble rows={len(trouble_rows)}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
