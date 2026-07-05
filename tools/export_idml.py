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


def load_symbols_rows(data_root: Path) -> tuple[list[tuple[str, str]], list[dict]]:
    """symbols_blocks.csv -> (signal rows [label, meaning], icon rows)."""
    path = data_root / "symbols_blocks.csv"
    signals: list[tuple[str, str]] = []
    icons: list[dict] = []
    rows = [r for r in csv.DictReader(path.open(encoding="utf-8"))
            if r.get("Is_Latest", r.get("Is_latest")) == "TRUE"]
    rows.sort(key=lambda r: float(r.get("order") or 0))
    for r in rows:
        text = (r.get("text_en") or "").strip()
        if r.get("block_type") == "signal_row":
            signals.append(((r.get("label_en") or "").strip(), text))
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
            shaded = name == "HB H1" or kind == "label"
            fill = "Color/Paper" if shaded else "Color/HB Brand Dark"
            shading = (
                'ShadingOn="true" ShadingColor="Color/HB Brand Dark" '
                'ShadingOffsetTop="2" ShadingOffsetBottom="2" '
                'ShadingOffsetLeft="3" ShadingOffsetRight="3" '
                'SpaceBefore="4" SpaceAfter="3" '
            ) if shaded else ""
            styles.append(
                f'  <ParagraphStyle Self="{self_id}" Name="{name}" '
                f'PointSize="{size:g}" FillColor="{fill}" {shading}'
                f'Justification="LeftAlign">\n'
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
            f'<idPkg:Styles xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
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
            f'<idPkg:Graphic xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
            '  <Color Self="Color/Black" Model="Process" Space="CMYK" ColorValue="0 0 0 100" Name="Black"/>\n'
            '  <Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" Name="Paper"/>\n'
            + "\n".join(colors) + "\n"
            '  <Swatch Self="Swatch/None" Name="None"/>\n'
            '</idPkg:Graphic>\n'
        )

    def fonts_xml(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Fonts xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
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
            f'<idPkg:Preferences xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
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
    def _psr(cls, style: str, text: str, *, terminal: bool = False) -> str:
        """One ParagraphStyleRange.

        IDML paragraphs are delimited by explicit <Br/> characters in the
        content stream, NOT by ParagraphStyleRange boundaries — without a
        trailing <Br/> adjacent ranges fuse into one paragraph
        ("SPECIFICATIONSGENERAL INFO", designer-reported). Every range
        therefore ends with <Br/> unless it is the story's last one.
        """
        lines = cls._clean_text(text).split("\n")
        content = "<Br/>".join(f"<Content>{escape(l)}</Content>" for l in lines)
        if not terminal:
            content += "<Br/>"
        sid = "ParagraphStyle/" + style.replace(" ", "%20")
        return (
            f'  <ParagraphStyleRange AppliedParagraphStyle="{sid}">\n'
            f'    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
            f'{content}</CharacterStyleRange>\n'
            '  </ParagraphStyleRange>\n'
        )

    def _table(self, tid: str, rows: list[tuple[str, str]]) -> str:
        left_ratio = float(self.params.get("comp_spec_table_left_ratio", ("0.315", ""))[0])
        body_w = self.page_w - self.m_l - self.m_r
        col1 = body_w * left_ratio
        col2 = body_w - col1
        cells = []
        for ri, (label, value) in enumerate(rows):
            for ci, (txt, style) in enumerate(((label, "HB Spec Label"), (value, "HB Spec Value"))):
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

    def add_prose_story(self, sid: str, title: str, blocks: list[tuple[str, str]],
                        bundle_root: Path) -> tuple[str, float]:
        """Story from extracted prose blocks; returns (sid, est_height_pt)."""
        parts: list[str] = []
        est = 0.0
        img_n = 0
        last_idx = len(blocks) - 1
        for bi, (kind, text) in enumerate(blocks):
            terminal = bi == last_idx
            if kind == "table":
                import json as _json
                rows = [tuple(r) if len(r) == 2 else (r[0], " / ".join(r[1:]))
                        for r in _json.loads(text)]
                img_n += 1
                table = self._table(f"{sid}_t{img_n}", [(str(a), str(b)) for a, b in rows])
                parts.append(
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">'
                    '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">'
                    + table + ("<Content></Content>" if terminal else "<Br/>")
                    + "</CharacterStyleRange></ParagraphStyleRange>\n")
                est += 11.0 * (len(rows) + 1)
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
            parts.append(self._psr(style, text, terminal=terminal))
            # width-aware: chars/line ~ frame_width / (0.52 * font size)
            size = {"h1": 9.0, "h2": 8.6, "h3": 7.0, "label": 6.8}.get(kind, 6.2)
            leading = {"h1": 16.0, "h2": 12.0, "h3": 9.0, "label": 12.0}.get(kind, 7.5)
            per_line = max(20, int((self.page_w - self.m_l - self.m_r) / (0.52 * size)))
            lines = sum(max(1, (len(seg) + per_line - 1) // per_line)
                        for seg in text.split("\n"))
            est += leading * lines
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
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
                ('  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Spec%20Label">'
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
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="LCD DISPLAY">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def add_symbols_story(self, signals: list[tuple[str, str]],
                          icons: list[dict], data_root: Path) -> str:
        sid = "st_symbols"
        parts = [self._psr("HB H1", "MEANING OF SYMBOLS")]
        if signals:
            table = self._table("tbl_sym_sig", signals)
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
                    '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Spec%20Label">'
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
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
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
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="TROUBLESHOOTING">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) + '</Story>\n</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

    def add_spec_story(self, sections: list[dict]) -> str:
        sid = "st_spec"
        parts = [self._psr("HB H1", "SPECIFICATIONS")]
        for si, sec in enumerate(sections):
            parts.append(self._psr("HB Spec Section", sec["title"]))
            # table anchored in its own paragraph; the paragraph still needs
            # its own <Br/> so the next section title starts a new paragraph
            table = self._table(f"tbl_spec{si}", sec["rows"])
            last = si == len(sections) - 1
            parts.append(
                '  <ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/HB%20Body">\n'
                '    <CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]">\n'
                + table +
                ('    <Content></Content></CharacterStyleRange>\n' if last else
                 '    <Br/></CharacterStyleRange>\n')
                + '  </ParagraphStyleRange>\n'
            )
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
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
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<idPkg:Story xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
            f'<Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="{escape(title)}">\n'
            '<StoryPreference OpticalMarginAlignment="false" FrameType="TextFrameType"/>\n'
            + "".join(parts) +
            '</Story>\n'
            '</idPkg:Story>\n'
        )
        self.stories.append((sid, xml))
        return sid

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
                f'<idPkg:Spread xmlns:idPkg="{IDPKG}" DOMVersion="8.0">\n'
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
            '<?aid style="50" type="document" readerVersion="6.0" featureSet="257" product="8.0(370)"?>\n'
            f'<Document xmlns:idPkg="{IDPKG}" DOMVersion="8.0" Self="doc" '
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
    sym_signals, sym_icons = load_symbols_rows(data_root)

    bundle_root = Path(args.bundle_root) if args.bundle_root else (
        ROOT / "docs" / "_build" / args.model / args.region / args.lang / "rst")
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
        # a two-column frame holds twice the height; keep a 1.2 safety factor
        # so underestimates surface as overset (one drag) instead of blanks
        pages = w.pages_for_height(est_h * 1.2 / max(1, columns))
        w.add_spread_chain(story_id, pages, page_cursor, columns=columns)
        page_cursor += pages

    DATA_PAGES = {"spec": "spec_", "lcd": "lcd_icons_", "trouble": "troubleshooting_",
                  "symbols": "symbols_"}
    ordered = bundle_page_order(bundle_root) if bundle_root.is_dir() else []
    if not ordered:
        print(f"[export-idml] NOTE: no prepared bundle at {bundle_root}; "
              "exporting data pages only (run `build.py rst` first for full prose)")

    emitted = {"spec": False, "lcd": False, "trouble": False, "symbols": False}

    def emit_data_page(kind: str) -> None:
        if emitted[kind]:
            return
        emitted[kind] = True
        if kind == "spec":
            sid = w.add_spec_story(sections)
            chain(sid, w.estimate_spec_height(sections))
        elif kind == "lcd" and lcd_rows:
            sid = w.add_lcd_story(lcd_rows, data_root)
            chain(sid, 16.0 + sum(max(28.0, 11.0 * (r["desc"].count("\n") + 1)) for r in lcd_rows))
        elif kind == "trouble" and trouble_rows:
            sid = w.add_trouble_story(trouble_rows)
            chain(sid, 16.0 + sum(11.0 * (v.count("\n") + 1) for _, v in trouble_rows))
        elif kind == "symbols" and (sym_signals or sym_icons):
            sid = w.add_symbols_story(sym_signals, sym_icons, data_root)
            chain(sid, 16.0 + 14.0 * len(sym_signals) + 26.0 * len(sym_icons))

    for page in ordered:
        matched = next((k for k, prefix in DATA_PAGES.items()
                        if page.name.startswith(prefix)), None)
        if matched:
            emit_data_page(matched)
            continue
        res = extract_page(page, tags)
        skipped_raw += res.skipped_raw
        if not res.blocks:
            continue
        sid = "st_" + re.sub(r"[^a-z0-9]+", "_", page.stem.lower()).strip("_")
        _, est = w.add_prose_story(sid, page.stem, res.blocks, bundle_root)
        chain(sid, est, columns=2 if res.twocol else 1)
        prose_pages += 1

    # data pages always ship, bundle or not
    for kind in ("spec", "lcd", "trouble", "symbols"):
        emit_data_page(kind)

    tag = f"manual_{args.model.replace('-', '').lower()}_{args.region.lower()}_{args.lang}"
    out = Path(args.out) if args.out else (
        ROOT / "docs" / "_build" / args.model / args.region / args.lang / "idml" / f"{tag}.idml")
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
